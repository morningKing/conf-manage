"""
工作流模板管理API
"""
from flask import request, jsonify
from models import db
from models.workflow_template import WorkflowTemplate
from datetime import datetime
import json
from . import api_bp


@api_bp.route('/workflow-templates', methods=['GET'])
def get_workflow_templates():
    """获取工作流模板列表"""
    try:
        category = request.args.get('category')

        query = WorkflowTemplate.query
        if category:
            query = query.filter_by(category=category)

        templates = query.order_by(
            WorkflowTemplate.is_builtin.desc(),
            WorkflowTemplate.created_at.desc()
        ).all()

        return jsonify({
            'code': 0,
            'data': [t.to_dict() for t in templates]
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/workflow-templates/<int:template_id>', methods=['GET'])
def get_workflow_template(template_id):
    """获取工作流模板详情"""
    try:
        template = WorkflowTemplate.query.get_or_404(template_id)
        return jsonify({
            'code': 0,
            'data': template.to_dict()
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/workflow-templates', methods=['POST'])
def create_workflow_template():
    """创建工作流模板"""
    try:
        data = request.get_json()

        if not data.get('name'):
            return jsonify({'code': 1, 'message': '模板名称不能为空'}), 400

        if not data.get('template_config'):
            return jsonify({'code': 1, 'message': '模板配置不能为空'}), 400

        # 检查名称是否重复
        if WorkflowTemplate.query.filter_by(name=data['name']).first():
            return jsonify({'code': 1, 'message': '模板名称已存在'}), 400

        template = WorkflowTemplate(
            name=data['name'],
            description=data.get('description', ''),
            category=data.get('category', ''),
            icon=data.get('icon', 'Document'),
            template_config=json.dumps(data['template_config']),
            is_builtin=data.get('is_builtin', False)
        )
        db.session.add(template)
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': template.to_dict(),
            'message': '模板创建成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/workflow-templates/<int:template_id>', methods=['PUT'])
def update_workflow_template(template_id):
    """更新工作流模板"""
    try:
        template = WorkflowTemplate.query.get_or_404(template_id)

        # 不允许修改内置模板
        if template.is_builtin:
            return jsonify({'code': 1, 'message': '不能修改内置模板'}), 400

        data = request.get_json()

        if 'name' in data:
            if data['name'] != template.name and WorkflowTemplate.query.filter_by(name=data['name']).first():
                return jsonify({'code': 1, 'message': '模板名称已存在'}), 400
            template.name = data['name']

        if 'description' in data:
            template.description = data['description']
        if 'category' in data:
            template.category = data['category']
        if 'icon' in data:
            template.icon = data['icon']
        if 'template_config' in data:
            template.template_config = json.dumps(data['template_config'])

        template.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': template.to_dict(),
            'message': '模板更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/workflow-templates/<int:template_id>', methods=['DELETE'])
def delete_workflow_template(template_id):
    """删除工作流模板"""
    try:
        template = WorkflowTemplate.query.get_or_404(template_id)

        # 不允许删除内置模板
        if template.is_builtin:
            return jsonify({'code': 1, 'message': '不能删除内置模板'}), 400

        db.session.delete(template)
        db.session.commit()

        return jsonify({
            'code': 0,
            'message': '模板删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/workflow-templates/<int:template_id>/use', methods=['POST'])
def use_workflow_template(template_id):
    """使用模板创建工作流"""
    try:
        template = WorkflowTemplate.query.get_or_404(template_id)
        data = request.get_json() or {}

        # 从模板配置创建工作流数据
        template_config = json.loads(template.template_config)

        # 返回模板配置，让前端使用
        return jsonify({
            'code': 0,
            'data': {
                'name': data.get('name', f"{template.name} - 副本"),
                'description': data.get('description', template.description),
                'nodes': template_config.get('nodes', []),
                'edges': template_config.get('edges', [])
            },
            'message': '模板加载成功'
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/workflow-templates/categories', methods=['GET'])
def get_template_categories():
    """获取模板分类列表"""
    try:
        categories = db.session.query(WorkflowTemplate.category).distinct().all()
        categories = [c[0] for c in categories if c[0]]

        return jsonify({
            'code': 0,
            'data': categories
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500
