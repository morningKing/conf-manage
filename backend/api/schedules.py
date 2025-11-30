"""
定时任务API
"""
from flask import request, jsonify
from . import api_bp
from models import db, Schedule, Script
from services.scheduler import scheduler_manager
import json


@api_bp.route('/schedules', methods=['GET'])
def get_schedules():
    """获取定时任务列表"""
    try:
        schedules = Schedule.query.order_by(Schedule.created_at.desc()).all()
        return jsonify({
            'code': 0,
            'data': [schedule.to_dict() for schedule in schedules]
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/schedules/<int:schedule_id>', methods=['GET'])
def get_schedule(schedule_id):
    """获取定时任务详情"""
    try:
        schedule = Schedule.query.get_or_404(schedule_id)
        return jsonify({
            'code': 0,
            'data': schedule.to_dict()
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/schedules', methods=['POST'])
def create_schedule():
    """创建定时任务"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('name'):
            return jsonify({'code': 1, 'message': '任务名称不能为空'}), 400
        if not data.get('script_id'):
            return jsonify({'code': 1, 'message': '脚本ID不能为空'}), 400
        if not data.get('cron'):
            return jsonify({'code': 1, 'message': 'Cron表达式不能为空'}), 400

        # 验证脚本是否存在
        script = Script.query.get(data['script_id'])
        if not script:
            return jsonify({'code': 1, 'message': '脚本不存在'}), 404

        # 创建定时任务
        schedule = Schedule(
            script_id=data['script_id'],
            name=data['name'],
            description=data.get('description', ''),
            cron=data['cron'],
            params=data.get('params', ''),
            enabled=data.get('enabled', True)
        )
        db.session.add(schedule)
        db.session.commit()

        # 添加到调度器
        if schedule.enabled:
            scheduler_manager.add_job(schedule)

        return jsonify({
            'code': 0,
            'data': schedule.to_dict(),
            'message': '定时任务创建成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/schedules/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """更新定时任务"""
    try:
        schedule = Schedule.query.get_or_404(schedule_id)
        data = request.get_json()

        # 更新任务信息
        if 'name' in data:
            schedule.name = data['name']
        if 'description' in data:
            schedule.description = data['description']
        if 'cron' in data:
            schedule.cron = data['cron']
        if 'params' in data:
            schedule.params = data['params']
        if 'enabled' in data:
            old_enabled = schedule.enabled
            schedule.enabled = data['enabled']

            # 如果启用状态发生变化，更新调度器
            if old_enabled != schedule.enabled:
                if schedule.enabled:
                    scheduler_manager.add_job(schedule)
                else:
                    scheduler_manager.remove_job(schedule.id)

        db.session.commit()

        # 如果Cron表达式改变且任务启用，重新添加到调度器
        if 'cron' in data and schedule.enabled:
            scheduler_manager.remove_job(schedule.id)
            scheduler_manager.add_job(schedule)

        return jsonify({
            'code': 0,
            'data': schedule.to_dict(),
            'message': '定时任务更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """删除定时任务"""
    try:
        schedule = Schedule.query.get_or_404(schedule_id)

        # 从调度器中移除
        scheduler_manager.remove_job(schedule_id)

        db.session.delete(schedule)
        db.session.commit()

        return jsonify({
            'code': 0,
            'message': '定时任务已删除'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/schedules/<int:schedule_id>/toggle', methods=['POST'])
def toggle_schedule(schedule_id):
    """启用/禁用定时任务"""
    try:
        schedule = Schedule.query.get_or_404(schedule_id)
        schedule.enabled = not schedule.enabled
        db.session.commit()

        # 更新调度器
        if schedule.enabled:
            scheduler_manager.add_job(schedule)
        else:
            scheduler_manager.remove_job(schedule.id)

        return jsonify({
            'code': 0,
            'data': schedule.to_dict(),
            'message': f'任务已{"启用" if schedule.enabled else "禁用"}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/schedules/<int:schedule_id>/run', methods=['POST'])
def run_schedule_now(schedule_id):
    """立即运行定时任务"""
    try:
        schedule = Schedule.query.get_or_404(schedule_id)

        # 创建执行记录并执行
        from ..models import Execution
        from ..services.executor import execute_script
        from threading import Thread

        execution = Execution(
            script_id=schedule.script_id,
            status='pending',
            params=schedule.params
        )
        db.session.add(execution)
        db.session.commit()

        thread = Thread(target=execute_script, args=(execution.id,))
        thread.start()

        return jsonify({
            'code': 0,
            'data': execution.to_dict(),
            'message': '任务已启动执行'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500
