# 数据库迁移指南

## 概述

本文档介绍如何将旧版本数据库的数据迁移到新版本数据库。

## 迁移工具

`migrate_database.py` - 自动化数据库迁移脚本

## 使用方法

### 1. 准备工作

在迁移之前，请确保：
- 已备份原数据库文件
- 停止正在运行的应用程序
- 确认老数据库文件路径

### 2. 备份当前数据库

```bash
cd backend
cp ../data/database.db ../data/database_backup_$(date +%Y%m%d_%H%M%S).db
```

### 3. 执行迁移

#### 方式一：使用默认路径

脚本会自动查找 `../data/database_backup.db`：

```bash
cd backend
python migrate_database.py
```

#### 方式二：指定老数据库路径

```bash
cd backend
python migrate_database.py /path/to/old/database.db
```

### 4. 验证迁移结果

迁移完成后，脚本会输出统计信息，显示迁移的各类数据数量。

启动应用程序并检查：
- 脚本列表是否完整
- 执行记录是否保留
- 工作流配置是否正确
- 定时任务是否正常

## 迁移流程

脚本会按照以下顺序迁移数据：

1. **基础数据**
   - 分类 (Categories)
   - 标签 (Tags)
   - 环境变量 (Environments)
   - 全局变量 (Global Variables)
   - AI配置 (AI Configs)

2. **脚本相关**
   - 脚本 (Scripts)
   - 脚本版本 (Script Versions)
   - 脚本-标签关联 (Script-Tag Relations)
   - 执行记录 (Executions)
   - 定时任务 (Schedules)

3. **工作流相关**
   - 工作流 (Workflows)
   - 工作流节点 (Workflow Nodes)
   - 工作流边 (Workflow Edges)
   - 工作流执行记录 (Workflow Executions)
   - 工作流节点执行记录 (Workflow Node Executions)
   - 工作流模板 (Workflow Templates)

## 安全保护

- 如果新数据库已存在，脚本会先创建备份
- 迁移前会要求用户确认
- 迁移失败时会自动回滚

## 常见问题

### Q: 迁移过程中断怎么办？

A: 脚本会在失败时自动回滚。如果迁移中断，可以从备份恢复原数据库，然后重新执行迁移。

### Q: 如何只迁移部分数据？

A: 编辑 `migrate_database.py`，注释掉不需要迁移的部分。

### Q: 老数据库缺少某些表怎么办？

A: 脚本会自动检测表是否存在，如果表不存在会跳过该部分迁移。

### Q: 新旧数据库字段不一致怎么办？

A: 脚本会检测表的列，对于不存在的列会使用默认值。

## 版本更新记录

### v1.0 (2025-12-21)
- 初始版本
- 支持所有核心表的迁移
- 自动检测表和列是否存在
- 支持数据备份和恢复

## 维护说明

**重要**: 当数据库模型发生变化时（添加新表、修改字段等），需要同步更新迁移脚本：

1. 在 `migrate_database.py` 中添加相应的迁移方法
2. 在 `run()` 方法中调用新的迁移方法
3. 更新本文档的版本记录
4. 测试迁移流程

### 添加新表迁移的步骤

以添加新表 `example_table` 为例：

```python
def migrate_example_table(self):
    """迁移示例表数据"""
    if not self.table_exists('example_table'):
        print("⚠️  example_table 表不存在，跳过")
        return

    print("开始迁移 example_table...")
    cursor = self.old_conn.cursor()
    cursor.execute("SELECT * FROM example_table")

    columns = self.get_columns('example_table')

    for row in cursor.fetchall():
        example = ExampleTable(
            id=row['id'],
            name=row['name'],
            # 添加其他字段...
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
        )
        db.session.add(example)
        self.stats['example_table'] += 1

    db.session.commit()
    print(f"✓ 迁移了 {self.stats['example_table']} 条记录")
```

然后在 `run()` 方法中适当位置调用：

```python
# 在 run() 方法中添加
self.migrate_example_table()
```

## 技术细节

### 数据库连接

- 老数据库: SQLite3 直接连接
- 新数据库: 通过 SQLAlchemy ORM

### 数据类型转换

- 时间字段: ISO格式字符串 → datetime 对象
- 布尔字段: 整数 → 布尔值
- JSON字段: 字符串保持不变

### 错误处理

- 表不存在: 跳过该表迁移
- 字段不存在: 使用默认值
- 数据错误: 回滚事务并报告错误
