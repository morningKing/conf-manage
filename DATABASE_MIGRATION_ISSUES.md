# 数据库迁移问题诊断报告

## 问题概述

根据git commit历史 (ee20fd8: "feat: 完成文件管理器式脚本页面...") 和 (8c4e94e: "feat: replace Category model with Folder model, update Script model")，代码已从Category模型迁移到Folder模型，但**数据库迁移脚本缺失**，导致模型定义与数据库schema不一致。

## 详细问题清单

### 1. Script模型与数据库不一致 ✗

**模型定义 (backend/models/script.py:20)**
```python
folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)
```

**实际数据库结构**
```
scripts表字段: id, name, description, type, code, dependencies, parameters,
               environment_id, version, created_at, updated_at,
               category_id, is_favorite  ← 缺少folder_id字段
```

**运行时错误**
```
sqlite3.OperationalError: no such column: scripts.folder_id
```

### 2. folders表创建但无数据 ✗

**folders表结构** (正确)
```sql
id INTEGER PRIMARY KEY
name VARCHAR(100) NOT NULL
parent_id INTEGER (自引用外键)
color VARCHAR(20)
sort_order INTEGER
created_at/updated_at DATETIME
```

**数据状态**
```
folders表: 0条记录 (空表)
categories表: 8条分类数据
```

**影响**
- categories数据未迁移到folders
- 前端文件管理器UI无法显示文件夹

### 3. 缺少迁移脚本 ✗

**现有迁移脚本目录**
```
backend/migrations/
├── add_categories_and_tags.py    ← 创建categories表
├── add_script_columns.py         ← 添加category_id字段
├── add_environment_support.py
├── add_execution_environment.py
├── add_workflow_tables.py
├── add_workflow_template_table.py
├── add_global_variables_table.py
└── add_ai_config_table.py
```

**缺失的迁移**
- ✗ 无 "convert_categories_to_folders.py"
- ✗ 无 "add_script_folder_id.py"

### 4. 数据完整性问题 ⚠

**categories表数据**
```
id=1: 数据处理 (#409EFF)
id=2: API调用 (#67C23A)
id=3: 文件操作 (#E6A23C)
id=4: 数据库操作 (#F56C6C)
id=5: 自动化任务 (#909399)
id=6: 监控告警 (#C71585)
id=7: 网络爬虫 (#FF69B4)
id=8: 其他 (#95A5A6)
```

**scripts表使用category_id的数据**
```
Script ID 4: "创建文件" 使用 category_id=1 (数据处理)
```

**风险**
- 如果直接删除categories表，会丢失数据关系
- Script无法关联到正确的folder

### 5. API路由已更新 ✓

**folders.py API** (backend/api/folders.py)
- `/api/folders/tree` - 获取文件夹树
- `/api/folders/<id>/contents` - 获取文件夹内容
- `/api/folders` - CRUD操作
- `/api/folders/<id>/move` - 移动文件夹

**scripts.py API** (backend/api/scripts.py)
- 使用 `Script.folder_id` 字段
- 查询参数: `folder_id`
- 创建/更新脚本时设置 `folder_id`

**状态**: API已正确实现，但因数据库问题无法运行

## 影响范围

### 运行时错误
1. **Script查询失败** - 访问 `script.folder` 关系时报错
2. **文件夹API失败** - `/api/folders/*` 返回空数据或错误
3. **前端文件管理器** - 无法显示文件夹树和脚本列表

### 数据完整性风险
1. **数据丢失** - categories数据可能被删除
2. **脚本分类丢失** - 现有脚本的分类关系丢失
3. **外键约束失效** - category_id指向不存在的表

## 需要的迁移步骤

### 步骤1: 添加folder_id字段
```sql
ALTER TABLE scripts ADD COLUMN folder_id INTEGER REFERENCES folders(id);
```

### 步骤2: 将categories数据迁移到folders
```sql
INSERT INTO folders (name, parent_id, color, sort_order, created_at, updated_at)
SELECT name, NULL, color, sort_order, created_at, updated_at
FROM categories;
```

### 步骤3: 迁移脚本数据关系
```sql
-- 建立category_id到folder_id的映射
UPDATE scripts
SET folder_id = (
    SELECT f.id FROM folders f
    JOIN categories c ON c.name = f.name AND c.color = f.color
    WHERE c.id = scripts.category_id
)
WHERE category_id IS NOT NULL;
```

### 步骤4: 清理category_id字段
```sql
-- SQLite不支持直接删除列，需要重建表
-- 详见迁移脚本
```

### 步骤5: (可选) 保留categories表
```sql
-- 建议: 暂时保留categories表作为备份
-- 后续确认无问题后可删除
```

## 建议方案

### 方案A: 创建完整迁移脚本
- 编写 `migrate_categories_to_folders.py`
- 包含数据迁移、字段更新、回滚功能
- 测试迁移脚本
- 执行迁移

### 方案B: 重建数据库 (风险高)
- 仅适用于开发环境
- 删除database.db
- 使用db.create_all()重建
- 手动导入数据

### 方案C: 手动SQL迁移 (不推荐)
- 直接在SQLite中执行SQL
- 无回滚能力
- 容易出错

## 推荐执行顺序

1. **备份数据库** ✓ (必须)
2. **创建迁移脚本** ✓ (推荐)
3. **测试迁移** ✓ (在测试数据库上)
4. **执行迁移** ✓ (在生产数据库上)
5. **验证结果** ✓ (运行test_db_migration.py)
6. **更新schema.sql** ✓ (更新文档)

## 附录: 测试验证结果

运行 `test_db_migration.py` 的输出：
```
[OK] folders 表存在
[ERROR] 有category_id字段，但没有folder_id字段
[OK] folders查询成功，找到 0 个文件夹
[ERROR] Script查询失败: OperationalError - no such column: scripts.folder_id
[WARN] 发现 1 个脚本使用category_id
```