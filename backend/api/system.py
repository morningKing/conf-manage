"""
系统管理API
"""
from flask import jsonify, request
from api import api_bp
from utils.cleanup import get_cleanup_stats, run_cleanup
from config import Config


@api_bp.route('/system/cleanup/stats', methods=['GET'])
def get_cleanup_stats_api():
    """
    获取清理统计信息
    GET /api/system/cleanup/stats
    """
    try:
        stats = get_cleanup_stats()

        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'code': 1,
            'message': f'获取清理统计失败: {str(e)}'
        }), 500


@api_bp.route('/system/cleanup', methods=['POST'])
def execute_cleanup():
    """
    执行清理操作
    POST /api/system/cleanup
    """
    try:
        result = run_cleanup()

        return jsonify({
            'code': 0,
            'message': '清理完成',
            'data': result
        })
    except Exception as e:
        return jsonify({
            'code': 1,
            'message': f'清理操作失败: {str(e)}'
        }), 500


@api_bp.route('/system/cleanup/config', methods=['GET'])
def get_cleanup_config():
    """
    获取清理配置
    GET /api/system/cleanup/config
    """
    try:
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'threshold': Config.CLEANUP_THRESHOLD
            }
        })
    except Exception as e:
        return jsonify({
            'code': 1,
            'message': f'获取配置失败: {str(e)}'
        }), 500


@api_bp.route('/system/cleanup/config', methods=['PUT'])
def update_cleanup_config():
    """
    更新清理配置
    PUT /api/system/cleanup/config

    Body参数：
    - threshold: 清理阈值（50-10000）
    """
    try:
        data = request.get_json() or {}
        threshold = data.get('threshold')

        # 验证参数
        if threshold is None:
            return jsonify({
                'code': 1,
                'message': '缺少threshold参数'
            }), 400

        if not isinstance(threshold, int):
            return jsonify({
                'code': 1,
                'message': 'threshold必须是整数'
            }), 400

        if threshold < 50 or threshold > 10000:
            return jsonify({
                'code': 1,
                'message': 'threshold必须在50-10000范围内'
            }), 400

        # 更新配置（仅运行时生效）
        Config.CLEANUP_THRESHOLD = threshold

        return jsonify({
            'code': 0,
            'message': '配置更新成功',
            'data': {
                'threshold': Config.CLEANUP_THRESHOLD
            }
        })
    except Exception as e:
        return jsonify({
            'code': 1,
            'message': f'更新配置失败: {str(e)}'
        }), 500