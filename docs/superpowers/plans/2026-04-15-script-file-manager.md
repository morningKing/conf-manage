# Script File Manager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the script management page from a table list into a file-manager-style interface with multi-level folders, right-click context menus, and drag-and-drop.

**Architecture:** Replace the flat Category model with a tree-structured Folder model (self-referencing parent_id). Frontend becomes a left-right split layout: el-tree folder navigation on the left, grid content view on the right. Scripts gain a `folder_id` field replacing `category_id`.

**Tech Stack:** Vue 3 + Element Plus (el-tree, el-breadcrumb, el-card), Flask + SQLAlchemy, native HTML5 drag-and-drop API, CodeMirror 6 (existing)

---

## File Structure

### Backend (modify existing)
- `backend/models/folder.py` — New file: Folder model with self-referencing parent_id (replaces category.py)
- `backend/models/script.py` — Modify: category_id → folder_id
- `backend/models/__init__.py` — Modify: import Folder instead of Category
- `backend/api/folders.py` — New file: Folder CRUD + tree API (replaces categories.py)
- `backend/api/scripts.py` — Modify: add move endpoint, change category_id → folder_id
- `backend/api/__init__.py` — Modify: import folders instead of categories

### Frontend (modify existing)
- `frontend/src/views/Scripts.vue` — Rewrite: file manager layout
- `frontend/src/api/index.js` — Modify: replace category APIs with folder APIs, add move/tree APIs
- `frontend/src/router/index.js` — Modify: remove /categories route
- `frontend/src/layouts/components/sidebar/index.vue` — Modify: remove 分类管理 menu entry
- `frontend/src/views/AIScriptWriter.vue` — Modify: category_id → folder_id, use folders API

### Delete
- `backend/models/category.py` — Delete (replaced by folder.py)
- `backend/api/categories.py` — Delete (replaced by folders.py)
- `frontend/src/views/Categories.vue` — Delete (no longer needed)

---

## Task 1: Backend — Create Folder Model

**Files:**
- Create: `backend/models/folder.py`
- Modify: `backend/models/__init__.py`
- Delete: `backend/models/category.py`

- [ ] **Step 1: Create `backend/models/folder.py`**

```python
"""
文件夹模型（替代分类）
"""
from datetime import datetime
from . import db


class Folder(db.Model):
    """文件夹表"""
    __tablename__ = 'folders'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent = db.relationship('Folder', remote_side=[id], backref=db.backref('children', lazy='dynamic'))

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_tree_dict(self):
        """转换为树形字典（含子文件夹）"""
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'sort_order': self.sort_order,
            'children': [child.to_tree_dict() for child in self.children.order_by(Folder.sort_order, Folder.name).all()],
            'script_count': len(self.scripts) if hasattr(self, 'scripts') else 0
        }
```

- [ ] **Step 2: Update `backend/models/__init__.py`**

Replace the Category import line and __all__ entry:

Change:
```python
from .category import Category, Tag, script_tags
```
To:
```python
from .folder import Folder
from .category import Tag, script_tags
```

Change in `__all__`:
```python
'Category', 'Tag', 'script_tags',
```
To:
```python
'Folder', 'Tag', 'script_tags',
```

- [ ] **Step 3: Commit**

```bash
git add backend/models/folder.py backend/models/__init__.py
git commit -m "feat: add Folder model replacing Category for tree-structured script organization"
```

---

## Task 2: Backend — Modify Script Model

**Files:**
- Modify: `backend/models/script.py`

- [ ] **Step 1: Update Script model — change category_id to folder_id**

In `backend/models/script.py`, make these changes:

Change:
```python
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)  # 分类ID
```
To:
```python
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)  # 文件夹ID
```

Change the relationship:
```python
    category = db.relationship('Category', backref='scripts', foreign_keys=[category_id])
```
To:
```python
    folder = db.relationship('Folder', backref='scripts', foreign_keys=[folder_id])
```

In `to_dict()`, change:
```python
            'category_id': self.category_id,
            'is_favorite': self.is_favorite,
            'category': self.category.to_dict() if self.category else None,
```
To:
```python
            'folder_id': self.folder_id,
            'is_favorite': self.is_favorite,
            'folder': self.folder.to_dict() if self.folder else None,
```

- [ ] **Step 2: Commit**

```bash
git add backend/models/script.py
git commit -m "feat: change Script.category_id to folder_id"
```

---

## Task 3: Backend — Modify Category Model (Keep Tag, Remove Category class)

**Files:**
- Modify: `backend/models/category.py`

- [ ] **Step 1: Remove Category class from category.py, keep Tag and script_tags**

Rewrite `backend/models/category.py` to only contain Tag and script_tags:

```python
"""
脚本标签模型
"""
from datetime import datetime
from . import db


class Tag(db.Model):
    """脚本标签表"""
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(20), default='#67C23A')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# 脚本与标签的多对多关系表
script_tags = db.Table('script_tags',
    db.Column('script_id', db.Integer, db.ForeignKey('scripts.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)
```

- [ ] **Step 2: Commit**

```bash
git add backend/models/category.py
git commit -m "refactor: remove Category class, keep Tag in category.py"
```

---

## Task 4: Backend — Create Folder API

**Files:**
- Create: `backend/api/folders.py`
- Modify: `backend/api/__init__.py`
- Delete: `backend/api/categories.py` (Tag routes move to folders.py or stay — see below)

- [ ] **Step 1: Create `backend/api/folders.py`**

```python
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
            # 检查同级目录下名称唯一
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

        # 检查是否有子文件夹
        child_count = Folder.query.filter_by(parent_id=folder_id).count()
        if child_count > 0:
            return jsonify({'code': 1, 'message': f'该文件夹下还有{child_count}个子文件夹，无法删除'}), 400

        # 检查是否有脚本
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
        new_parent_id = data.get('parent_id')  # None means move to root

        # 防止移动到自身
        if new_parent_id == folder_id:
            return jsonify({'code': 1, 'message': '不能将文件夹移动到自身'}), 400

        # 防止移动到自己的子孙文件夹（循环检测）
        if new_parent_id:
            current = Folder.query.get(new_parent_id)
            while current:
                if current.id == folder_id:
                    return jsonify({'code': 1, 'message': '不能将文件夹移动到其子文件夹中'}), 400
                current = current.parent

        # 检查目标目录下名称唯一
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
```

- [ ] **Step 2: Delete `backend/api/categories.py`**

Remove the file entirely — all Tag routes are now in folders.py.

- [ ] **Step 3: Update `backend/api/__init__.py`**

Change:
```python
from . import scripts, executions, schedules, files, environments, categories, workflows, workflow_templates, global_variables, ai_configs, ai_scripts, webhooks, webhook_trigger, backup, selection, upload
```
To:
```python
from . import scripts, executions, schedules, files, environments, folders, workflows, workflow_templates, global_variables, ai_configs, ai_scripts, webhooks, webhook_trigger, backup, selection, upload
```

- [ ] **Step 4: Commit**

```bash
git add backend/api/folders.py backend/api/__init__.py
git rm backend/api/categories.py
git commit -m "feat: add Folder API with tree/contents/move endpoints, migrate Tag routes"
```

---

## Task 5: Backend — Modify Scripts API

**Files:**
- Modify: `backend/api/scripts.py`

- [ ] **Step 1: Add move endpoint and update category_id references**

Add this new route at the end of `backend/api/scripts.py`:

```python
@api_bp.route('/scripts/<int:script_id>/move', methods=['POST'])
def move_script(script_id):
    """移动脚本到指定文件夹"""
    try:
        script = Script.query.get_or_404(script_id)
        data = request.get_json()
        folder_id = data.get('folder_id')  # None means move to root

        if folder_id is not None:
            from models import Folder
            folder = Folder.query.get(folder_id)
            if not folder:
                return jsonify({'code': 1, 'message': '目标文件夹不存在'}), 400

        script.folder_id = folder_id
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': script.to_dict(),
            'message': '脚本移动成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500
```

- [ ] **Step 2: Update get_scripts to use folder_id filter**

In the `get_scripts()` function, change:
```python
        category_id = request.args.get('category_id', type=int)
```
To:
```python
        folder_id = request.args.get('folder_id', type=str)  # string to detect "null" vs absent
```

And change the filter block:
```python
        # 按分类过滤
        if category_id:
            query = query.filter(Script.category_id == category_id)
```
To:
```python
        # 按文件夹过滤
        if folder_id is not None:
            if folder_id == 'null' or folder_id == '':
                query = query.filter(Script.folder_id.is_(None))
            else:
                query = query.filter(Script.folder_id == int(folder_id))
```

- [ ] **Step 3: Update create_script to use folder_id**

In the `create_script()` function, change:
```python
            category_id=data.get('category_id'),
```
To:
```python
            folder_id=data.get('folder_id'),
```

- [ ] **Step 4: Update update_script to use folder_id**

In the `update_script()` function, change:
```python
        if 'category_id' in data:
            script.category_id = data['category_id']
```
To:
```python
        if 'folder_id' in data:
            script.folder_id = data['folder_id']
```

- [ ] **Step 5: Update import — remove Category if imported**

In `backend/api/scripts.py`, the import line is:
```python
from models import db, Script, ScriptVersion, Tag
```
This does not import Category, so no change needed here.

- [ ] **Step 6: Commit**

```bash
git add backend/api/scripts.py
git commit -m "feat: add script move endpoint, change category_id to folder_id in scripts API"
```

---

## Task 6: Backend — Database Migration Script

**Files:**
- Create: `backend/migrate_categories_to_folders.py`

- [ ] **Step 1: Create migration script**

This script handles the SQLite migration from `categories` to `folders` table and updates the `scripts` table. It should be run once.

```python
"""
数据迁移脚本：将 categories 表迁移为 folders 表
运行方式: python backend/migrate_categories_to_folders.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'database.db')

def migrate():
    if not os.path.exists(DB_PATH):
        print("数据库文件不存在，跳过迁移")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 检查 categories 表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categories'")
        if not cursor.fetchone():
            print("categories 表不存在，跳过迁移")
            conn.close()
            return

        # 检查 folders 表是否已存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='folders'")
        if cursor.fetchone():
            print("folders 表已存在，跳过迁移")
            conn.close()
            return

        # 创建 folders 表
        cursor.execute('''
            CREATE TABLE folders (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                parent_id INTEGER REFERENCES folders(id),
                sort_order INTEGER DEFAULT 0,
                created_at DATETIME,
                updated_at DATETIME
            )
        ''')

        # 从 categories 迁移数据
        cursor.execute('SELECT id, name, sort_order, created_at, updated_at FROM categories')
        rows = cursor.fetchall()
        for row in rows:
            cursor.execute(
                'INSERT INTO folders (id, name, parent_id, sort_order, created_at, updated_at) VALUES (?, ?, NULL, ?, ?, ?)',
                (row[0], row[1], row[2], row[3], row[4])
            )
        print(f"迁移了 {len(rows)} 个分类到文件夹")

        # 检查 scripts 表是否有 category_id 列
        cursor.execute("PRAGMA table_info(scripts)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'category_id' in columns and 'folder_id' not in columns:
            # SQLite 不支持 RENAME COLUMN（旧版本），用重建表的方式
            # 但如果 SQLite >= 3.25.0，可以直接 ALTER TABLE RENAME COLUMN
            cursor.execute("ALTER TABLE scripts RENAME COLUMN category_id TO folder_id")
            print("已将 scripts.category_id 重命名为 folder_id")

        conn.commit()
        print("迁移完成！")

    except Exception as e:
        conn.rollback()
        print(f"迁移失败: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
```

- [ ] **Step 2: Commit**

```bash
git add backend/migrate_categories_to_folders.py
git commit -m "feat: add database migration script for categories to folders"
```

---

## Task 7: Frontend — Update API Client

**Files:**
- Modify: `frontend/src/api/index.js`

- [ ] **Step 1: Replace category APIs with folder APIs**

In `frontend/src/api/index.js`, replace the category section:

```javascript
// 分类管理
export const getCategories = () => request.get('/categories')
export const createCategory = (data) => request.post('/categories', data)
export const updateCategory = (id, data) => request.put(`/categories/${id}`, data)
export const deleteCategory = (id) => request.delete(`/categories/${id}`)
```

With:

```javascript
// 文件夹管理
export const getFolderTree = () => request.get('/folders/tree')
export const getFolderContents = (id) => request.get(`/folders/${id}/contents`)
export const getRootContents = () => request.get('/folders/root/contents')
export const createFolder = (data) => request.post('/folders', data)
export const updateFolder = (id, data) => request.put(`/folders/${id}`, data)
export const deleteFolder = (id) => request.delete(`/folders/${id}`)
export const moveFolder = (id, data) => request.post(`/folders/${id}/move`, data)
export const getFolderPath = (id) => request.get(`/folders/${id}/path`)
```

- [ ] **Step 2: Add script move API**

After the existing script APIs, add:

```javascript
export const moveScript = (id, data) => request.post(`/scripts/${id}/move`, data)
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/index.js
git commit -m "feat: replace category APIs with folder APIs, add moveScript"
```

---

## Task 8: Frontend — Rewrite Scripts.vue as File Manager

**Files:**
- Rewrite: `frontend/src/views/Scripts.vue`

This is the largest task. The new Scripts.vue will have:
- Left panel: folder tree (el-tree)
- Right panel: breadcrumb + grid of folders and scripts
- Right-click context menu
- Drag and drop
- Reused dialogs for edit/execute/view

- [ ] **Step 1: Write the new Scripts.vue template**

Replace the entire `<template>` section of `frontend/src/views/Scripts.vue` with:

```html
<template>
  <div class="file-manager">
    <!-- 左侧文件夹树 -->
    <div class="folder-tree-panel">
      <div class="tree-header">
        <span class="tree-title">文件夹</span>
      </div>
      <div class="tree-content">
        <div
          class="tree-item root-item"
          :class="{ active: currentFolderId === null && !searchMode }"
          @click="navigateToRoot"
          @dragover.prevent="handleTreeDragOver($event, null)"
          @dragleave="handleTreeDragLeave($event)"
          @drop.prevent="handleTreeDrop($event, null)"
        >
          <el-icon><FolderOpened /></el-icon>
          <span>全部脚本</span>
        </div>
        <el-tree
          ref="folderTreeRef"
          :data="folderTree"
          node-key="id"
          :props="{ label: 'name', children: 'children' }"
          :expand-on-click-node="false"
          :highlight-current="true"
          default-expand-all
          @node-click="handleTreeNodeClick"
          @node-contextmenu="handleTreeContextMenu"
        >
          <template #default="{ node, data }">
            <div
              class="tree-node-content"
              @dragover.prevent="handleTreeDragOver($event, data.id)"
              @dragleave="handleTreeDragLeave($event)"
              @drop.prevent="handleTreeDrop($event, data.id)"
            >
              <el-icon><Folder /></el-icon>
              <span class="tree-node-label">{{ data.name }}</span>
              <span v-if="data.script_count" class="tree-node-count">{{ data.script_count }}</span>
            </div>
          </template>
        </el-tree>
      </div>
      <div class="tree-footer">
        <el-button text @click="handleCreateRootFolder">
          <el-icon><Plus /></el-icon>
          新建文件夹
        </el-button>
      </div>
    </div>

    <!-- 右侧内容区 -->
    <div class="content-panel">
      <!-- 顶部工具栏 -->
      <div class="content-header">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item @click="navigateToRoot" class="breadcrumb-clickable">
            全部脚本
          </el-breadcrumb-item>
          <el-breadcrumb-item
            v-for="item in breadcrumbPath"
            :key="item.id"
            @click="navigateToFolder(item.id)"
            class="breadcrumb-clickable"
          >
            {{ item.name }}
          </el-breadcrumb-item>
        </el-breadcrumb>

        <div class="header-actions">
          <el-input
            v-model="searchText"
            placeholder="搜索脚本"
            style="width: 200px;"
            clearable
            @input="handleSearch"
            @clear="handleSearchClear"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button @click="handleCreateFolder">
            <el-icon><FolderAdd /></el-icon>
            新建文件夹
          </el-button>
          <el-button type="primary" @click="handleCreateScript">
            <el-icon><Plus /></el-icon>
            新建脚本
          </el-button>
        </div>
      </div>

      <!-- 内容网格 -->
      <div class="content-grid" v-if="!searchMode">
        <!-- 文件夹 -->
        <div
          v-for="folder in currentFolders"
          :key="'folder-' + folder.id"
          class="grid-item folder-item"
          @dblclick="navigateToFolder(folder.id)"
          @contextmenu.prevent="showFolderContextMenu($event, folder)"
          @dragover.prevent="handleGridFolderDragOver($event, folder.id)"
          @dragleave="handleGridFolderDragLeave($event)"
          @drop.prevent="handleGridFolderDrop($event, folder.id)"
        >
          <div class="item-icon folder-icon">
            <el-icon :size="40"><Folder /></el-icon>
          </div>
          <div class="item-name">{{ folder.name }}</div>
        </div>

        <!-- 脚本 -->
        <div
          v-for="script in currentScripts"
          :key="'script-' + script.id"
          class="grid-item script-item"
          draggable="true"
          @dragstart="handleDragStart($event, script)"
          @dragend="handleDragEnd"
          @contextmenu.prevent="showScriptContextMenu($event, script)"
        >
          <div class="item-icon script-icon" :class="script.type">
            <el-icon :size="40"><Document /></el-icon>
            <span class="type-badge">{{ script.type === 'python' ? '.py' : '.js' }}</span>
          </div>
          <div class="item-name">{{ script.name }}</div>
        </div>

        <!-- 空状态 -->
        <div v-if="currentFolders.length === 0 && currentScripts.length === 0" class="empty-state">
          <el-empty description="此文件夹为空">
            <div class="empty-actions">
              <el-button type="primary" @click="handleCreateScript">新建脚本</el-button>
              <el-button @click="handleCreateFolder">新建文件夹</el-button>
            </div>
          </el-empty>
        </div>
      </div>

      <!-- 搜索结果 -->
      <div class="content-grid" v-else>
        <div
          v-for="script in searchResults"
          :key="'search-' + script.id"
          class="grid-item script-item"
          @contextmenu.prevent="showScriptContextMenu($event, script)"
        >
          <div class="item-icon script-icon" :class="script.type">
            <el-icon :size="40"><Document /></el-icon>
            <span class="type-badge">{{ script.type === 'python' ? '.py' : '.js' }}</span>
          </div>
          <div class="item-name">{{ script.name }}</div>
          <div class="item-path" v-if="script.folder">{{ script.folder.name }}</div>
        </div>
        <div v-if="searchResults.length === 0" class="empty-state">
          <el-empty description="没有找到匹配的脚本" />
        </div>
      </div>
    </div>

    <!-- 右键菜单 -->
    <div
      v-if="contextMenu.visible"
      class="context-menu"
      :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
    >
      <!-- 脚本右键菜单 -->
      <template v-if="contextMenu.type === 'script'">
        <div class="context-menu-item" @click="handleExecute(contextMenu.target)">
          <el-icon><VideoPlay /></el-icon>
          <span>执行</span>
        </div>
        <div class="context-menu-item" @click="handleEdit(contextMenu.target)">
          <el-icon><Edit /></el-icon>
          <span>编辑</span>
        </div>
        <div class="context-menu-item" @click="handleView(contextMenu.target)">
          <el-icon><View /></el-icon>
          <span>查看</span>
        </div>
        <div class="context-menu-divider"></div>
        <div class="context-menu-item danger" @click="handleDeleteScript(contextMenu.target)">
          <el-icon><Delete /></el-icon>
          <span>删除</span>
        </div>
      </template>
      <!-- 文件夹右键菜单 -->
      <template v-if="contextMenu.type === 'folder'">
        <div class="context-menu-item" @click="handleCreateSubFolder(contextMenu.target)">
          <el-icon><FolderAdd /></el-icon>
          <span>新建子文件夹</span>
        </div>
        <div class="context-menu-item" @click="handleRenameFolder(contextMenu.target)">
          <el-icon><EditPen /></el-icon>
          <span>重命名</span>
        </div>
        <div class="context-menu-divider"></div>
        <div class="context-menu-item danger" @click="handleDeleteFolder(contextMenu.target)">
          <el-icon><Delete /></el-icon>
          <span>删除</span>
        </div>
      </template>
    </div>

    <!-- 创建/编辑脚本对话框 -->
    <el-dialog
      v-model="scriptDialogVisible"
      :title="scriptDialogTitle"
      width="80%"
      :close-on-click-modal="false"
      class="script-dialog"
    >
      <el-form :model="scriptForm" label-width="100px" class="script-form">
        <el-form-item label="脚本名称">
          <el-input v-model="scriptForm.name" placeholder="请输入脚本名称" />
        </el-form-item>
        <el-form-item label="脚本类型">
          <el-select v-model="scriptForm.type" placeholder="请选择脚本类型" @change="handleTypeChange">
            <el-option label="Python" value="python" />
            <el-option label="JavaScript" value="javascript" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="scriptForm.tag_ids"
            placeholder="选择标签（可选）"
            multiple
            clearable
            collapse-tags
            collapse-tags-tooltip
          >
            <el-option
              v-for="tag in tags"
              :key="tag.id"
              :label="tag.name"
              :value="tag.id"
            >
              <el-tag :color="tag.color" size="small" effect="plain">{{ tag.name }}</el-tag>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="收藏">
          <el-switch v-model="scriptForm.is_favorite" />
        </el-form-item>
        <el-form-item label="执行环境">
          <el-select v-model="scriptForm.environment_id" placeholder="默认环境（可选）" clearable>
            <el-option
              v-for="env in filteredEnvironments"
              :key="env.id"
              :label="`${env.name}${env.is_default ? ' (默认)' : ''}`"
              :value="env.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="scriptForm.description" type="textarea" rows="2" />
        </el-form-item>
        <el-form-item label="依赖配置">
          <el-input v-model="scriptForm.dependencies" type="textarea" rows="2" placeholder="多个依赖用逗号分隔" />
        </el-form-item>
        <el-form-item label="参数配置">
          <ParameterConfig v-model="scriptForm.parameters" />
        </el-form-item>
        <el-form-item label="脚本代码">
          <CodeEditor
            v-model="scriptForm.code"
            :language="scriptForm.type"
            height="400px"
            theme="dark"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scriptDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveScript">保存</el-button>
      </template>
    </el-dialog>

    <!-- 查看脚本对话框 -->
    <el-dialog
      v-model="viewDialogVisible"
      :title="`查看脚本: ${viewScript?.name || ''}`"
      width="80%"
    >
      <el-descriptions :column="2" border v-if="viewScript">
        <el-descriptions-item label="名称">{{ viewScript.name }}</el-descriptions-item>
        <el-descriptions-item label="类型">
          <el-tag :type="viewScript.type === 'python' ? 'success' : 'warning'">{{ viewScript.type }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="版本">v{{ viewScript.version }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatTime(viewScript.updated_at) }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ viewScript.description || '无' }}</el-descriptions-item>
      </el-descriptions>
      <div style="margin-top: 16px;">
        <CodeEditor
          v-if="viewScript"
          :model-value="viewScript.code"
          :language="viewScript.type"
          height="500px"
          theme="dark"
          :readonly="true"
        />
      </div>
      <template #footer>
        <el-button @click="viewDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleEdit(viewScript); viewDialogVisible = false">编辑</el-button>
        <el-button type="success" @click="handleExecute(viewScript); viewDialogVisible = false">执行</el-button>
      </template>
    </el-dialog>

    <!-- 执行对话框 -->
    <el-dialog v-model="executeVisible" title="执行脚本" width="700px">
      <el-form :model="executeForm" label-width="100px">
        <el-form-item label="脚本名称">
          <el-input :value="currentScript?.name" disabled />
        </el-form-item>
        <el-form-item label="脚本参数" v-if="currentScript?.parameters">
          <ExecutionParams
            :key="`exec-params-${currentScript.id}-${executeVisible}`"
            :parameters="currentScript.parameters"
            v-model="executeParamsObj"
          />
        </el-form-item>
        <el-form-item label="执行环境">
          <el-select v-model="executeForm.environment_id" placeholder="默认环境（可选）" clearable style="width: 100%;">
            <el-option
              v-for="env in executeEnvironments"
              :key="env.id"
              :label="`${env.name}${env.is_default ? ' (默认)' : ''}`"
              :value="env.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="上传文件">
          <FileUpload v-model="uploadFiles" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="executeVisible = false">取消</el-button>
        <el-button type="primary" @click="handleExecuteConfirm">执行</el-button>
      </template>
    </el-dialog>

    <!-- 实时日志对话框 -->
    <el-dialog
      v-model="logVisible"
      title="执行日志（实时）"
      width="80%"
      :close-on-click-modal="false"
      @close="closeLogStream"
    >
      <div class="log-header">
        <el-tag :type="getStatusType(logStatus)" size="large">{{ getStatusText(logStatus) }}</el-tag>
        <div class="log-actions">
          <el-button v-if="logStatus === 'running'" type="danger" size="small" @click="handleCancelExecution">中断执行</el-button>
          <el-button v-if="logStatus === 'running'" type="info" size="small" @click="closeLogStream">停止监听</el-button>
        </div>
      </div>
      <el-divider />
      <div class="progress-section">
        <ExecutionProgress :progress="logProgress" :stage="logStage" :status="logStatus" :show-detail="true" />
      </div>
      <el-divider />
      <div class="log-container" ref="logContainer">
        <pre v-if="realTimeLogs">{{ realTimeLogs }}</pre>
        <div v-else class="log-empty">等待日志输出...</div>
      </div>
      <div v-if="logError" class="error-container">
        <el-divider>错误信息</el-divider>
        <pre>{{ logError }}</pre>
      </div>
      <div v-if="logStatus === 'success' || logStatus === 'failed'" class="files-section">
        <el-divider>执行空间文件</el-divider>
        <div v-if="filesLoading" style="text-align: center; padding: 20px;">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span style="margin-left: 8px;">加载文件列表中...</span>
        </div>
        <div v-else-if="executionFiles.length === 0" class="files-empty">执行空间中没有文件</div>
        <el-table v-else :data="executionFiles" stripe max-height="300">
          <el-table-column prop="name" label="文件名" min-width="200" />
          <el-table-column prop="path" label="路径" min-width="200" show-overflow-tooltip />
          <el-table-column label="大小" width="120">
            <template #default="{ row }">{{ formatFileSize(row.size) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="handleFilePreview(row)" v-if="row.is_text">预览</el-button>
              <el-button size="small" type="primary" @click="handleFileDownload(row)">下载</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="closeLogStream">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 文件预览对话框 -->
    <el-dialog v-model="filePreviewVisible" :title="`预览: ${selectedFile?.name || ''}`" width="80%">
      <div class="file-preview-container">
        <pre v-if="filePreviewType === 'text'">{{ filePreviewContent }}</pre>
        <div v-else style="color: #909399; text-align: center; padding: 40px;">{{ filePreviewContent }}</div>
      </div>
      <template #footer>
        <el-button @click="filePreviewVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleFileDownload(selectedFile)">下载</el-button>
      </template>
    </el-dialog>
  </div>
</template>
```

- [ ] **Step 2: Write the new Scripts.vue script section**

Replace the entire `<script setup>` section:

```javascript
<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getScripts,
  createScript,
  updateScript,
  deleteScript,
  executeScriptWithFiles,
  getEnvironments,
  cancelExecution,
  getTags,
  getExecutionFiles,
  getExecutionFile,
  previewExecutionFile,
  getFolderTree,
  getFolderContents,
  getRootContents,
  createFolder,
  updateFolder,
  deleteFolder as deleteFolderApi,
  getFolderPath,
  moveScript
} from '../api'
import FileUpload from '../components/FileUpload.vue'
import CodeEditor from '../components/CodeEditor.vue'
import ParameterConfig from '../components/ParameterConfig.vue'
import ExecutionParams from '../components/ExecutionParams.vue'
import ExecutionProgress from '../components/ExecutionProgress.vue'
import {
  Plus, Search, Folder, FolderOpened, FolderAdd, Document, Edit, EditPen,
  Delete, VideoPlay, View, Loading
} from '@element-plus/icons-vue'

// ===== 文件夹树 =====
const folderTreeRef = ref(null)
const folderTree = ref([])
const currentFolderId = ref(null)
const breadcrumbPath = ref([])

// ===== 当前文件夹内容 =====
const currentFolders = ref([])
const currentScripts = ref([])

// ===== 搜索 =====
const searchText = ref('')
const searchMode = ref(false)
const searchResults = ref([])

// ===== 基础数据 =====
const environments = ref([])
const tags = ref([])

// ===== 右键菜单 =====
const contextMenu = ref({ visible: false, x: 0, y: 0, type: '', target: null })

// ===== 脚本编辑对话框 =====
const scriptDialogVisible = ref(false)
const scriptDialogTitle = ref('新建脚本')
const scriptForm = ref({
  name: '', type: 'python', description: '', code: '',
  dependencies: '', parameters: '', environment_id: null,
  folder_id: null, tag_ids: [], is_favorite: false
})
const editingScript = ref(null)

// ===== 查看对话框 =====
const viewDialogVisible = ref(false)
const viewScript = ref(null)

// ===== 执行对话框 =====
const currentScript = ref(null)
const executeVisible = ref(false)
const executeForm = ref({})
const executeParamsObj = ref({})
const uploadFiles = ref([])

// ===== 日志 =====
const logVisible = ref(false)
const realTimeLogs = ref('')
const logError = ref('')
const logStatus = ref('pending')
const logProgress = ref(0)
const logStage = ref('pending')
const currentExecutionId = ref(null)
const logContainer = ref(null)
let eventSource = null

// ===== 执行文件 =====
const executionFiles = ref([])
const filesLoading = ref(false)
const selectedFile = ref(null)
const filePreviewVisible = ref(false)
const filePreviewContent = ref('')
const filePreviewType = ref('text')

// ===== 拖拽 =====
let dragScript = null

// ===== 计算属性 =====
const filteredEnvironments = computed(() => {
  return environments.value.filter(env => env.type === scriptForm.value.type)
})

const executeEnvironments = computed(() => {
  if (!currentScript.value) return []
  return environments.value.filter(env => env.type === currentScript.value.type)
})

// ===== 数据加载 =====
const loadFolderTree = async () => {
  try {
    const res = await getFolderTree()
    folderTree.value = res.data
  } catch (error) {
    console.error('加载文件夹树失败:', error)
  }
}

const loadFolderContents = async (folderId) => {
  try {
    let res
    if (folderId === null) {
      res = await getRootContents()
    } else {
      res = await getFolderContents(folderId)
    }
    currentFolders.value = res.data.folders
    currentScripts.value = res.data.scripts
  } catch (error) {
    console.error('加载文件夹内容失败:', error)
  }
}

const loadBreadcrumb = async (folderId) => {
  if (folderId === null) {
    breadcrumbPath.value = []
    return
  }
  try {
    const res = await getFolderPath(folderId)
    breadcrumbPath.value = res.data
  } catch (error) {
    console.error('加载面包屑失败:', error)
  }
}

const loadEnvironments = async () => {
  try {
    const res = await getEnvironments()
    environments.value = res.data
  } catch (error) {
    console.error(error)
  }
}

const loadTags = async () => {
  try {
    const res = await getTags()
    tags.value = res.data
  } catch (error) {
    console.error(error)
  }
}

// ===== 导航 =====
const navigateToRoot = () => {
  currentFolderId.value = null
  searchMode.value = false
  searchText.value = ''
  loadFolderContents(null)
  loadBreadcrumb(null)
  if (folderTreeRef.value) {
    folderTreeRef.value.setCurrentKey(null)
  }
}

const navigateToFolder = (folderId) => {
  currentFolderId.value = folderId
  searchMode.value = false
  searchText.value = ''
  loadFolderContents(folderId)
  loadBreadcrumb(folderId)
  if (folderTreeRef.value) {
    folderTreeRef.value.setCurrentKey(folderId)
  }
}

const handleTreeNodeClick = (data) => {
  navigateToFolder(data.id)
}

// ===== 搜索 =====
let searchTimer = null
const handleSearch = () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    if (!searchText.value.trim()) {
      handleSearchClear()
      return
    }
    searchMode.value = true
    try {
      const res = await getScripts({ search: searchText.value })
      searchResults.value = res.data
    } catch (error) {
      console.error(error)
    }
  }, 300)
}

const handleSearchClear = () => {
  searchMode.value = false
  searchResults.value = []
  loadFolderContents(currentFolderId.value)
}

// ===== 右键菜单 =====
const showScriptContextMenu = (event, script) => {
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    type: 'script',
    target: script
  }
}

const showFolderContextMenu = (event, folder) => {
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    type: 'folder',
    target: folder
  }
}

const handleTreeContextMenu = (event, data) => {
  event.preventDefault()
  showFolderContextMenu(event, data)
}

const hideContextMenu = () => {
  contextMenu.value.visible = false
}

// ===== 文件夹操作 =====
const handleCreateRootFolder = () => {
  promptCreateFolder(null)
}

const handleCreateFolder = () => {
  promptCreateFolder(currentFolderId.value)
}

const handleCreateSubFolder = (folder) => {
  hideContextMenu()
  promptCreateFolder(folder.id)
}

const promptCreateFolder = async (parentId) => {
  try {
    const { value } = await ElMessageBox.prompt('请输入文件夹名称', '新建文件夹', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /\S+/,
      inputErrorMessage: '文件夹名称不能为空'
    })
    await createFolder({ name: value.trim(), parent_id: parentId })
    ElMessage.success('文件夹创建成功')
    loadFolderTree()
    loadFolderContents(currentFolderId.value)
  } catch (error) {
    if (error !== 'cancel' && error?.message !== 'cancel') {
      ElMessage.error('创建文件夹失败: ' + (error.message || error))
    }
  }
}

const handleRenameFolder = async (folder) => {
  hideContextMenu()
  try {
    const { value } = await ElMessageBox.prompt('请输入新名称', '重命名文件夹', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: folder.name,
      inputPattern: /\S+/,
      inputErrorMessage: '名称不能为空'
    })
    await updateFolder(folder.id, { name: value.trim() })
    ElMessage.success('重命名成功')
    loadFolderTree()
    loadFolderContents(currentFolderId.value)
  } catch (error) {
    if (error !== 'cancel' && error?.message !== 'cancel') {
      ElMessage.error('重命名失败: ' + (error.message || error))
    }
  }
}

const handleDeleteFolder = async (folder) => {
  hideContextMenu()
  try {
    await ElMessageBox.confirm(`确定要删除文件夹「${folder.name}」吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteFolderApi(folder.id)
    ElMessage.success('文件夹删除成功')
    loadFolderTree()
    if (currentFolderId.value === folder.id) {
      navigateToRoot()
    } else {
      loadFolderContents(currentFolderId.value)
    }
  } catch (error) {
    if (error !== 'cancel' && error?.message !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.message || error))
    }
  }
}

// ===== 脚本操作 =====
const handleCreateScript = () => {
  scriptDialogTitle.value = '新建脚本'
  scriptForm.value = {
    name: '', type: 'python', description: '', code: '',
    dependencies: '', parameters: '', environment_id: null,
    folder_id: currentFolderId.value, tag_ids: [], is_favorite: false
  }
  editingScript.value = null
  scriptDialogVisible.value = true
}

const handleEdit = (script) => {
  hideContextMenu()
  scriptDialogTitle.value = '编辑脚本'
  scriptForm.value = {
    ...script,
    tag_ids: script.tags ? script.tags.map(t => t.id) : []
  }
  editingScript.value = script
  scriptDialogVisible.value = true
}

const handleView = (script) => {
  hideContextMenu()
  viewScript.value = script
  viewDialogVisible.value = true
}

const handleSaveScript = async () => {
  try {
    if (editingScript.value) {
      await updateScript(editingScript.value.id, scriptForm.value)
      ElMessage.success('更新成功')
    } else {
      await createScript(scriptForm.value)
      ElMessage.success('创建成功')
    }
    scriptDialogVisible.value = false
    loadFolderContents(currentFolderId.value)
    loadFolderTree()
  } catch (error) {
    console.error(error)
    ElMessage.error('保存失败: ' + (error.message || error))
  }
}

const handleDeleteScript = async (script) => {
  hideContextMenu()
  try {
    await ElMessageBox.confirm(`确定要删除脚本「${script.name}」吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteScript(script.id)
    ElMessage.success('删除成功')
    loadFolderContents(currentFolderId.value)
    loadFolderTree()
  } catch (error) {
    if (error !== 'cancel') console.error(error)
  }
}

const handleTypeChange = () => {
  if (scriptForm.value.environment_id) {
    const selectedEnv = environments.value.find(env => env.id === scriptForm.value.environment_id)
    if (selectedEnv && selectedEnv.type !== scriptForm.value.type) {
      scriptForm.value.environment_id = null
    }
  }
}

// ===== 执行 =====
const handleExecute = (script) => {
  hideContextMenu()
  currentScript.value = script
  executeParamsObj.value = {}
  uploadFiles.value = []
  executeForm.value = { environment_id: null }
  executeVisible.value = true
}

const handleExecuteConfirm = async () => {
  try {
    const formData = new FormData()
    uploadFiles.value.forEach((file, index) => {
      formData.append(`file${index}`, file)
    })
    if (executeParamsObj.value && Object.keys(executeParamsObj.value).length > 0) {
      formData.append('params', JSON.stringify(executeParamsObj.value))
    }
    if (executeForm.value.environment_id) {
      formData.append('environment_id', executeForm.value.environment_id)
    }

    const res = await executeScriptWithFiles(currentScript.value.id, formData)
    const executionId = res.data.id
    ElMessage.success('脚本执行已启动')
    executeVisible.value = false
    openLogStream(executionId)
  } catch (error) {
    ElMessage.error('执行失败: ' + error.message)
    console.error(error)
  }
}

// ===== 日志流 =====
const openLogStream = (executionId) => {
  realTimeLogs.value = ''
  logError.value = ''
  logStatus.value = 'pending'
  logProgress.value = 0
  logStage.value = 'pending'
  currentExecutionId.value = executionId
  logVisible.value = true

  if (eventSource) eventSource.close()

  const apiUrl = import.meta.env.VITE_API_URL || '/api'
  eventSource = new EventSource(`${apiUrl}/executions/${executionId}/logs/stream`)

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'log') {
        realTimeLogs.value += data.content
        nextTick(() => {
          if (logContainer.value) logContainer.value.scrollTop = logContainer.value.scrollHeight
        })
      } else if (data.type === 'progress') {
        logProgress.value = data.progress || 0
        logStage.value = data.stage || 'pending'
        if (['running', 'preparing', 'installing_deps', 'finishing'].includes(data.stage)) {
          logStatus.value = 'running'
        }
      } else if (data.type === 'status') {
        logStatus.value = data.status
        logProgress.value = data.progress || 100
        logStage.value = data.stage || (data.status === 'success' ? 'completed' : 'failed')
        if (data.error) logError.value = data.error
        eventSource.close()
        eventSource = null
        loadExecutionFiles()
      }
    } catch (error) {
      console.error('解析日志数据失败:', error)
    }
  }

  eventSource.onerror = () => {
    ElMessage.error('日志流连接中断')
    if (eventSource) { eventSource.close(); eventSource = null }
  }
}

const loadExecutionFiles = async () => {
  if (!currentExecutionId.value) return
  filesLoading.value = true
  try {
    const res = await getExecutionFiles(currentExecutionId.value)
    executionFiles.value = res.data.files || []
  } catch (error) {
    console.error('加载执行文件失败:', error)
  } finally {
    filesLoading.value = false
  }
}

const closeLogStream = () => {
  if (eventSource) { eventSource.close(); eventSource = null }
  logVisible.value = false
  executionFiles.value = []
}

const handleCancelExecution = async () => {
  try {
    await ElMessageBox.confirm('确定要中断当前执行吗？', '提示', {
      confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
    })
    await cancelExecution(currentExecutionId.value)
    ElMessage.success('执行已中断')
    logStatus.value = 'failed'
    logStage.value = 'cancelled'
    logProgress.value = 100
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('中断执行失败: ' + (error.message || error))
  }
}

// ===== 文件操作 =====
const handleFilePreview = async (file) => {
  selectedFile.value = file
  if (file.is_text) {
    try {
      const res = await previewExecutionFile(currentExecutionId.value, file.path)
      filePreviewContent.value = res.data.content
      filePreviewType.value = res.data.type
      filePreviewVisible.value = true
    } catch (error) {
      ElMessage.error('预览文件失败: ' + error.message)
    }
  } else {
    handleFileDownload(file)
  }
}

const handleFileDownload = (file) => {
  const url = getExecutionFile(currentExecutionId.value, file.path, true)
  window.open(url, '_blank')
}

// ===== 拖拽 =====
const handleDragStart = (event, script) => {
  dragScript = script
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', script.id.toString())
}

const handleDragEnd = () => {
  dragScript = null
  // 移除所有高亮
  document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'))
}

const handleTreeDragOver = (event, folderId) => {
  if (!dragScript) return
  if (dragScript.folder_id === folderId) return
  event.currentTarget.classList.add('drag-over')
}

const handleTreeDragLeave = (event) => {
  event.currentTarget.classList.remove('drag-over')
}

const handleTreeDrop = async (event, folderId) => {
  event.currentTarget.classList.remove('drag-over')
  if (!dragScript) return
  if (dragScript.folder_id === folderId) return

  try {
    await moveScript(dragScript.id, { folder_id: folderId })
    ElMessage.success('脚本已移动')
    loadFolderContents(currentFolderId.value)
    loadFolderTree()
  } catch (error) {
    ElMessage.error('移动失败: ' + (error.message || error))
  }
  dragScript = null
}

const handleGridFolderDragOver = (event, folderId) => {
  if (!dragScript) return
  event.currentTarget.classList.add('drag-over')
}

const handleGridFolderDragLeave = (event) => {
  event.currentTarget.classList.remove('drag-over')
}

const handleGridFolderDrop = async (event, folderId) => {
  event.currentTarget.classList.remove('drag-over')
  if (!dragScript) return

  try {
    await moveScript(dragScript.id, { folder_id: folderId })
    ElMessage.success('脚本已移动')
    loadFolderContents(currentFolderId.value)
    loadFolderTree()
  } catch (error) {
    ElMessage.error('移动失败: ' + (error.message || error))
  }
  dragScript = null
}

// ===== 工具函数 =====
const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}

const formatFileSize = (size) => {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + ' KB'
  return (size / (1024 * 1024)).toFixed(2) + ' MB'
}

const getStatusType = (status) => {
  const types = { pending: 'info', running: '', success: 'success', failed: 'danger' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { pending: '等待中', running: '运行中', success: '执行成功', failed: '执行失败' }
  return texts[status] || '未知状态'
}

// ===== 生命周期 =====
onMounted(() => {
  loadFolderTree()
  loadFolderContents(null)
  loadEnvironments()
  loadTags()
  document.addEventListener('click', hideContextMenu)
})

onUnmounted(() => {
  document.removeEventListener('click', hideContextMenu)
  if (eventSource) { eventSource.close(); eventSource = null }
})
</script>
```

- [ ] **Step 3: Write the new Scripts.vue style section**

Replace the entire `<style>` section:

```css
<style scoped>
.file-manager {
  display: flex;
  height: calc(100vh - 60px);
  background: var(--el-bg-color);
}

/* ===== 左侧文件夹树 ===== */
.folder-tree-panel {
  width: 250px;
  min-width: 250px;
  border-right: 1px solid var(--el-border-color-lighter);
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color);
}

.tree-header {
  padding: 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.tree-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.tree-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.tree-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 4px;
  color: var(--el-text-color-regular);
  transition: all 0.2s;
}

.tree-item:hover {
  background: var(--el-fill-color-light);
}

.tree-item.active {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 500;
}

.tree-node-content {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  padding: 4px 0;
}

.tree-node-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-node-count {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  background: var(--el-fill-color);
  padding: 0 6px;
  border-radius: 10px;
}

.tree-footer {
  padding: 8px;
  border-top: 1px solid var(--el-border-color-lighter);
}

/* ===== 右侧内容区 ===== */
.content-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 20px;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.breadcrumb-clickable {
  cursor: pointer;
}

.breadcrumb-clickable:hover :deep(.el-breadcrumb__inner) {
  color: var(--el-color-primary);
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* ===== 内容网格 ===== */
.content-grid {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-wrap: wrap;
  align-content: flex-start;
  gap: 16px;
  padding: 4px;
}

.grid-item {
  width: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.grid-item:hover {
  background: var(--el-fill-color-light);
}

.grid-item.drag-over {
  background: var(--el-color-primary-light-8);
  outline: 2px dashed var(--el-color-primary);
}

.item-icon {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
  position: relative;
}

.folder-icon {
  color: #E6A23C;
}

.script-icon.python {
  color: #3776AB;
}

.script-icon.javascript {
  color: #F7DF1E;
}

.type-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  font-size: 10px;
  background: var(--el-bg-color);
  padding: 0 4px;
  border-radius: 3px;
  color: var(--el-text-color-secondary);
  border: 1px solid var(--el-border-color-lighter);
}

.item-name {
  font-size: 13px;
  text-align: center;
  word-break: break-all;
  line-height: 1.3;
  max-width: 100%;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  color: var(--el-text-color-primary);
}

.item-path {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-top: 2px;
}

.empty-state {
  width: 100%;
  padding: 60px 0;
}

.empty-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 12px;
}

/* ===== 右键菜单 ===== */
.context-menu {
  position: fixed;
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  padding: 6px 0;
  min-width: 160px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 3000;
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  color: var(--el-text-color-regular);
  transition: all 0.15s;
}

.context-menu-item:hover {
  background: var(--el-fill-color-light);
  color: var(--el-color-primary);
}

.context-menu-item.danger:hover {
  background: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
}

.context-menu-divider {
  height: 1px;
  background: var(--el-border-color-lighter);
  margin: 4px 0;
}

/* ===== 拖拽高亮 ===== */
.drag-over {
  background: var(--el-color-primary-light-8) !important;
  outline: 2px dashed var(--el-color-primary);
}

/* ===== 对话框样式 ===== */
.script-dialog :deep(.el-dialog__body) {
  max-height: 70vh;
  overflow-y: auto;
  padding: 20px;
}

.script-form {
  padding-right: 10px;
}

/* ===== 日志样式 ===== */
.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.log-actions {
  display: flex;
  gap: 8px;
}

.progress-section {
  margin-bottom: 16px;
}

.log-container {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 4px;
  max-height: 500px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.log-container pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.log-empty {
  color: #909399;
  text-align: center;
  padding: 40px;
  font-style: italic;
}

.error-container {
  margin-top: 16px;
}

.error-container pre {
  background-color: #fee;
  color: #c00;
  padding: 16px;
  border-radius: 4px;
  border-left: 4px solid #f56c6c;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  margin: 0;
}

.files-section {
  margin-top: 16px;
}

.files-empty {
  color: #909399;
  text-align: center;
  padding: 40px;
  font-style: italic;
}

.file-preview-container {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 4px;
  max-height: 600px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.file-preview-container pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/Scripts.vue
git commit -m "feat: rewrite Scripts.vue as file manager with folder tree, grid view, context menu, drag-and-drop"
```

---

## Task 9: Frontend — Update Router and Sidebar

**Files:**
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/layouts/components/sidebar/index.vue`

- [ ] **Step 1: Remove /categories route from router**

In `frontend/src/router/index.js`, remove this route object:

```javascript
  {
    path: '/categories',
    name: 'Categories',
    component: () => import('../views/Categories.vue')
  },
```

- [ ] **Step 2: Remove 分类管理 from sidebar menu**

In `frontend/src/layouts/components/sidebar/index.vue`, in the `menuItems` array, inside the `系统配置` children array, remove:

```javascript
      {
        path: '/categories',
        icon: 'Grid',
        title: '分类管理',
        color: '#409EFF'
      },
```

- [ ] **Step 3: Delete Categories.vue**

Delete `frontend/src/views/Categories.vue`.

- [ ] **Step 4: Commit**

```bash
git rm frontend/src/views/Categories.vue
git add frontend/src/router/index.js frontend/src/layouts/components/sidebar/index.vue
git commit -m "feat: remove Categories page and route, replaced by folder tree in Scripts"
```

---

## Task 10: Frontend — Update AIScriptWriter.vue

**Files:**
- Modify: `frontend/src/views/AIScriptWriter.vue`

- [ ] **Step 1: Replace category references with folder references**

In the template, change the 分类 form item (around line 178-187):

From:
```html
        <el-form-item label="分类" prop="category_id">
          <el-select v-model="saveForm.category_id" placeholder="请选择分类">
            <el-option
              v-for="category in categories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            />
          </el-select>
        </el-form-item>
```

To:
```html
        <el-form-item label="文件夹" prop="folder_id">
          <el-select v-model="saveForm.folder_id" placeholder="请选择文件夹" clearable>
            <el-option
              v-for="folder in folders"
              :key="folder.id"
              :label="folder.name"
              :value="folder.id"
            />
          </el-select>
        </el-form-item>
```

In the script section, change:
```javascript
const categories = ref([])
```
To:
```javascript
const folders = ref([])
```

Change the `loadCategories` function:
```javascript
const loadCategories = async () => {
  try {
    const response = await request.get('/categories')
    categories.value = response
```
To:
```javascript
const loadFolders = async () => {
  try {
    const response = await request.get('/folders/tree')
    // Flatten tree to list for select dropdown
    const flatList = []
    const flatten = (items, prefix = '') => {
      for (const item of items) {
        flatList.push({ id: item.id, name: prefix + item.name })
        if (item.children && item.children.length > 0) {
          flatten(item.children, prefix + item.name + ' / ')
        }
      }
    }
    flatten(response.data || response)
    folders.value = flatList
```

Update the `onMounted` call from `loadCategories()` to `loadFolders()`.

Update `saveForm` to use `folder_id` instead of `category_id` wherever the save form data is submitted.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/AIScriptWriter.vue
git commit -m "feat: update AIScriptWriter to use folders instead of categories"
```

---

## Task 11: Verify and Fix — Backend Startup

**Files:** All backend files

- [ ] **Step 1: Start the Flask backend and verify no import errors**

Run:
```bash
cd backend && python app.py
```

Expected: Server starts without import errors. Check for any remaining references to `Category` that would cause AttributeError.

- [ ] **Step 2: Fix any remaining `Category` references**

Search backend codebase for any remaining `Category` references:
```bash
grep -r "Category" backend/ --include="*.py"
```

Update any found references to use `Folder` instead.

- [ ] **Step 3: Commit fixes if any**

```bash
git add -A
git commit -m "fix: resolve remaining Category references in backend"
```

---

## Task 12: Verify and Fix — Frontend Build

**Files:** All frontend files

- [ ] **Step 1: Build the frontend**

Run:
```bash
cd frontend && npm run build
```

Expected: No TypeScript/compilation errors.

- [ ] **Step 2: Fix any remaining import or reference issues**

Search for remaining category references:
```bash
grep -r "category" frontend/src/ --include="*.vue" --include="*.js"
```

Fix any issues found (except for git-tracked files that haven't been modified).

- [ ] **Step 3: Commit fixes if any**

```bash
git add -A
git commit -m "fix: resolve remaining category references in frontend"
```

---

## Task 13: End-to-End Verification

- [ ] **Step 1: Run migration script (if existing database)**

```bash
python backend/migrate_categories_to_folders.py
```

- [ ] **Step 2: Start both servers**

```bash
# Terminal 1
cd backend && python app.py

# Terminal 2
cd frontend && npm run dev
```

- [ ] **Step 3: Manual verification checklist**

Open http://localhost:5173/scripts in a browser and verify:

1. Left panel shows folder tree
2. Right panel shows grid of folders and scripts
3. Can create a new folder (via button and right-click)
4. Can create a new script (appears in current folder)
5. Can right-click script → Execute → script runs
6. Can right-click script → Edit → edit dialog opens
7. Can right-click script → View → read-only view opens
8. Can drag a script to a folder in the tree → script moves
9. Can navigate via breadcrumb
10. Search works across all folders
11. Double-click folder navigates into it

- [ ] **Step 4: Final commit if needed**

```bash
git add -A
git commit -m "feat: complete file manager style script management"
```
