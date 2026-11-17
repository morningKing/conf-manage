"""
AI配置管理API
"""
from flask import request, jsonify
from . import api_bp
from models import db, AIConfig
from utils.http_utils import validate_http_url


def _validate_base_url(base_url):
    """校验 base_url 的协议与解析 IP 边界，非法时抛出 ValueError。"""
    if base_url:
        validate_http_url(base_url)


@api_bp.route('/ai-configs', methods=['GET'])
def get_ai_configs():
    """获取所有AI配置"""
    configs = AIConfig.query.all()
    return jsonify([config.to_dict() for config in configs])


@api_bp.route('/ai-configs/active', methods=['GET'])
def get_active_ai_config():
    """获取当前激活的AI配置"""
    config = AIConfig.query.filter_by(is_active=True).first()
    if not config:
        return jsonify({'error': 'No active AI config found'}), 404
    return jsonify(config.to_dict())


@api_bp.route('/ai-configs', methods=['POST'])
def create_ai_config():
    """创建AI配置"""
    data = request.json

    # 验证必填字段
    if not data.get('api_key'):
        return jsonify({'error': 'API key is required'}), 400

    # SSRF 边界校验：非法协议或受限 IP 直接拒绝保存
    try:
        _validate_base_url(data.get('base_url'))
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    # 如果设置为激活，将其他配置设为不激活
    if data.get('is_active', False):
        AIConfig.query.update({'is_active': False})

    config = AIConfig(
        provider=data.get('provider', 'openai'),
        api_key=data.get('api_key'),
        base_url=data.get('base_url'),
        model=data.get('model', 'gpt-4'),
        is_active=data.get('is_active', True)
    )

    db.session.add(config)
    db.session.commit()

    return jsonify(config.to_dict()), 201


@api_bp.route('/ai-configs/<int:config_id>', methods=['PUT'])
def update_ai_config(config_id):
    """更新AI配置"""
    config = AIConfig.query.get(config_id)
    if not config:
        return jsonify({'error': 'AI config not found'}), 404

    data = request.json

    # 如果设置为激活，将其他配置设为不激活
    if data.get('is_active', False):
        AIConfig.query.filter(AIConfig.id != config_id).update({'is_active': False})

    if 'provider' in data:
        config.provider = data['provider']
    # 编辑时前端不回显 api_key（空串），仅在有新值时更新
    if data.get('api_key'):
        config.api_key = data['api_key']
    if 'base_url' in data:
        # SSRF 边界校验：非法协议或受限 IP 直接拒绝保存
        try:
            _validate_base_url(data['base_url'])
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        config.base_url = data['base_url']
    if 'model' in data:
        config.model = data['model']
    if 'is_active' in data:
        config.is_active = data['is_active']

    db.session.commit()

    return jsonify(config.to_dict())


@api_bp.route('/ai-configs/<int:config_id>', methods=['DELETE'])
def delete_ai_config(config_id):
    """删除AI配置"""
    config = AIConfig.query.get(config_id)
    if not config:
        return jsonify({'error': 'AI config not found'}), 404

    db.session.delete(config)
    db.session.commit()

    return '', 204


@api_bp.route('/ai-configs/<int:config_id>/activate', methods=['POST'])
def activate_ai_config(config_id):
    """激活AI配置"""
    config = AIConfig.query.get(config_id)
    if not config:
        return jsonify({'error': 'AI config not found'}), 404

    # 将所有配置设为不激活
    AIConfig.query.update({'is_active': False})

    # 激活当前配置
    config.is_active = True
    db.session.commit()

    return jsonify(config.to_dict())
