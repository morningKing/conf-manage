"""
脚本管理API
"""
from flask import request, jsonify
from . import api_bp
from models import db, Script, ScriptVersion, Tag
from config import Config
from datetime import datetime
import json
import os
import shutil


@api_bp.route('/scripts', methods=['GET'])
def get_scripts():
    """获取脚本列表，支持过滤和搜索"""
    try:
        # 获取过滤参数
        category_id = request.args.get('category_id', type=int)
        tag_ids = request.args.get('tags', '')  # 逗号分隔的标签ID
        is_favorite = request.args.get('is_favorite', type=str)
        search = request.args.get('search', '').strip()

        # 构建查询
        query = Script.query

        # 按分类过滤
        if category_id:
            query = query.filter(Script.category_id == category_id)

        # 按收藏过滤
        if is_favorite and is_favorite.lower() == 'true':
            query = query.filter(Script.is_favorite == True)

        # 按标签过滤
        if tag_ids:
            tag_id_list = [int(tid) for tid in tag_ids.split(',') if tid.strip()]
            if tag_id_list:
                # 找到包含所有指定标签的脚本
                for tag_id in tag_id_list:
                    query = query.filter(Script.tags.any(Tag.id == tag_id))

        # 按名称或描述搜索
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                db.or_(
                    Script.name.like(search_pattern),
                    Script.description.like(search_pattern)
                )
            )

        scripts = query.order_by(Script.created_at.desc()).all()
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
            category_id=data.get('category_id'),
            is_favorite=data.get('is_favorite', False),
            version=1
        )

        # 设置环境
        if data.get('environment_id'):
            script.environment_id = data['environment_id']

        db.session.add(script)
        db.session.flush()

        # 添加标签
        tag_ids = data.get('tag_ids', [])
        if tag_ids:
            tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
            script.tags = tags

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
        if 'category_id' in data:
            script.category_id = data['category_id']
        if 'is_favorite' in data:
            script.is_favorite = data['is_favorite']
        if 'environment_id' in data:
            script.environment_id = data['environment_id']

        # 更新标签
        if 'tag_ids' in data:
            tag_ids = data['tag_ids']
            tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
            script.tags = tags

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

        # 检查是否有工作流正在使用此脚本
        from models.workflow import WorkflowNode
        workflow_nodes = WorkflowNode.query.filter_by(script_id=script_id).all()

        if workflow_nodes:
            # 获取使用此脚本的工作流列表
            workflow_names = []
            for node in workflow_nodes:
                if node.workflow and node.workflow.name not in workflow_names:
                    workflow_names.append(node.workflow.name)

            return jsonify({
                'code': 1,
                'message': f'无法删除脚本：以下工作流正在使用此脚本：{", ".join(workflow_names)}'
            }), 400

        # 检查是否有定时任务正在使用此脚本
        from models.schedule import Schedule
        schedules = Schedule.query.filter_by(script_id=script_id, enabled=True).all()

        if schedules:
            schedule_names = [s.name for s in schedules]
            return jsonify({
                'code': 1,
                'message': f'无法删除脚本：以下定时任务正在使用此脚本：{", ".join(schedule_names)}'
            }), 400

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


@api_bp.route('/scripts/<int:script_id>/favorite', methods=['POST'])
def toggle_favorite(script_id):
    """切换脚本的收藏状态"""
    try:
        script = Script.query.get_or_404(script_id)
        script.is_favorite = not script.is_favorite
        script.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': {
                'id': script.id,
                'is_favorite': script.is_favorite
            },
            'message': '已收藏' if script.is_favorite else '已取消收藏'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/scripts/<int:script_id>/versions/clean', methods=['DELETE'])
def clean_script_versions(script_id):
    """清理脚本版本历史"""
    try:
        script = Script.query.get_or_404(script_id)

        # 获取请求数据
        data = request.get_json() or {}
        keep_latest = data.get('keep_latest', 5)  # 默认保留最新5个版本

        # 获取所有版本，按版本号倒序
        all_versions = script.versions.order_by(ScriptVersion.version.desc()).all()

        # 总版本数
        total_count = len(all_versions)

        if total_count <= keep_latest:
            return jsonify({
                'code': 0,
                'message': f'当前版本数量({total_count})未超过保留数量({keep_latest})，无需清理',
                'data': {
                    'deleted_count': 0,
                    'kept_count': total_count
                }
            })

        # 保留最新的N个版本
        versions_to_keep = all_versions[:keep_latest]
        versions_to_delete = all_versions[keep_latest:]

        # 删除多余的版本
        for version in versions_to_delete:
            db.session.delete(version)

        db.session.commit()

        return jsonify({
            'code': 0,
            'message': f'已清理 {len(versions_to_delete)} 个版本历史',
            'data': {
                'deleted_count': len(versions_to_delete),
                'kept_count': keep_latest
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/scripts/<int:script_id>/executions/clean', methods=['DELETE'])
def clean_script_executions(script_id):
    """清理脚本执行历史"""
    try:
        script = Script.query.get_or_404(script_id)

        # 获取请求数据
        data = request.get_json() or {}

        # 清理条件
        keep_latest = data.get('keep_latest', 50)  # 默认保留最新50条
        status = data.get('status')  # 按状态过滤：success, failed, cancelled
        before_days = data.get('before_days')  # 清理N天前的记录

        # 构建查询
        from models.execution import Execution
        query = Execution.query.filter_by(script_id=script_id)

        # 按状态过滤
        if status:
            query = query.filter_by(status=status)

        # 按时间过滤
        if before_days:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=before_days)
            query = query.filter(Execution.created_at < cutoff_date)

        # 获取所有符合条件的执行记录
        all_executions = query.order_by(Execution.created_at.desc()).all()

        # 总记录数
        total_count = len(all_executions)

        if total_count <= keep_latest:
            return jsonify({
                'code': 0,
                'message': f'当前执行记录数量({total_count})未超过保留数量({keep_latest})，无需清理',
                'data': {
                    'deleted_count': 0,
                    'kept_count': total_count
                }
            })

        # 保留最新的N条记录
        executions_to_keep = all_executions[:keep_latest]
        executions_to_delete = all_executions[keep_latest:]

        # 删除多余的执行记录
        deleted_count = 0
        for execution in executions_to_delete:
            # 删除日志文件
            if execution.log_file and os.path.exists(execution.log_file):
                try:
                    os.remove(execution.log_file)
                    print(f"删除日志文件: {execution.log_file}")
                except Exception as log_error:
                    print(f"删除日志文件失败: {log_error}")

            db.session.delete(execution)
            deleted_count += 1

        db.session.commit()

        return jsonify({
            'code': 0,
            'message': f'已清理 {deleted_count} 条执行历史',
            'data': {
                'deleted_count': deleted_count,
                'kept_count': keep_latest
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500
