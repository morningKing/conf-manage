"""
Webhook管理API
"""
from flask import request, jsonify
from . import api_bp
from models import db, Webhook, WebhookLog, Script
from datetime import datetime


@api_bp.route('/webhooks', methods=['GET'])
def get_webhooks():
    """获取Webhook列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()

        query = Webhook.query

        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                db.or_(
                    Webhook.name.like(search_pattern),
                    Webhook.description.like(search_pattern)
                )
            )

        pagination = query.order_by(Webhook.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'code': 0,
            'data': {
                'items': [wh.to_dict() for wh in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/webhooks', methods=['POST'])
def create_webhook():
    """创建Webhook"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('name'):
            return jsonify({'code': 1, 'message': 'Webhook名称不能为空'}), 400
        if not data.get('script_id'):
            return jsonify({'code': 1, 'message': '必须选择脚本'}), 400

        # 检查名称是否重复
        if Webhook.query.filter_by(name=data['name']).first():
            return jsonify({'code': 1, 'message': 'Webhook名称已存在'}), 400

        # 检查脚本是否存在
        script = Script.query.get(data['script_id'])
        if not script:
            return jsonify({'code': 1, 'message': '脚本不存在'}), 404

        # 处理自定义webhook_key
        webhook_key = data.get('webhook_key', '').strip()
        if webhook_key:
            # 验证格式：只允许字母、数字、连字符、下划线
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', webhook_key):
                return jsonify({'code': 1, 'message': 'Webhook路径只能包含字母、数字、连字符和下划线'}), 400

            # 检查是否重复
            if Webhook.query.filter_by(webhook_key=webhook_key).first():
                return jsonify({'code': 1, 'message': 'Webhook路径已存在'}), 400

        # 创建webhook
        webhook = Webhook(
            name=data['name'],
            description=data.get('description', ''),
            script_id=data['script_id'],
            webhook_key=webhook_key if webhook_key else None,  # 如果为空则自动生成
            token_enabled=data.get('token_enabled', False),
            execution_mode=data.get('execution_mode', 'async'),
            timeout=data.get('timeout', 30),
            pass_full_request=data.get('pass_full_request', True),
            enabled=data.get('enabled', True)
        )

        db.session.add(webhook)
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': webhook.to_dict(),
            'message': 'Webhook创建成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/webhooks/<int:webhook_id>', methods=['GET'])
def get_webhook(webhook_id):
    """获取Webhook详情"""
    try:
        webhook = Webhook.query.get_or_404(webhook_id)
        return jsonify({
            'code': 0,
            'data': webhook.to_dict()
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/webhooks/<int:webhook_id>', methods=['PUT'])
def update_webhook(webhook_id):
    """更新Webhook"""
    try:
        webhook = Webhook.query.get_or_404(webhook_id)
        data = request.get_json()

        # 更新字段
        if 'name' in data:
            if data['name'] != webhook.name and Webhook.query.filter_by(name=data['name']).first():
                return jsonify({'code': 1, 'message': 'Webhook名称已存在'}), 400
            webhook.name = data['name']

        if 'description' in data:
            webhook.description = data['description']
        if 'script_id' in data:
            webhook.script_id = data['script_id']
        if 'token_enabled' in data:
            webhook.token_enabled = data['token_enabled']
            if webhook.token_enabled and not webhook.token:
                webhook.token = Webhook.generate_token()
        if 'execution_mode' in data:
            webhook.execution_mode = data['execution_mode']
        if 'timeout' in data:
            webhook.timeout = data['timeout']
        if 'pass_full_request' in data:
            webhook.pass_full_request = data['pass_full_request']
        if 'enabled' in data:
            webhook.enabled = data['enabled']

        webhook.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': webhook.to_dict(),
            'message': 'Webhook更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/webhooks/<int:webhook_id>', methods=['DELETE'])
def delete_webhook(webhook_id):
    """删除Webhook"""
    try:
        webhook = Webhook.query.get_or_404(webhook_id)
        db.session.delete(webhook)
        db.session.commit()

        return jsonify({
            'code': 0,
            'message': 'Webhook删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/webhooks/<int:webhook_id>/regenerate-token', methods=['POST'])
def regenerate_webhook_token(webhook_id):
    """重新生成Token"""
    try:
        webhook = Webhook.query.get_or_404(webhook_id)

        if not webhook.token_enabled:
            return jsonify({'code': 1, 'message': 'Token验证未启用'}), 400

        webhook.token = Webhook.generate_token()
        webhook.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': {'token': webhook.token},
            'message': 'Token重新生成成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/webhooks/<int:webhook_id>/toggle', methods=['POST'])
def toggle_webhook(webhook_id):
    """启用/禁用Webhook"""
    try:
        webhook = Webhook.query.get_or_404(webhook_id)
        webhook.enabled = not webhook.enabled
        webhook.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': {'enabled': webhook.enabled},
            'message': '已启用' if webhook.enabled else '已禁用'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/webhooks/<int:webhook_id>/logs', methods=['GET'])
def get_webhook_logs(webhook_id):
    """获取Webhook调用日志"""
    try:
        webhook = Webhook.query.get_or_404(webhook_id)

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        pagination = WebhookLog.query.filter_by(webhook_id=webhook_id).order_by(
            WebhookLog.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'code': 0,
            'data': {
                'items': [log.to_dict() for log in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/webhooks/<int:webhook_id>/statistics', methods=['GET'])
def get_webhook_statistics(webhook_id):
    """获取Webhook统计信息"""
    try:
        webhook = Webhook.query.get_or_404(webhook_id)

        # 计算成功率
        success_rate = 0
        if webhook.call_count > 0:
            success_rate = round(webhook.success_count / webhook.call_count * 100, 2)

        # 最近调用记录
        recent_logs = WebhookLog.query.filter_by(webhook_id=webhook_id).order_by(
            WebhookLog.created_at.desc()
        ).limit(10).all()

        return jsonify({
            'code': 0,
            'data': {
                'call_count': webhook.call_count,
                'success_count': webhook.success_count,
                'failed_count': webhook.failed_count,
                'success_rate': success_rate,
                'last_called_at': webhook.last_called_at.isoformat() if webhook.last_called_at else None,
                'recent_logs': [log.to_dict() for log in recent_logs]
            }
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500
