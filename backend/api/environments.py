"""
环境管理 API
"""
from flask import request, jsonify
from . import api_bp
from models import db, Environment
import subprocess
import os


@api_bp.route('/environments', methods=['GET'])
def get_environments():
    """获取所有环境"""
    try:
        environments = Environment.query.order_by(Environment.type, Environment.name).all()
        return jsonify({
            'code': 0,
            'data': [env.to_dict() for env in environments],
            'message': '获取成功'
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/environments/<int:env_id>', methods=['GET'])
def get_environment(env_id):
    """获取单个环境"""
    try:
        environment = Environment.query.get_or_404(env_id)
        return jsonify({
            'code': 0,
            'data': environment.to_dict(),
            'message': '获取成功'
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 404


@api_bp.route('/environments', methods=['POST'])
def create_environment():
    """创建环境"""
    try:
        data = request.json

        # 检查名称是否重复
        if Environment.query.filter_by(name=data.get('name')).first():
            return jsonify({'code': 1, 'message': '环境名称已存在'}), 400

        # 检查可执行文件路径是否有效
        executable_path = data.get('executable_path')
        if not os.path.exists(executable_path):
            return jsonify({'code': 1, 'message': '可执行文件路径不存在'}), 400

        # 检测版本
        version = detect_version(executable_path, data.get('type'))

        # 如果设置为默认，取消其他同类型的默认环境
        if data.get('is_default'):
            Environment.query.filter_by(
                type=data.get('type'),
                is_default=True
            ).update({'is_default': False})

        environment = Environment(
            name=data.get('name'),
            type=data.get('type'),
            executable_path=executable_path,
            description=data.get('description', ''),
            is_default=data.get('is_default', False),
            version=version
        )

        db.session.add(environment)
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': environment.to_dict(),
            'message': '创建成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/environments/<int:env_id>', methods=['PUT'])
def update_environment(env_id):
    """更新环境"""
    try:
        environment = Environment.query.get_or_404(env_id)
        data = request.json

        # 检查名称是否重复（排除自己）
        if data.get('name') and data.get('name') != environment.name:
            if Environment.query.filter_by(name=data.get('name')).first():
                return jsonify({'code': 1, 'message': '环境名称已存在'}), 400

        # 如果修改了可执行文件路径，检查有效性并更新版本
        if data.get('executable_path') and data.get('executable_path') != environment.executable_path:
            if not os.path.exists(data.get('executable_path')):
                return jsonify({'code': 1, 'message': '可执行文件路径不存在'}), 400
            environment.version = detect_version(data.get('executable_path'), environment.type)

        # 如果设置为默认，取消其他同类型的默认环境
        if data.get('is_default') and not environment.is_default:
            Environment.query.filter_by(
                type=environment.type,
                is_default=True
            ).update({'is_default': False})

        # 更新字段
        for key in ['name', 'description', 'executable_path', 'is_default']:
            if key in data:
                setattr(environment, key, data[key])

        db.session.commit()

        return jsonify({
            'code': 0,
            'data': environment.to_dict(),
            'message': '更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/environments/<int:env_id>', methods=['DELETE'])
def delete_environment(env_id):
    """删除环境"""
    try:
        environment = Environment.query.get_or_404(env_id)

        # 检查是否有脚本在使用
        if environment.scripts.count() > 0:
            return jsonify({
                'code': 1,
                'message': f'该环境正在被 {environment.scripts.count()} 个脚本使用，无法删除'
            }), 400

        db.session.delete(environment)
        db.session.commit()

        return jsonify({
            'code': 0,
            'message': '删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/environments/<int:env_id>/set-default', methods=['POST'])
def set_default_environment(env_id):
    """设置为默认环境"""
    try:
        environment = Environment.query.get_or_404(env_id)

        # 取消同类型其他默认环境
        Environment.query.filter_by(
            type=environment.type,
            is_default=True
        ).update({'is_default': False})

        # 设置当前为默认
        environment.is_default = True
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': environment.to_dict(),
            'message': '设置成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/environments/detect', methods=['POST'])
def detect_environment():
    """检测环境版本"""
    try:
        data = request.json
        executable_path = data.get('executable_path')
        env_type = data.get('type')

        if not executable_path or not env_type:
            return jsonify({'code': 1, 'message': '缺少必要参数'}), 400

        if not os.path.exists(executable_path):
            return jsonify({'code': 1, 'message': '可执行文件路径不存在'}), 400

        version = detect_version(executable_path, env_type)

        return jsonify({
            'code': 0,
            'data': {'version': version},
            'message': '检测成功'
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


def detect_version(executable_path, env_type):
    """检测解释器版本"""
    try:
        if env_type == 'python':
            result = subprocess.run(
                [executable_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Python 版本信息可能在 stdout 或 stderr
            version_str = result.stdout or result.stderr
            return version_str.strip()
        elif env_type == 'javascript':
            result = subprocess.run(
                [executable_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        else:
            return '未知'
    except Exception as e:
        return f'检测失败: {str(e)}'
