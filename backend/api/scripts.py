"""
脚本管理API
"""
from flask import request, jsonify
from . import api_bp
from models import db, Script, ScriptVersion
from config import Config
from datetime import datetime
import json
import os
import shutil


@api_bp.route('/scripts', methods=['GET'])
def get_scripts():
    """获取脚本列表"""
    try:
        scripts = Script.query.order_by(Script.created_at.desc()).all()
        return jsonify({
            'code': 0,
            'data': [script.to_dict() for script in scripts]
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/scripts/<int:script_id>', methods=['GET'])
def get_script(script_id):
    """获取脚本详情"""
    try:
        script = Script.query.get_or_404(script_id)
        return jsonify({
            'code': 0,
            'data': script.to_dict()
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/scripts', methods=['POST'])
def create_script():
    """创建脚本"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('name'):
            return jsonify({'code': 1, 'message': '脚本名称不能为空'}), 400
        if not data.get('type'):
            return jsonify({'code': 1, 'message': '脚本类型不能为空'}), 400
        if not data.get('code'):
            return jsonify({'code': 1, 'message': '脚本代码不能为空'}), 400

        # 检查名称是否重复
        if Script.query.filter_by(name=data['name']).first():
            return jsonify({'code': 1, 'message': '脚本名称已存在'}), 400

        # 创建脚本
        script = Script(
            name=data['name'],
            description=data.get('description', ''),
            type=data['type'],
            code=data['code'],
            dependencies=data.get('dependencies', ''),
            parameters=data.get('parameters', ''),
            version=1
        )
        db.session.add(script)
        db.session.flush()

        # 创建脚本工作目录
        workspace_path = Config.ensure_script_workspace(script.id)
        print(f"为脚本 {script.id} 创建工作目录: {workspace_path}")

        # 创建第一个版本
        version = ScriptVersion(
            script_id=script.id,
            version=1,
            code=data['code'],
            dependencies=data.get('dependencies', ''),
            description='初始版本'
        )
        db.session.add(version)
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': script.to_dict(),
            'message': '脚本创建成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/scripts/<int:script_id>', methods=['PUT'])
def update_script(script_id):
    """更新脚本"""
    try:
        script = Script.query.get_or_404(script_id)
        data = request.get_json()

        # 检查代码是否有变化
        code_changed = 'code' in data and data['code'] != script.code
        dependencies_changed = 'dependencies' in data and data['dependencies'] != script.dependencies

        # 更新脚本信息
        if 'name' in data:
            # 检查新名称是否与其他脚本重复
            if data['name'] != script.name and Script.query.filter_by(name=data['name']).first():
                return jsonify({'code': 1, 'message': '脚本名称已存在'}), 400
            script.name = data['name']

        if 'description' in data:
            script.description = data['description']
        if 'type' in data:
            script.type = data['type']
        if 'code' in data:
            script.code = data['code']
        if 'dependencies' in data:
            script.dependencies = data['dependencies']
        if 'parameters' in data:
            script.parameters = data['parameters']

        script.updated_at = datetime.utcnow()

        # 如果代码或依赖有变化，创建新版本
        if code_changed or dependencies_changed:
            script.version += 1
            version = ScriptVersion(
                script_id=script.id,
                version=script.version,
                code=script.code,
                dependencies=script.dependencies,
                description=data.get('version_description', f'版本 {script.version}')
            )
            db.session.add(version)

        db.session.commit()

        return jsonify({
            'code': 0,
            'data': script.to_dict(),
            'message': '脚本更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/scripts/<int:script_id>', methods=['DELETE'])
def delete_script(script_id):
    """删除脚本"""
    try:
        script = Script.query.get_or_404(script_id)

        # 删除脚本工作目录
        workspace_path = Config.get_script_workspace(script_id)
        if os.path.exists(workspace_path):
            shutil.rmtree(workspace_path)
            print(f"删除脚本 {script_id} 的工作目录: {workspace_path}")

        db.session.delete(script)
        db.session.commit()

        return jsonify({
            'code': 0,
            'message': '脚本删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/scripts/<int:script_id>/versions', methods=['GET'])
def get_script_versions(script_id):
    """获取脚本版本列表"""
    try:
        script = Script.query.get_or_404(script_id)
        versions = script.versions.order_by(ScriptVersion.version.desc()).all()

        return jsonify({
            'code': 0,
            'data': [version.to_dict() for version in versions]
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/scripts/<int:script_id>/versions/<int:version_id>', methods=['GET'])
def get_script_version(script_id, version_id):
    """获取指定版本"""
    try:
        version = ScriptVersion.query.filter_by(
            script_id=script_id,
            id=version_id
        ).first_or_404()

        return jsonify({
            'code': 0,
            'data': version.to_dict()
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/scripts/<int:script_id>/rollback/<int:version_num>', methods=['POST'])
def rollback_script(script_id, version_num):
    """回滚到指定版本"""
    try:
        script = Script.query.get_or_404(script_id)
        version = ScriptVersion.query.filter_by(
            script_id=script_id,
            version=version_num
        ).first_or_404()

        # 更新脚本代码和依赖
        script.code = version.code
        script.dependencies = version.dependencies
        script.version += 1
        script.updated_at = datetime.utcnow()

        # 创建新版本记录
        new_version = ScriptVersion(
            script_id=script.id,
            version=script.version,
            code=version.code,
            dependencies=version.dependencies,
            description=f'回滚到版本 {version_num}'
        )
        db.session.add(new_version)
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': script.to_dict(),
            'message': f'已回滚到版本 {version_num}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500
