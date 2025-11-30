"""
定时任务调度器
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from datetime import datetime
import json


class SchedulerManager:
    """调度器管理类"""

    def __init__(self):
        self.scheduler = BackgroundScheduler(
            jobstores={'default': MemoryJobStore()},
            timezone='Asia/Shanghai'
        )
        self.scheduler.start()

    def add_job(self, schedule):
        """添加定时任务"""
        try:
            # 解析Cron表达式
            # 支持标准Cron格式: 分 时 日 月 周
            cron_parts = schedule.cron.strip().split()

            if len(cron_parts) == 5:
                minute, hour, day, month, day_of_week = cron_parts
            else:
                raise ValueError('Cron表达式格式错误，应为: 分 时 日 月 周')

            # 创建触发器
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            )

            # 添加任务
            self.scheduler.add_job(
                func=self._execute_scheduled_task,
                trigger=trigger,
                id=f'schedule_{schedule.id}',
                args=[schedule.id],
                replace_existing=True
            )

            # 更新下次执行时间
            job = self.scheduler.get_job(f'schedule_{schedule.id}')
            if job:
                from models import db
                schedule.next_run = job.next_run_time
                db.session.commit()

            return True
        except Exception as e:
            print(f'添加定时任务失败: {str(e)}')
            return False

    def remove_job(self, schedule_id):
        """移除定时任务"""
        try:
            job_id = f'schedule_{schedule_id}'
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            return True
        except Exception as e:
            print(f'移除定时任务失败: {str(e)}')
            return False

    def _execute_scheduled_task(self, schedule_id):
        """执行定时任务"""
        from models import db, Schedule, Execution
        from services.executor import execute_script
        from threading import Thread

        try:
            # 获取任务配置
            schedule = Schedule.query.get(schedule_id)
            if not schedule or not schedule.enabled:
                return

            # 更新上次执行时间
            schedule.last_run = datetime.utcnow()

            # 更新下次执行时间
            job = self.scheduler.get_job(f'schedule_{schedule_id}')
            if job:
                schedule.next_run = job.next_run_time

            db.session.commit()

            # 创建执行记录
            execution = Execution(
                script_id=schedule.script_id,
                status='pending',
                params=schedule.params
            )
            db.session.add(execution)
            db.session.commit()

            # 异步执行脚本
            thread = Thread(target=execute_script, args=(execution.id,))
            thread.start()

        except Exception as e:
            print(f'执行定时任务失败: {str(e)}')

    def reload_schedules(self):
        """重新加载所有定时任务"""
        from models import Schedule

        try:
            # 清空现有任务
            self.scheduler.remove_all_jobs()

            # 加载启用的任务
            schedules = Schedule.query.filter_by(enabled=True).all()
            for schedule in schedules:
                self.add_job(schedule)

            print(f'已加载 {len(schedules)} 个定时任务')
            return True
        except Exception as e:
            print(f'重新加载定时任务失败: {str(e)}')
            return False

    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()


# 创建全局调度器实例
scheduler_manager = SchedulerManager()
