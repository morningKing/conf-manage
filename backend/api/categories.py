"""
分类和标签API
"""
from flask import request, jsonify
from . import api_bp
from models import db, Category, Tag, Script


@api_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取所有分类"""
    try:
        categories = Category.query.order_by(Category.sort_order).all()
        return jsonify({
            'code': 0,
            'data': [cat.to_dict() for cat in categories]
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/categories', methods=['POST'])
def create_category():
    """创建分类"""
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        color = data.get('color', '#409EFF')
        icon = data.get('icon', '')
        sort_order = data.get('sort_order', 0)

        if not name:
            return jsonify({'code': 1, 'message': '分类名称不能为空'}), 400

        # 检查名称是否已存在
        existing = Category.query.filter_by(name=name).first()
        if existing:
            return jsonify({'code': 1, 'message': '分类名称已存在'}), 400

        category = Category(
            name=name,
            description=description,
            color=color,
            icon=icon,
            sort_order=sort_order
        )
        db.session.add(category)
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': category.to_dict(),
            'message': '分类创建成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """更新分类"""
    try:
        category = Category.query.get_or_404(category_id)
        data = request.get_json()

        if 'name' in data:
            # 检查新名称是否与其他分类冲突
            existing = Category.query.filter(
                Category.name == data['name'],
                Category.id != category_id
            ).first()
            if existing:
                return jsonify({'code': 1, 'message': '分类名称已存在'}), 400
            category.name = data['name']

        if 'description' in data:
            category.description = data['description']
        if 'color' in data:
            category.color = data['color']
        if 'icon' in data:
            category.icon = data['icon']
        if 'sort_order' in data:
            category.sort_order = data['sort_order']

        db.session.commit()

        return jsonify({
            'code': 0,
            'data': category.to_dict(),
            'message': '分类更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """删除分类"""
    try:
        category = Category.query.get_or_404(category_id)

        # 检查是否有脚本使用此分类
        script_count = Script.query.filter_by(category_id=category_id).count()
        if script_count > 0:
            return jsonify({
                'code': 1,
                'message': f'该分类下还有{script_count}个脚本，无法删除'
            }), 400

        db.session.delete(category)
        db.session.commit()

        return jsonify({
            'code': 0,
            'message': '分类删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/tags', methods=['GET'])
def get_tags():
    """获取所有标签"""
    try:
        tags = Tag.query.order_by(Tag.name).all()
        return jsonify({
            'code': 0,
            'data': [tag.to_dict() for tag in tags]
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/tags', methods=['POST'])
def create_tag():
    """创建标签"""
    try:
        data = request.get_json()
        name = data.get('name')
        color = data.get('color', '#67C23A')

        if not name:
            return jsonify({'code': 1, 'message': '标签名称不能为空'}), 400

        # 检查名称是否已存在
        existing = Tag.query.filter_by(name=name).first()
        if existing:
            return jsonify({'code': 1, 'message': '标签名称已存在'}), 400

        tag = Tag(name=name, color=color)
        db.session.add(tag)
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': tag.to_dict(),
            'message': '标签创建成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/tags/<int:tag_id>', methods=['PUT'])
def update_tag(tag_id):
    """更新标签"""
    try:
        tag = Tag.query.get_or_404(tag_id)
        data = request.get_json()

        if 'name' in data:
            # 检查新名称是否与其他标签冲突
            existing = Tag.query.filter(
                Tag.name == data['name'],
                Tag.id != tag_id
            ).first()
            if existing:
                return jsonify({'code': 1, 'message': '标签名称已存在'}), 400
            tag.name = data['name']

        if 'color' in data:
            tag.color = data['color']

        db.session.commit()

        return jsonify({
            'code': 0,
            'data': tag.to_dict(),
            'message': '标签更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/tags/<int:tag_id>', methods=['DELETE'])
def delete_tag(tag_id):
    """删除标签"""
    try:
        tag = Tag.query.get_or_404(tag_id)

        # 标签关联会自动解除，无需手动处理
        db.session.delete(tag)
        db.session.commit()

        return jsonify({
            'code': 0,
            'message': '标签删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500
