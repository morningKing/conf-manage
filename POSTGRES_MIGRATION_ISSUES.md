# SQLite到PostgreSQL迁移脚本问题报告

## 🚨 发现的严重问题

### 问题1: 导入错误 - Category模型不存在 ⛔

**迁移脚本 (backend/migrate_to_postgres.py:32)**
```python
from models import (
    db, Script, ScriptVersion, Execution, Schedule, Environment,
    Category, Tag, script_tags, ...  # ← Category不再存在
)
```

**模型定义 (backend/models/__init__.py:12)**
```python
from .folder import Folder  # ← 已改用Folder，没有Category
from .category import Tag, script_tags  # ← 只导入Tag，没有Category类
```

**影响:**
- ❌ 导入时会报 `ImportError: cannot import name 'Category'`
- ❌ 迁移脚本根本无法运行

### 问题2: folders表缺失迁移 ⛔

**SQLite数据库实际表结构:**
```sql
sqlite_master tables:
- folders (存在，有数据)     ← 迁移脚本没有处理
- categories (存在，旧数据)   ← 迁移脚本尝试处理但模型不存在
- scripts (有folder_id字段)  ← 依赖folders表
```

**迁移脚本处理的表 (backend/migrate_to_postgres.py:342-363)**
```python
tables_order = [
    ('categories', Category, None),  # ← Category不存在，会失败
    ('tags', Tag, None),
    ('global_variables', GlobalVariable, None),
    ('environments', Environment, None),
    ('scripts', Script, None),  # ← folder_id会丢失外键关系
    ...
    # ← 缺失: ('folders', Folder, None)
]
```

**影响:**
- ❌ folders表不会被迁移到PostgreSQL
- ❌ Script的folder_id外键指向不存在的表
- ❌ 所有文件夹数据丢失

### 问题3: 验证列表缺失folders表 ⚠️

**验证列表 (backend/migrate_to_postgres.py:227-246)**
```python
tables_to_verify = [
    ('categories', 'categories'),  # ← 验证categories
    ('tags', 'tags'),
    ...
    # ← 缺失: ('folders', 'folders')
]
```

**影响:**
- ⚠️ folders表迁移不会被验证
- ⚠️ 即使迁移失败也不会报错

### 问题4: Schema不一致导致数据丢失 ⛔

**当前SQLite数据库状态:**
```
scripts表字段:
- folder_id (存在) → folders表
- category_id (仍存在) → categories表 (冗余字段)

folders表:
- 有数据 (0条或少量数据)

categories表:
- 有数据 (8条分类)
```

**迁移脚本期望的Schema:**
```
scripts表字段:
- category_id → categories表  # ← 脚本仍使用旧schema

folders表:
- 不存在  # ← 脚本未处理
```

**迁移后结果:**
```
PostgreSQL:
- categories表: 会尝试迁移 (失败，因为Category模型不存在)
- folders表: 不会被创建 ❌
- scripts表: folder_id字段会丢失外键关系 ❌
```

### 问题5: 外键约束破坏 ⛔

**Script模型 (backend/models/script.py:20)**
```python
folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'))
```

**迁移后PostgreSQL状态:**
```
- folders表不存在 ❌
- scripts.folder_id指向不存在的表
- 外键约束失败
```

## 🔍 详细检查结果

### SQLite数据库实际表列表
```
ai_configs
categories         ← 存在
environments
executions
folders            ← 存在，但迁移脚本不处理 ⚠️
global_variables
schedules
script_tags
script_versions
scripts
selection_sessions
tags
webhook_logs
webhooks
workflow_edges
workflow_executions
workflow_node_executions
workflow_nodes
workflow_templates
workflows
```

### 模型导入关系

**models/__init__.py 导入:**
```python
from .folder import Folder     ← 有Folder模型
from .category import Tag      ← 只有Tag，无Category ⚠️
```

**migrate_to_postgres.py 导入:**
```python
from models import Category    ← 导入不存在的东西 ❌
```

**结果:** ImportError

## 📊 问题严重程度评估

| 问题 | 严重程度 | 影响 | 是否阻止迁移 |
|------|----------|------|-------------|
| Category导入错误 | 🔴 Critical | 脚本无法运行 | ✅ 是 |
| folders表缺失 | 🔴 Critical | 数据丢失 | ✅ 是 |
| 验证缺失 | 🟡 Medium | 无法检测错误 | ⚠️ 部分 |
| 外键破坏 | 🔴 Critical | 数据完整性失效 | ✅ 是 |

## 🎯 需要的修复方案

### 修复1: 更新导入语句
```python
# backend/migrate_to_postgres.py
from models import (
    db, Script, ScriptVersion, Execution, Schedule, Environment,
    Folder, Tag, script_tags, ...  # ← 改用Folder
)
```

### 修复2: 添加folders表迁移
```python
tables_order = [
    ('folders', Folder, None),  # ← 添加folders迁移
    ('tags', Tag, None),
    ('global_variables', GlobalVariable, None),
    ('environments', Environment, None),
    ('scripts', Script, None),
    ...
]
```

### 修复3: 添加folders表验证
```python
tables_to_verify = [
    ('folders', 'folders'),  # ← 添加验证
    ('tags', 'tags'),
    ...
]
```

### 修复4: 处理categories到folders的数据迁移

**选项A: 如果SQLite中categories有数据但folders无数据**
```python
# 1. 先迁移categories数据到folders
# 2. 建立映射关系
# 3. 更新scripts.category_id到scripts.folder_id
# 4. 跳过categories表迁移（或作为备份表迁移）
```

**选项B: 如果folders已有数据**
```python
# 1. 直接迁移folders表
# 2. 迁移scripts时使用folder_id
# 3. 可选：保留categories表作为历史数据
```

### 修复5: 处理Script的category_id字段

**检查SQLite数据库中的实际字段:**
```python
# 需要先检查scripts表是否还有category_id字段
# 如果有，需要迁移数据到folder_id
```

## 🔧 修复后的迁移顺序

```python
tables_order = [
    # 1. 基础数据表
    ('folders', Folder, None),  # ← 替换categories
    ('tags', Tag, None),
    ('global_variables', GlobalVariable, None),
    ('environments', Environment, None),

    # 2. 脚本相关（依赖folders）
    ('scripts', Script, None),
    ('script_versions', ScriptVersion, None),
    ('script_tags', None, None),  # 关联表

    # 3. 执行相关
    ('executions', Execution, ['params']),
    ('schedules', Schedule, ['params']),

    # 4. 工作流相关
    ('workflows', Workflow, ['config']),
    ('workflow_nodes', WorkflowNode, ['config']),
    ('workflow_edges', WorkflowEdge, ['condition']),
    ('workflow_executions', WorkflowExecution, ['params']),
    ('workflow_node_executions', WorkflowNodeExecution, ['output']),
    ('workflow_templates', WorkflowTemplate, ['template_config']),

    # 5. 其他配置
    ('webhooks', Webhook, None),
    ('webhook_logs', WebhookLog, None),
    ('ai_configs', AIConfig, None),

    # 6. 可选：保留categories作为备份（创建临时模型）
    # ('categories', None, None),  # 如果需要保留
]
```

## 💡 建议的修复步骤

### 步骤1: 立即修复导入错误
```bash
# 编辑 migrate_to_postgres.py
# 将 Category 改为 Folder
```

### 步骤2: 添加folders表处理
```bash
# 在 tables_order 中添加 folders
# 在验证列表中添加 folders
```

### 步骤3: 检查实际SQLite数据
```bash
sqlite3 data/database.db "SELECT COUNT(*) FROM folders;"
sqlite3 data/database.db "SELECT COUNT(*) FROM categories;"
sqlite3 data/database.db "PRAGMA table_info(scripts);"
```

### 步骤4: 根据数据状态选择迁移策略

**如果folders为空，categories有数据:**
1. 创建临时迁移函数将categories→folders
2. 映射category_id→folder_id
3. 迁移数据

**如果folders已有数据:**
1. 直接迁移folders表
2. 迁移scripts时使用folder_id

### 步骤5: 测试迁移脚本
```bash
# 先在测试环境运行
python backend/migrate_to_postgres.py --skip-verify
# 检查PostgreSQL数据完整性
```

## 📝 总结

**当前状态:**
- ❌ 迁移脚本**无法运行**（ImportError）
- ❌ 迁移脚本**设计过时**（基于旧schema）
- ❌ 迁移后会**丢失folders数据**
- ❌ 外键约束会**完全失效**

**修复优先级:**
1. 🔴 立即修复导入错误（阻止运行）
2. 🔴 添加folders表迁移（阻止数据完整性）
3. 🟡 更新验证列表（检测错误）
4. 🟢 处理category_id→folder_id迁移（可选，取决于数据状态）

**建议:**
迁移脚本需要**完全重写或大幅修改**才能正确处理当前的schema。建议：
1. 先修复SQLite内部的category→folder迁移
2. 然后更新PostgreSQL迁移脚本
3. 最后测试完整迁移流程