# 数据库迁移快速参考

## 一键迁移（推荐）

```bash
cd backend
./quick_migrate.sh
```

## 手动迁移

### 1. 备份当前数据库
```bash
cd backend
cp ../data/database.db ../data/database_backup_$(date +%Y%m%d_%H%M%S).db
```

### 2. 执行迁移
```bash
python migrate_database.py /path/to/old_database.db
```

### 3. 查看迁移结果
```bash
python view_database.py
```

## 常用命令

### 查看当前数据库
```bash
python view_database.py
```

### 查看指定数据库
```bash
python view_database.py /path/to/database.db
```

### 比较两个数据库
```bash
python view_database.py ../data/database.db > new_db.txt
python view_database.py ../data/database_backup.db > old_db.txt
diff new_db.txt old_db.txt
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `migrate_database.py` | 主迁移脚本 |
| `quick_migrate.sh` | 一键迁移工具（自动备份） |
| `view_database.py` | 数据库查看工具 |
| `DATABASE_MIGRATION.md` | 详细迁移文档 |

## 迁移顺序

迁移按以下依赖顺序自动执行：

```
基础数据
├── Categories（分类）
├── Tags（标签）
├── Environments（环境变量）
├── Global Variables（全局变量）
└── AI Configs（AI配置）

脚本数据
├── Scripts（脚本）
├── Script Versions（脚本版本）
├── Script Tags（脚本标签关联）
├── Executions（执行记录）
└── Schedules（定时任务）

工作流数据
├── Workflows（工作流）
├── Workflow Nodes（工作流节点）
├── Workflow Edges（工作流边）
├── Workflow Executions（工作流执行）
├── Workflow Node Executions（节点执行）
└── Workflow Templates（工作流模板）
```

## 新增表迁移模板

当数据库新增表时，在 `migrate_database.py` 中添加：

```python
def migrate_new_table(self):
    """迁移新表数据"""
    if not self.table_exists('new_table'):
        print("⚠️  new_table 表不存在，跳过")
        return

    print("开始迁移 new_table...")
    cursor = self.old_conn.cursor()
    cursor.execute("SELECT * FROM new_table")

    columns = self.get_columns('new_table')

    for row in cursor.fetchall():
        item = NewTable(
            id=row['id'],
            name=row['name'],
            # 检查列是否存在，提供默认值
            field=row['field'] if 'field' in columns else None,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
        )
        db.session.add(item)
        self.stats['new_table'] += 1

    db.session.commit()
    print(f"✓ 迁移了 {self.stats['new_table']} 条记录")
```

然后在 `run()` 方法中调用：
```python
self.migrate_new_table()
```

## 故障排除

### 问题：迁移失败
**解决**：检查错误信息，从备份恢复后重试

### 问题：数据不完整
**解决**：使用 `view_database.py` 比较新老数据库

### 问题：表结构不匹配
**解决**：脚本会自动处理缺失字段，使用默认值

## 安全提示

✅ **推荐做法**
- 迁移前备份数据库
- 在测试环境先验证
- 迁移后验证数据完整性

❌ **避免操作**
- 不备份直接迁移
- 在生产环境直接测试
- 跳过数据验证步骤
