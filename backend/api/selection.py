"""
选择会话API - 用于批量操作的状态管理
"""
from flask import request, jsonify
from . import api_bp
from models import db, SelectionSession, Execution
import uuid
import json
import os


@api_bp.route('/executions/selection/create', methods=['POST'])
def create_selection_session():
    """创建新的选择会话"""
    try:
        session_id = uuid.uuid4().hex[:16]
        session = SelectionSession(session_id=session_id)
        db.session.add(session)
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': {
                'session_id': session_id,
                'max_limit': SelectionSession.MAX_SELECTIONS
            },
            'message': '选择会话已创建'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions/selection/<session_id>', methods=['GET'])
def get_selection_session(session_id):
    """获取选择会话详情"""
    try:
        session = SelectionSession.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({'code': 1, 'message': '会话不存在'}), 404

        # 获取选中项基本信息
        ids = session.get_ids()
        items = []
        for eid in ids:
            execution = Execution.query.get(eid)
            if execution:
                items.append({
                    'id': execution.id,
                    'script_name': execution.script.name if execution.script else None,
                    'status': execution.status,
                    'created_at': execution.created_at.isoformat() if execution.created_at else None
                })

        return jsonify({
            'code': 0,
            'data': {
                'session_id': session.session_id,
                'count': session.count,
                'max_limit': SelectionSession.MAX_SELECTIONS,
                'ids': ids,
                'items': items
            }
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions/selection/<session_id>/add', methods=['POST'])
def add_to_selection(session_id):
    """添加执行ID到选择会话"""
    try:
        session = SelectionSession.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({'code': 1, 'message': '会话不存在'}), 404

        data = request.get_json()
        execution_ids = data.get('execution_ids', [])

        if not isinstance(execution_ids, list):
            return jsonify({'code': 1, 'message': 'execution_ids必须是数组'}), 400

        # 验证ID是否存在
        valid_ids = []
        for eid in execution_ids:
            if Execution.query.get(eid):
                valid_ids.append(eid)

        new_count = session.add_ids(valid_ids)
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': {
                'count': new_count,
                'max_limit': SelectionSession.MAX_SELECTIONS,
                'max_reached': session.is_max_reached()
            },
            'message': f'已添加{len(valid_ids)}项'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions/selection/<session_id>/remove', methods=['POST'])
def remove_from_selection(session_id):
    """从选择会话移除执行ID"""
    try:
        session = SelectionSession.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({'code': 1, 'message': '会话不存在'}), 404

        data = request.get_json()
        execution_ids = data.get('execution_ids', [])

        if not isinstance(execution_ids, list):
            return jsonify({'code': 1, 'message': 'execution_ids必须是数组'}), 400

        new_count = session.remove_ids(execution_ids)
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': {
                'count': new_count,
                'max_limit': SelectionSession.MAX_SELECTIONS
            },
            'message': f'已移除{len(execution_ids)}项'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions/selection/<session_id>/clear', methods=['POST'])
def clear_selection(session_id):
    """清空选择会话"""
    try:
        session = SelectionSession.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({'code': 1, 'message': '会话不存在'}), 404

        session.clear()
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': {
                'count': 0,
                'max_limit': SelectionSession.MAX_SELECTIONS
            },
            'message': '选择已清空'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions/selection/<session_id>/delete', methods=['POST'])
def delete_selection_batch(session_id):
    """批量删除选中的执行记录"""
    try:
        import shutil
        from config import Config

        session = SelectionSession.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({'code': 1, 'message': '会话不存在'}), 404

        ids = session.get_ids()
        if not ids:
            return jsonify({'code': 1, 'message': '没有选中项'}), 400

        result = {
            'total': len(ids),
            'success': 0,
            'failed': 0,
            'details': []
        }

        for eid in ids:
            execution = Execution.query.get(eid)
            if not execution:
                result['failed'] += 1
                result['details'].append({
                    'id': eid,
                    'status': 'failed',
                    'message': '执行记录不存在'
                })
                continue

            try:
                # 删除日志文件
                if execution.log_file and os.path.exists(execution.log_file):
                    os.remove(execution.log_file)

                # 删除执行空间
                execution_space = Config.get_execution_space(eid)
                if os.path.exists(execution_space):
                    shutil.rmtree(execution_space)

                db.session.delete(execution)
                result['success'] += 1
                result['details'].append({
                    'id': eid,
                    'status': 'success',
                    'message': '删除成功'
                })

            except Exception as e:
                result['failed'] += 1
                result['details'].append({
                    'id': eid,
                    'status': 'failed',
                    'message': str(e)
                })

        # 清空选择会话
        session.clear()
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': result,
            'message': f'批量删除完成: 成功{result["success"]}个，失败{result["failed"]}个'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500