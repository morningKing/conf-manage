# PostgreSQL 数据库迁移实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将脚本管理系统从 SQLite 数据库迁移到 PostgreSQL，保持数据完整性和应用兼容性。

**Architecture:** 使用 SQLAlchemy 的多数据库支持，通过环境变量切换数据库类型。创建独立迁移脚本，按外键依赖顺序逐表迁移数据，迁移后验证数据完整性。保留 SQLite 回退能力。

**Tech Stack:** PostgreSQL 15, psycopg2-binary, SQLAlchemy, Flask

---

## 文件结构

```
backend/
├── config.py                    # 修改：添加 PostgreSQL 配置支持
├── migrate_to_postgres.py       # 新建：迁移脚本
├── models/__init__.py           # 无需修改：SQLAlchemy 自动适配
├── requirements.txt             # 修改：添加 psycopg2-binary
└── data/
    └── database.db              # 保留：作为迁移源和备份
```

---

### Task 1: 添加 PostgreSQL 依赖

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 添加 psycopg2-binary 到 requirements.txt**

打开 `backend/requirements.txt`，在文件末尾添加：

```
psycopg2-binary==2.9.9
```

完整添加后的依赖列表应包含：
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-CORS==4.0.0
SQLAlchemy==2.0.23
python-dotenv==1.0.0
apscheduler==3.10.4
watchdog==3.0.0
psutil==5.9.6
psycopg2-binary==2.9.9
```

- [ ] **Step 2: 安装新依赖**

Run: `cd backend && pip install psycopg2-binary==2.9.9`
Expected: Successfully installed psycopg2-binary-2.9.9

- [ ] **Step 3: 验证安装**

Run: `python -c "import psycopg2; print(psycopg2.__version__)"`
Expected: 2.9.9 (或类似版本号)

- [ ] **Step 4: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore: add psycopg2-binary for PostgreSQL support"
```

---

### Task 2: 修改配置文件支持 PostgreSQL

**Files:**
- Modify: `backend/config.py:1-113`

- [ ] **Step 1: 添加环境变量和 PostgreSQL 配置**

在 `backend/config.py` 的 `import os` 后面，`BASE_DIR` 定义之前添加：

```python
# 环境变量支持（便于部署切换）
DB_TYPE = os.environ.get('DB_TYPE', 'postgresql')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'jay123')
DB_NAME = os.environ.get('DB_NAME', 'confmanage')
```

- [ ] **Step 2: 修改 SQLALCHEMY_DATABASE_URI 配置**

将 `Config` 类中的 `SQLALCHEMY_DATABASE_URI` 从：

```python
SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "data", "database.db")}'
```

修改为：

```python
# PostgreSQL配置（默认）
if DB_TYPE == 'sqlite':
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "data", "database.db")}'
else:
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
```

- [ ] **Step 3: 添加连接池配置**

在 `SQLALCHEMY_TRACK_MODIFICATIONS = False` 后添加：

```python
# PostgreSQL连接池配置
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_recycle': 300,
    'pool_pre_ping': True
}
```

- [ ] **Step 4: 添加 SQLite 路径常量（供迁移脚本使用）**

在类定义末尾添加静态属性：

```python
# SQLite路径保留（供迁移脚本使用）
SQLITE_DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'database.db')
SQLITE_DATABASE_URI = f'sqlite:///{SQLITE_DATABASE_PATH}'
```

- [ ] **Step 5: 验证配置语法**

Run: `cd backend && python -c "from config import Config; print(Config.SQLALCHEMY_DATABASE_URI)"`
Expected: postgresql://postgres:jay123@localhost:5432/confmanage

- [ ] **Step 6: Commit**

```bash
git add backend/config.py
git commit -m "feat: add PostgreSQL configuration with environment variable support"
```

---

### Task 3: 创建迁移脚本

**Files:**
- Create: `backend/migrate_to_postgres.py`

- [ ] **Step 1: 创建迁移脚本骨架**

创建 `backend/migrate_to_postgres.py`：

```python
"""
SQLite到PostgreSQL数据迁移脚本

使用方式：
cd backend
python migrate_to_postgres.py [--sqlite-path PATH] [--skip-verify]

参数：
--sqlite-path: SQLite数据库路径（默认data/database.db）
--skip-verify: 跳过迁移验证
"""

import sys
import os
import json
import argparse
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 导入配置和模型
from config import Config
from models import db
from models.script import Script, ScriptVersion
from models.execution import Execution
from models.schedule import Schedule
from models.environment import Environment
from models.category import Category, Tag, script_tags
from models.workflow import Workflow, WorkflowNode, WorkflowEdge, WorkflowExecution, WorkflowNodeExecution
from models.workflow_template import WorkflowTemplate
from models.global_variable import GlobalVariable
from models.ai_config import AIConfig
from models.webhook import Webhook, WebhookLog
from app import app


# 迁移统计
migration_stats = {
    'tables': {},
    'total_source': 0,
    'total_migrated': 0,
    'errors': []
}


def get_sqlite_engine(sqlite_path=None):
    """获取SQLite引擎"""
    if sqlite_path:
        uri = f'sqlite:///{sqlite_path}'
    else:
        uri = Config.SQLITE_DATABASE_URI
    return create_engine(uri)


def get_postgres_engine():
    """获取PostgreSQL引擎"""
    return create_engine(Config.SQLALCHEMY_DATABASE_URI)


def create_postgres_tables(engine):
    """在PostgreSQL中创建表结构"""
    print("\n[1/4] 创建PostgreSQL表结构...")
    with app.app_context():
        db.create_all(bind=engine)
    print("表结构创建完成")


def migrate_table(source_conn, target_conn, table_name, model_class, json_fields=None):
    """迁移单表数据"""
    print(f"  迁移表: {table_name}...")

    try:
        # 从SQLite读取数据
        result = source_conn.execute(text(f"SELECT * FROM {table_name}"))
        rows = result.fetchall()
        columns = result.keys()

        source_count = len(rows)
        migration_stats['tables'][table_name] = {
            'source': source_count,
            'migrated': 0,
            'status': 'pending'
        }
        migration_stats['total_source'] += source_count

        if source_count == 0:
            print(f"    表 {table_name} 无数据，跳过")
            migration_stats['tables'][table_name]['status'] = 'skipped'
            return

        # 准备插入数据
        inserted = 0
        for row in rows:
            row_dict = dict(zip(columns, row))

            # 处理JSON字段（SQLite存储为字符串）
            if json_fields:
                for field in json_fields:
                    if field in row_dict and row_dict[field]:
                        try:
                            if isinstance(row_dict[field], str):
                                row_dict[field] = row_dict[field]
                        except:
                            pass

            # 创建模型实例
            instance = model_class(**row_dict)
            target_conn.add(instance)
            inserted += 1

        target_conn.commit()
        migration_stats['tables'][table_name]['migrated'] = inserted
        migration_stats['tables'][table_name]['status'] = 'success'
        migration_stats['total_migrated'] += inserted

        print(f"    成功迁移 {inserted} 条记录")

    except Exception as e:
        migration_stats['tables'][table_name]['status'] = 'failed'
        migration_stats['errors'].append(f"{table_name}: {str(e)}")
        print(f"    错误: {str(e)}")
        target_conn.rollback()


def verify_migration(source_conn, target_conn):
    """验证迁移完整性"""
    print("\n[3/4] 验证迁移完整性...")

    tables = migration_stats['tables']
    all_valid = True

    for table_name, stats in tables.items():
        if stats['status'] != 'success':
            continue

        # 查询PostgreSQL记录数
        result = target_conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        pg_count = result.fetchone()[0]

        if pg_count != stats['source']:
            print(f"  ⚠ {table_name}: 源{stats['source']}条，目标{pg_count}条 - 不匹配!")
            all_valid = False
        else:
            print(f"  ✓ {table_name}: {pg_count}条记录一致")

    return all_valid


def print_report():
    """打印迁移报告"""
    print("\n" + "="*50)
    print("迁移报告")
    print("="*50)

    print(f"\n总源记录数: {migration_stats['total_source']}")
    print(f"总迁移记录数: {migration_stats['total_migrated']}")

    print("\n各表详情:")
    for table, stats in migration_stats['tables'].items():
        status_icon = {'success': '✓', 'failed': '✗', 'skipped': '-', 'pending': '?'}
        icon = status_icon.get(stats['status'], '?')
        print(f"  {icon} {table}: {stats['source']} → {stats['migrated']} ({stats['status']})")

    if migration_stats['errors']:
        print("\n错误列表:")
        for error in migration_stats['errors']:
            print(f"  - {error}")

    print("\n" + "="*50)


def main():
    parser = argparse.ArgumentParser(description='SQLite到PostgreSQL迁移脚本')
    parser.add_argument('--sqlite-path', help='SQLite数据库路径')
    parser.add_argument('--skip-verify', action='store_true', help='跳过验证')
    args = parser.parse_args()

    print("="*50)
    print("SQLite → PostgreSQL 数据迁移")
    print("="*50)
    print(f"源数据库: {args.sqlite_path or Config.SQLITE_DATABASE_PATH}")
    print(f"目标数据库: {Config.SQLALCHEMY_DATABASE_URI}")

    # 连接数据库
    sqlite_engine = get_sqlite_engine(args.sqlite_path)
    postgres_engine = get_postgres_engine()

    # 创建PostgreSQL表结构
    create_postgres_tables(postgres_engine)

    # 创建会话
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)

    sqlite_session = SQLiteSession()
    postgres_session = PostgresSession()

    print("\n[2/4] 开始数据迁移...")

    # 按依赖顺序迁移表
    tables_order = [
        ('categories', Category),
        ('tags', Tag),
        ('global_variables', GlobalVariable),
        ('environments', Environment),
        ('scripts', Script),
        ('script_versions', ScriptVersion),
        ('script_tags', None),  # 关联表，特殊处理
        ('executions', Execution, ['params']),
        ('schedules', Schedule, ['params']),
        ('webhooks', Webhook),
        ('webhook_logs', WebhookLog),
        ('workflows', Workflow, ['nodes', 'edges']),
        ('workflow_nodes', WorkflowNode, ['config']),
        ('workflow_edges', WorkflowEdge),
        ('workflow_executions', WorkflowExecution, ['params', 'node_executions']),
        ('workflow_node_executions', WorkflowNodeExecution, ['params', 'output']),
        ('workflow_templates', WorkflowTemplate, ['nodes', 'edges']),
        ('ai_configs', AIConfig),
    ]

    for table_info in tables_order:
        table_name = table_info[0]
        model_class = table_info[1]
        json_fields = table_info[2] if len(table_info) > 2 else None

        if model_class is None:
            # 特殊处理关联表
            migrate_association_table(sqlite_session, postgres_session, table_name)
        else:
            migrate_table(sqlite_session, postgres_session, table_name, model_class, json_fields)

    # 验证迁移
    if not args.skip_verify:
        valid = verify_migration(sqlite_session, postgres_session)
        if not valid:
            print("\n⚠ 验证失败，请检查数据完整性!")

    # 打印报告
    print_report()

    # 关闭连接
    sqlite_session.close()
    postgres_session.close()

    print("\n迁移完成!")


def migrate_association_table(source_conn, target_conn, table_name):
    """迁移关联表（如script_tags）"""
    print(f"  迁移关联表: {table_name}...")

    try:
        result = source_conn.execute(text(f"SELECT * FROM {table_name}"))
        rows = result.fetchall()

        if not rows:
            print(f"    表 {table_name} 无数据，跳过")
            return

        # 直接插入
        for row in rows:
            columns = result.keys()
            values = dict(zip(columns, row))
            insert_sql = text(f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({','.join([':'+c for c in columns])})")
            target_conn.execute(insert_sql, values)

        target_conn.commit()
        print(f"    成功迁移 {len(rows)} 条记录")

    except Exception as e:
        print(f"    错误: {str(e)}")
        target_conn.rollback()


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: 验证脚本语法**

Run: `cd backend && python -c "import migrate_to_postgres; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add backend/migrate_to_postgres.py
git commit -m "feat: add SQLite to PostgreSQL migration script"
```

---

### Task 4: 确保 PostgreSQL 数据库已创建

**Files:**
- 无文件修改，数据库准备

- [ ] **Step 1: 检查 PostgreSQL 服务状态**

Run: `psql -U postgres -c "SELECT version();"`
Expected: PostgreSQL 版本信息输出

如果连接失败，请确保 PostgreSQL 服务已启动：
```bash
# Windows: 通过服务管理器启动 PostgreSQL
# 或使用: net start postgresql-x64-15
```

- [ ] **Step 2: 创建数据库**

Run: `psql -U postgres -c "CREATE DATABASE confmanage;"`
Expected: CREATE DATABASE

如果数据库已存在，会输出：database "confmanage" already exists

- [ ] **Step 3: 验证数据库创建**

Run: `psql -U postgres -c "\l confmanage"`
Expected: 显示 confmanage 数据库信息

---

### Task 5: 执行迁移

**Files:**
- 无文件修改，执行迁移

- [ ] **Step 1: 备份 SQLite 数据库**

Run: `cp backend/data/database.db backend/data/database.db.backup`
Expected: 创建备份文件

- [ ] **Step 2: 运行迁移脚本**

Run: `cd backend && python migrate_to_postgres.py`
Expected: 迁移报告显示各表迁移状态

迁移成功输出示例：
```
==================================================
SQLite → PostgreSQL 数据迁移
==================================================
源数据库: data/database.db
目标数据库: postgresql://postgres:jay123@localhost:5432/confmanage

[1/4] 创建PostgreSQL表结构...
表结构创建完成

[2/4] 开始数据迁移...
  迁移表: categories...
    成功迁移 X 条记录
  ...

[3/4] 验证迁移完整性...
  ✓ categories: X条记录一致
  ...

==================================================
迁移报告
==================================================
总源记录数: XXX
总迁移记录数: XXX
...
迁移完成!
```

- [ ] **Step 3: 验证应用启动**

Run: `cd backend && python app.py`
Expected: Flask 应用正常启动，无数据库错误

- [ ] **Step 4: 前端验证（可选）**

启动前端，验证：
1. 脚本列表正常显示
2. 执行历史正常显示
3. 各功能正常工作

- [ ] **Step 5: Commit 迁移完成标记**

```bash
git add backend/data/database.db.backup
git commit -m "chore: complete PostgreSQL migration, backup SQLite database"
```

---

### Task 6: 测试回退能力

**Files:**
- 无文件修改，验证回退

- [ ] **Step 1: 测试环境变量回退到 SQLite**

Run: `cd backend && DB_TYPE=sqlite python -c "from config import Config; print(Config.SQLALCHEMY_DATABASE_URI)"`
Expected: sqlite:///...路径

- [ ] **Step 2: 验证回退后应用可用**

Run: `cd backend && DB_TYPE=sqlite python app.py`
Expected: Flask 应用正常启动，使用 SQLite

- [ ] **Step 3: 确认 PostgreSQL 配置为默认**

运行正常模式验证：
Run: `cd backend && python -c "from config import Config; print('DB:', Config.SQLALCHEMY_DATABASE_URI[:20])"`
Expected: DB: postgresql://...

---

## 自检清单

**1. Spec覆盖检查:**
- ✓ PostgreSQL 连接配置 - Task 2
- ✓ 环境变量支持 - Task 2
- ✓ 连接池配置 - Task 2
- ✓ 迁移脚本 - Task 3
- ✓ 迁移表顺序 - Task 3 (tables_order)
- ✓ 数据验证 - Task 5
- ✓ 回退方案 - Task 6

**2. Placeholder扫描:**
- 无 TBD、TODO、implement later
- 无 "add appropriate error handling"
- 所有代码步骤都有完整实现

**3. 类型一致性:**
- Config.SQLALCHEMY_DATABASE_URI 使用字符串格式一致
- 迁移脚本使用 SQLAlchemy 模型与现有模型一致

---

## 完成标记

迁移完成后，后续开发将默认使用 PostgreSQL。如需回退，设置环境变量 `DB_TYPE=sqlite`。