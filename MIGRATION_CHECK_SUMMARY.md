# 数据库迁移脚本检查结果总结

## 🚨 发现的严重问题

### 问题1: Script模型与数据库schema不一致 ⛔

**代码定义:**
```python
# backend/models/script.py:20
folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'))
```

**实际数据库:**
```sql
-- scripts表字段
category_id INTEGER  ← 使用category_id，不是folder_id
-- 缺少folder_id字段
```

**运行时错误:**
```
sqlite3.OperationalError: no such column: scripts.folder_id
```

### 问题2: 数据迁移脚本缺失 ⛔

Git历史显示:
- Commit 8c4e94e: "replace Category model with Folder model"
- Commit fcb3589: "add Folder API with tree/contents/move endpoints"

但**没有对应的数据库迁移脚本**:
- ❌ 无脚本创建folders表并迁移数据
- ❌ 无脚本添加scripts.folder_id字段
- ❌ 无脚本将category_id数据映射到folder_id

### 问题3: 数据不一致 ⚠️

**现状:**
```
folders表: 0条记录 (空表，但已创建)
categories表: 8条分类数据 (有数据，但未迁移)
scripts表: 1个脚本使用category_id=1 (关联数据存在)
```

**风险:**
- 前端文件管理器无法显示文件夹
- Script API无法正常工作
- 查询Script时会抛出异常

## 📋 检测到的迁移脚本列表

**现有的迁移脚本:**
```
backend/migrations/
├── add_categories_and_tags.py          ✓ 创建categories表
├── add_script_columns.py               ✓ 添加category_id字段
├── add_parameters_field.py             ✓ 添加parameters字段
├── add_environment_support.py          ✓ 创建environments表
├── add_execution_environment.py        ✓ 添加environment_id字段
├── add_execution_progress.py           ✓ 添加progress字段
├── add_workflow_tables.py              ✓ 创建workflow表
├── add_workflow_template_table.py      ✓ 创建template表
├── add_global_variables_table.py       ✓ 创建global_variables表
└── add_ai_config_table.py              ✓ 创建ai_configs表
```

**缺失的迁移脚本:**
```
backend/migrations/
├── migrate_categories_to_folders.py    ❌ 缺失 (已创建)
└── ...其他迁移脚本
```

## ✅ 已创建的修复方案

### 1. 问题诊断报告

**文件:** `DATABASE_MIGRATION_ISSUES.md`

包含:
- 详细的问题分析
- 影响范围评估
- 数据完整性检查
- 推荐的迁移步骤

### 2. 数据库迁移脚本

**文件:** `backend/migrations/migrate_categories_to_folders.py`

**功能:**
1. ✓ 自动备份数据库
2. ✓ 为scripts表添加folder_id字段
3. ✓ 将categories数据迁移到folders表
4. ✓ 建立category_id到folder_id的映射
5. ✓ 更新scripts的folder_id数据
6. ✓ 删除scripts.category_id字段
7. ✓ 验证迁移结果
8. ✓ 支持回滚操作

**使用方法:**
```bash
# 执行迁移
python backend/migrations/migrate_categories_to_folders.py migrate

# 从备份回滚
python backend/migrations/migrate_categories_to_folders.py rollback
```

### 3. 测试验证脚本

**文件:** `test_db_migration.py`

检测:
- folders表是否存在
- scripts表字段结构
- Script模型查询是否成功
- 数据完整性检查

## 🎯 建议的执行步骤

### 步骤1: 运行检测脚本
```bash
python test_db_migration.py
```
查看当前数据库状态和问题详情

### 步骤2: 执行迁移脚本
```bash
python backend/migrations/migrate_categories_to_folders.py migrate
```
脚本会自动:
- 备份数据库
- 执行所有迁移步骤
- 验证结果

### 步骤3: 再次验证
```bash
python test_db_migration.py
```
确认迁移成功

### 步骤4: 启动应用测试
```bash
python backend/app.py
```
访问 http://localhost:5000/api/folders/tree 验证API工作正常

### 步骤5: 清理备份 (可选)
确认功能正常后:
```bash
# 删除categories表 (可选)
sqlite3 data/database.db "DROP TABLE categories;"

# 删除备份文件 (可选)
rm data/database.db.backup_*
```

## 🔍 其他潜在问题检查

### ✅ 已检查的方面
- ✓ 外键约束正确性
- ✓ API路由一致性
- ✓ Model定义完整性
- ✓ 数据表创建顺序

### ⚠️ 需要注意的事项
- ⚠ database_schema.sql需要更新 (当前还是categories表定义)
- ⚠ 前端可能需要适配新的folder_id字段
- ⚠ 确保测试覆盖文件夹API

## 📊 迁移前后对比

### 迁移前
```
scripts表: category_id INTEGER → categories表
folders表: 空 (无数据)
categories表: 8条分类数据
Script查询: ✗ 失败 (no such column: scripts.folder_id)
```

### 迁移后
```
scripts表: folder_id INTEGER → folders表
folders表: 8条文件夹数据 (迁移自categories)
categories表: 保留作为备份
Script查询: ✓ 成功
```

## 💡 额外建议

### 1. 更新database_schema.sql
建议更新`database_schema.sql`文件，将categories表定义改为folders表

### 2. 添加迁移版本管理
考虑添加迁移版本号机制:
```python
# 在database中记录已执行的迁移
CREATE TABLE migration_history (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),
    executed_at DATETIME,
    success BOOLEAN
)
```

### 3. 测试覆盖率
为迁移脚本添加单元测试:
- 测试数据完整性
- 测试回滚功能
- 测试边界情况

## 📝 总结

**问题严重程度:** 🔴 高危

**状态:**
- ❌ 模型定义已更新但数据库未迁移
- ❌ 应用无法正常运行
- ✅ 迁移脚本已创建

**影响:**
- Script API无法使用
- 文件管理器功能无法使用
- 前端页面可能显示错误

**建议:** 立即执行迁移脚本修复数据库