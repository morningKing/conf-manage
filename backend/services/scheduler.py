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
                try:
                    from models import db
                    schedule.next_run = job.next_run_time
                    db.session.commit()
                    print(f'[调度器] 任务 {schedule.id} ({schedule.name}) 已添加，下次执行: {job.next_run_time}')
                except Exception as e:
                    print(f'[调度器] 更新下次执行时间失败: {str(e)}')

            return True
        except Exception as e:
            print(f'[调度器] 添加定时任务失败: {str(e)}')
            import traceback
            traceback.print_exc()
            return False

    def remove_job(self, schedule_id):
        """移除定时任务"""
        try:
            job_id = f'schedule_{schedule_id}'
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                print(f'[调度器] 任务 {schedule_id} 已移除')
            return True
        except Exception as e:
            print(f'[调度器] 移除定时任务失败: {str(e)}')
            return False

    def _execute_scheduled_task(self, schedule_id):
        """执行定时任务"""
        from models import db, Schedule, Execution
        from services.executor import execute_script
        from threading import Thread
        from flask import current_app

        def run_task_in_context():
            """在应用上下文中执行任务"""
            try:
                # 移除旧的会话，创建新的会话
                db.session.remove()

                # 获取任务配置
                schedule = Schedule.query.get(schedule_id)
                if not schedule:
                    print(f'[定时任务] 任务 {schedule_id} 不存在')
                    return
                
                if not schedule.enabled:
                    print(f'[定时任务] 任务 {schedule_id} 已禁用，跳过执行')
                    return

                print(f'[定时任务] 开始执行任务 {schedule_id} - {schedule.name}')

                # 更新上次执行时间
                schedule.last_run = datetime.utcnow()

                # 更新下次执行时间
                job = self.scheduler.get_job(f'schedule_{schedule_id}')
                if job:
                    schedule.next_run = job.next_run_time
                    print(f'[定时任务] 下次执行时间: {schedule.next_run}')

                db.session.commit()

                # 创建执行记录
                execution = Execution(
                    script_id=schedule.script_id,
                    status='pending',
                    params=schedule.params
                )
                db.session.add(execution)
                db.session.commit()

                print(f'[定时任务] 创建执行记录成功, 执行ID: {execution.id}')

                # 异步执行脚本
                thread = Thread(target=execute_script, args=(execution.id,))
                thread.daemon = True
                thread.start()
                print(f'[定时任务] 脚本执行线程已启动')

            except Exception as e:
                print(f'[定时任务] 执行定时任务 {schedule_id} 失败: {str(e)}')
                import traceback
                traceback.print_exc()

        # 在应用上下文中执行任务
        try:
            # 获取当前应用上下文或创建新的
            with current_app.app_context():
                run_task_in_context()
        except RuntimeError:
            # 如果没有应用上下文，这表示调度器在启动时就开始运行了
            # 这是正常的情况，任务会在后台执行
            print(f'[定时任务] 在无应用上下文的情况下执行任务 {schedule_id}')
            run_task_in_context()

    def reload_schedules(self):
        """重新加载所有定时任务"""
        from models import Schedule

        try:
            # 清空现有任务
            self.scheduler.remove_all_jobs()
            print(f'[调度器] 已清空现有任务')

            # 加载启用的任务
            schedules = Schedule.query.filter_by(enabled=True).all()
            for schedule in schedules:
                self.add_job(schedule)

            print(f'[调度器] 已加载 {len(schedules)} 个定时任务')
            return True
        except Exception as e:
            print(f'[调度器] 重新加载定时任务失败: {str(e)}')
            import traceback
            traceback.print_exc()
            return False

    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()


# 创建全局调度器实例
scheduler_manager = SchedulerManager()
