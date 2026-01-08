"""
Webhook触发处理API
"""
from flask import request, jsonify
from . import api_bp
from models import db, Webhook
from services.webhook_executor import execute_webhook
import json


@api_bp.route('/webhook/<webhook_key>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def trigger_webhook(webhook_key):
    """
    触发Webhook
    公开端点，外部系统调用
    """
    try:
        # 查找webhook
        webhook = Webhook.query.filter_by(webhook_key=webhook_key).first()

        if not webhook:
            return jsonify({
                'code': 1,
                'message': 'Webhook不存在'
            }), 404

        if not webhook.enabled:
            return jsonify({
                'code': 1,
                'message': 'Webhook已禁用'
            }), 403

        # Token验证
        if webhook.token_enabled:
            token = None

            # 从Header获取
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]

            # 从Query参数获取
            if not token:
                token = request.args.get('token', '')

            # 验证Token
            if not token or token != webhook.token:
                return jsonify({
                    'code': 1,
                    'message': 'Token验证失败'
                }), 401

        # 解析请求数据
        request_data = {
            'method': request.method,
            'headers': dict(request.headers),
            'body': {},
            'query': dict(request.args),
            'ip': request.remote_addr
        }

        # 解析body
        if request.is_json:
            request_data['body'] = request.get_json() or {}
        elif request.form:
            request_data['body'] = dict(request.form)
        elif request.data:
            try:
                request_data['body'] = json.loads(request.data.decode('utf-8'))
            except:
                request_data['body'] = {'raw': request.data.decode('utf-8', errors='ignore')}

        # 执行webhook
        status, data, code = execute_webhook(webhook.id, request_data, request)

        return jsonify({
            'code': 0 if status == 'success' else 1,
            'data': data,
            'message': '执行成功' if status == 'success' else data.get('error', '执行失败')
        }), code

    except Exception as e:
        return jsonify({
            'code': 1,
            'message': str(e)
        }), 500
