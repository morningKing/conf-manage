"""
文件夹管理API
"""
from flask import request, jsonify
from . import api_bp
from models import db, Folder, Script, Tag


@api_bp.route('/folders/tree', methods=['GET'])
def get_folder_tree():
    """获取完整文件夹树"""
    try:
        root_folders = Folder.query.filter(Folder.parent_id.is_(None)).order_by(Folder.sort_order, Folder.name).all()
        tree = [folder.to_tree_dict() for folder in root_folders]
        return jsonify({'code': 0, 'data': tree})
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/folders/<int:folder_id>/contents', methods=['GET'])
def get_folder_contents(folder_id):
    """获取文件夹内容（子文件夹 + 脚本）"""
    try:
        folder = Folder.query.get_or_404(folder_id)
        sub_folders = Folder.query.filter_by(parent_id=folder_id).order_by(Folder.sort_order, Folder.name).all()
        scripts = Script.query.filter_by(folder_id=folder_id).order_by(Script.name).all()

        return jsonify({
            'code': 0,
            'data': {
                'folder': folder.to_dict(),
                'folders': [f.to_dict() for f in sub_folders],
                'scripts': [s.to_dict() for s in scripts]
            }
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/folders/root/contents', methods=['GET'])
def get_root_contents():
    """获取根目录内容"""
    try:
        root_folders = Folder.query.filter(Folder.parent_id.is_(None)).order_by(Folder.sort_order, Folder.name).all()
        root_scripts = Script.query.filter(Script.folder_id.is_(None)).order_by(Script.name).all()

        return jsonify({
            'code': 0,
            'data': {
                'folder': None,
                'folders': [f.to_dict() for f in root_folders],
                'scripts': [s.to_dict() for s in root_scripts]
            }
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/folders', methods=['POST'])
def create_folder():
    """创建文件夹"""
    try:
        data = request.get_json()
        name = data.get('name')
        parent_id = data.get('parent_id')

        if not name:
            return jsonify({'code': 1, 'message': '文件夹名称不能为空'}), 400

        # 检查同级目录下名称唯一
        existing = Folder.query.filter_by(name=name, parent_id=parent_id).first()
        if existing:
            return jsonify({'code': 1, 'message': '同级目录下已存在同名文件夹'}), 400

        # 验证父文件夹存在
        if parent_id:
            parent = Folder.query.get(parent_id)
            if not parent:
                return jsonify({'code': 1, 'message': '父文件夹不存在'}), 400

        folder = Folder(name=name, parent_id=parent_id)
        db.session.add(folder)
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': folder.to_dict(),
            'message': '文件夹创建成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/folders/<int:folder_id>', methods=['PUT'])
def update_folder(folder_id):
    """更新文件夹（重命名）"""
    try:
        folder = Folder.query.get_or_404(folder_id)
        data = request.get_json()

        if 'name' in data:
            existing = Folder.query.filter(
                Folder.name == data['name'],
                Folder.parent_id == folder.parent_id,
                Folder.id != folder_id
            ).first()
            if existing:
                return jsonify({'code': 1, 'message': '同级目录下已存在同名文件夹'}), 400
            folder.name = data['name']

        if 'sort_order' in data:
            folder.sort_order = data['sort_order']

        db.session.commit()

        return jsonify({
            'code': 0,
            'data': folder.to_dict(),
            'message': '文件夹更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/folders/<int:folder_id>', methods=['DELETE'])
def delete_folder(folder_id):
    """删除文件夹"""
    try:
        folder = Folder.query.get_or_404(folder_id)

        child_count = Folder.query.filter_by(parent_id=folder_id).count()
        if child_count > 0:
            return jsonify({'code': 1, 'message': f'该文件夹下还有{child_count}个子文件夹，无法删除'}), 400

        script_count = Script.query.filter_by(folder_id=folder_id).count()
        if script_count > 0:
            return jsonify({'code': 1, 'message': f'该文件夹下还有{script_count}个脚本，无法删除'}), 400

        db.session.delete(folder)
        db.session.commit()

        return jsonify({'code': 0, 'message': '文件夹删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/folders/<int:folder_id>/move', methods=['POST'])
def move_folder(folder_id):
    """移动文件夹到新的父文件夹"""
    try:
        folder = Folder.query.get_or_404(folder_id)
        data = request.get_json()
        new_parent_id = data.get('parent_id')

        if new_parent_id == folder_id:
            return jsonify({'code': 1, 'message': '不能将文件夹移动到自身'}), 400

        # 循环检测
        if new_parent_id:
            current = Folder.query.get(new_parent_id)
            while current:
                if current.id == folder_id:
                    return jsonify({'code': 1, 'message': '不能将文件夹移动到其子文件夹中'}), 400
                current = current.parent

        existing = Folder.query.filter(
            Folder.name == folder.name,
            Folder.parent_id == new_parent_id,
            Folder.id != folder_id
        ).first()
        if existing:
            return jsonify({'code': 1, 'message': '目标目录下已存在同名文件夹'}), 400

        folder.parent_id = new_parent_id
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': folder.to_dict(),
            'message': '文件夹移动成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/folders/<int:folder_id>/path', methods=['GET'])
def get_folder_path(folder_id):
    """获取文件夹的完整路径（面包屑用）"""
    try:
        path = []
        folder = Folder.query.get_or_404(folder_id)
        while folder:
            path.insert(0, folder.to_dict())
            folder = folder.parent

        return jsonify({'code': 0, 'data': path})
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


# ===== Tag API（从 categories.py 迁移） =====

@api_bp.route('/tags', methods=['GET'])
def get_tags():
    """获取所有标签"""
    try:
        tags = Tag.query.order_by(Tag.name).all()
        return jsonify({'code': 0, 'data': [tag.to_dict() for tag in tags]})
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

        existing = Tag.query.filter_by(name=name).first()
        if existing:
            return jsonify({'code': 1, 'message': '标签名称已存在'}), 400

        tag = Tag(name=name, color=color)
        db.session.add(tag)
        db.session.commit()

        return jsonify({'code': 0, 'data': tag.to_dict(), 'message': '标签创建成功'})
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
            existing = Tag.query.filter(Tag.name == data['name'], Tag.id != tag_id).first()
            if existing:
                return jsonify({'code': 1, 'message': '标签名称已存在'}), 400
            tag.name = data['name']

        if 'color' in data:
            tag.color = data['color']

        db.session.commit()
        return jsonify({'code': 0, 'data': tag.to_dict(), 'message': '标签更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/tags/<int:tag_id>', methods=['DELETE'])
def delete_tag(tag_id):
    """删除标签"""
    try:
        tag = Tag.query.get_or_404(tag_id)
        db.session.delete(tag)
        db.session.commit()
        return jsonify({'code': 0, 'message': '标签删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500
