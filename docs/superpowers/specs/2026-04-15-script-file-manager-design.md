# Script File Manager Design

## Overview

将脚本管理页面从表格列表改为文件管理器风格，支持多级文件夹、右键菜单、拖拽移动。文件夹完全替代现有的分类（Category）功能。

## Data Model Changes

### Folder Model (替代 Category)

将现有 `categories` 表改造为 `folders` 表：

```python
class Folder(db.Model):
    __tablename__ = 'folders'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey('folders.id'), nullable=True)  # None = root
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    parent = relationship('Folder', remote_side=[id], backref='children')
```

- `parent_id = None` 表示根级文件夹
- 同一父文件夹下名称唯一
- 移除 Category 的 `color`, `icon`, `description` 字段

### Script Model Changes

- `category_id` 字段改为 `folder_id`，外键指向 `folders.id`
- `folder_id = None` 表示脚本位于根目录
- 移除 `category` relationship，替换为 `folder` relationship
- `to_dict()` 返回 `folder_id` 和 `folder` 信息（替代 `category_id` 和 `category`）

### Database Migration

由于项目使用 SQLAlchemy 直接建表（无 migration 系统），通过 ALTER TABLE 实现：
1. 重命名 `categories` 表为 `folders`
2. 添加 `parent_id` 列
3. 移除 `color`, `icon`, `description` 列
4. 将 Script 表的 `category_id` 外键更新指向 `folders`

实际操作：由于 SQLite 限制 ALTER TABLE，直接修改模型定义，在 app 启动时 `create_all()` 会处理新表。对现有数据，手动写迁移脚本转移数据。

## Backend API

### Folder API (`/api/folders`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/folders/tree` | 获取完整文件夹树（含每个文件夹下的脚本数量） |
| GET | `/api/folders/<id>/contents` | 获取文件夹内容（子文件夹 + 脚本） |
| POST | `/api/folders` | 创建文件夹（参数：name, parent_id） |
| PUT | `/api/folders/<id>` | 更新文件夹（重命名） |
| DELETE | `/api/folders/<id>` | 删除文件夹（如果下面有内容则拒绝，或提示递归删除） |
| POST | `/api/folders/<id>/move` | 移动文件夹到新的父文件夹 |

### Script API Changes

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/scripts/<id>/move` | 移动脚本到指定文件夹 |
| GET | `/api/scripts` | 新增 `folder_id` 过滤参数，`folder_id=null` 获取根目录脚本，`folder_id=0` 获取全部脚本 |

现有的创建/编辑脚本 API 中的 `category_id` 参数改为 `folder_id`。

### 删除 Category API

移除 `/api/categories` 相关的所有路由，由 `/api/folders` 替代。

## Frontend Design

### Page Layout

左右分栏布局：

```
+---------------------------+------------------------------------------+
|   文件夹树 (250px)         |          当前文件夹内容                    |
|                           |                                          |
|  > 全部脚本               |  面包屑: 全部 > 运维 > 数据库              |
|  v 运维脚本               |                                          |
|    v 数据库               |  [新建脚本] [新建文件夹] [搜索]            |
|      备份                 |                                          |
|    > 服务器               |  +--------+  +--------+  +--------+      |
|  v 数据处理               |  | folder |  | .py    |  | .js    |      |
|    日志分析               |  | 监控   |  | 备份   |  | 清理   |      |
|  > 定时任务               |  +--------+  +--------+  +--------+      |
|                           |                                          |
|  [+ 新建文件夹]           |                                          |
+---------------------------+------------------------------------------+
```

### Left Panel - Folder Tree

- 使用 `el-tree` 组件展示文件夹层级
- 顶部固定一个「全部脚本」节点，点击时右侧显示所有脚本
- 点击文件夹节点 → 右侧切换到该文件夹内容
- 文件夹节点右键菜单：新建子文件夹、重命名、删除
- 底部「+ 新建文件夹」按钮在根级创建文件夹
- 作为拖拽目标，接受从右侧拖入的脚本

### Right Panel - Content Area

**Header：**
- 面包屑导航，显示当前路径层级，每级可点击跳转
- 操作按钮：新建脚本、新建文件夹、搜索

**Content Grid：**
- 网格形式展示，文件夹排在脚本前面
- 每个条目显示：图标（文件夹/Python/JavaScript）+ 名称 + 类型标识
- 双击文件夹进入该文件夹
- 脚本可拖拽（draggable），拖拽到左侧树或右侧文件夹图标上

**脚本右键菜单：**
- 执行：弹出执行对话框（复用现有的执行弹窗）
- 编辑：弹出编辑对话框（复用现有的编辑弹窗）
- 查看：弹出只读查看对话框（CodeEditor readonly=true）
- 移动到：弹出文件夹选择器
- 删除

**文件夹右键菜单（右侧网格中的文件夹）：**
- 新建子文件夹
- 重命名
- 删除

### Dialogs (Reuse Existing)

- **编辑对话框**：复用 Scripts.vue 中已有的创建/编辑表单，`category_id` 下拉改为 `folder_id`（当前文件夹自动填充）
- **执行对话框**：复用 Scripts.vue 中已有的执行表单
- **查看对话框**：新建一个只读查看对话框，展示脚本名称、类型、描述、代码（readonly CodeEditor）
- **日志对话框**：复用现有的实时日志对话框

### Drag & Drop

- 脚本条目设置 `draggable=true`
- 左侧 el-tree 节点和右侧文件夹图标作为 drop target
- 拖拽完成后调用 `POST /api/scripts/<id>/move` 移动脚本
- 拖拽中高亮目标文件夹

### Search

保留搜索功能，搜索时显示全局结果（跨文件夹），结果中显示脚本所在路径。

## Files to Modify

### Backend
1. `backend/models/category.py` → 重写为 `backend/models/folder.py`（Folder 模型）
2. `backend/models/script.py` → 修改 category_id 为 folder_id
3. `backend/models/__init__.py` → 更新导入
4. `backend/api/categories.py` → 重写为 `backend/api/folders.py`（Folder API）
5. `backend/api/scripts.py` → 添加 move 端点，修改过滤逻辑
6. `backend/api/__init__.py` → 更新导入

### Frontend
7. `frontend/src/views/Scripts.vue` → 完全重写为文件管理器页面
8. `frontend/src/api/index.js` → 替换 category API 为 folder API，添加 move API
9. `frontend/src/views/Categories.vue` → 删除（被文件夹替代）

### Additional Files Affected
10. `frontend/src/router/index.js` → 移除 `/categories` 路由
11. `frontend/src/App.vue` → 移除分类管理菜单项（如果仍在使用旧 App.vue）
12. `frontend/src/layouts/components/sidebar/index.vue` → 移除分类管理侧边栏入口
13. `frontend/src/views/AIScriptWriter.vue` → 将 categories API 调用改为 folders
14. `frontend/src/views/Workflows.vue` → 该文件从脚本数据中提取分类信息，改造后会自然跟随 Script.to_dict() 的变化

## Out of Scope

- 文件夹的拖拽排序（仅支持脚本拖拽到文件夹）
- 文件夹之间的拖拽移动（可通过右键菜单实现）
- 多选批量移动脚本
- 文件夹颜色/图标自定义
