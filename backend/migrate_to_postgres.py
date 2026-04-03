#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SQLite 到 PostgreSQL 数据迁移脚本

使用方法:
    python migrate_to_postgres.py --sqlite-path /path/to/database.db
    python migrate_to_postgres.py --skip-verify  # 跳过验证

环境变量 (PostgreSQL 连接配置):
    DB_HOST: 数据库主机 (默认: localhost)
    DB_PORT: 数据库端口 (默认: 5432)
    DB_USER: 数据库用户 (默认: postgres)
    DB_PASSWORD: 数据库密码 (默认: 空)
    DB_NAME: 数据库名称 (默认: confmanage)
"""

import sys
import os
import argparse
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from models import (
    db, Script, ScriptVersion, Execution, Schedule, Environment,
    Category, Tag, script_tags, Workflow, WorkflowNode, WorkflowEdge,
    WorkflowExecution, WorkflowNodeExecution, WorkflowTemplate, GlobalVariable,
    AIConfig, Webhook, WebhookLog
)
from flask import Flask


def get_sqlite_engine(sqlite_path=None):
    """获取 SQLite 数据库引擎"""
    if sqlite_path:
        uri = f'sqlite:///{sqlite_path}'
    else:
        uri = Config.SQLITE_DATABASE_URI
    print(f"[INFO] SQLite URI: {uri}")
    return create_engine(uri)


def get_postgres_engine():
    """获取 PostgreSQL 数据库引擎"""
    uri = Config.SQLALCHEMY_DATABASE_URI
    # 隐藏密码显示
    display_uri = uri
    if 'postgresql://' in uri and '@' in uri:
        parts = uri.split('@')
        display_uri = parts[0].rsplit(':', 1)[0] + ':***@' + parts[1]
    print(f"[INFO] PostgreSQL URI: {display_uri}")
    return create_engine(uri)


def create_postgres_tables(pg_engine):
    """在 PostgreSQL 中创建表结构"""
    print("\n[STEP] 创建 PostgreSQL 表结构...")

    # 创建 Flask 应用上下文
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        # 删除已存在的表（如果需要重新迁移）
        # db.drop_all()
        db.create_all()

    print("[OK] 表结构创建完成")


def get_table_count(engine, table_name):
    """获取表中的记录数"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar()
    except Exception:
        return 0


def migrate_table(sqlite_engine, pg_engine, model_class, json_fields=None):
    """
    迁移单个表的数据

    Args:
        sqlite_engine: SQLite 引擎
        pg_engine: PostgreSQL 引擎
        model_class: SQLAlchemy 模型类
        json_fields: 需要特殊处理的 JSON 字段列表
    """
    table_name = model_class.__tablename__
    json_fields = json_fields or []

    print(f"\n[MIGRATING] {table_name}...")

    # 获取 SQLite 数据
    sqlite_session = sessionmaker(bind=sqlite_engine)()
    pg_session = sessionmaker(bind=pg_engine)()

    try:
        # 获取所有记录
        records = sqlite_session.execute(text(f"SELECT * FROM {table_name}"))
        columns = records.keys()
        rows = records.fetchall()

        if not rows:
            print(f"  [SKIP] {table_name} 表为空，跳过")
            sqlite_session.close()
            pg_session.close()
            return 0

        # 获取模型列名
        inspector = inspect(model_class)
        model_columns = [col.name for col in inspector.columns]

        migrated_count = 0
        for row in rows:
            # 构建数据字典
            data = {}
            for i, col in enumerate(columns):
                if col in model_columns:
                    value = row[i]
                    # SQLite 的布尔值处理
                    if isinstance(value, int) and col in ['enabled', 'is_favorite', 'is_default',
                                                            'is_encrypted', 'is_active',
                                                            'token_enabled', 'pass_full_request',
                                                            'is_builtin']:
                        value = bool(value)
                    data[col] = value

            # 创建模型实例并插入
            instance = model_class(**data)
            pg_session.add(instance)
            migrated_count += 1

            # 每100条提交一次
            if migrated_count % 100 == 0:
                pg_session.commit()

        pg_session.commit()
        print(f"  [OK] 迁移 {migrated_count} 条记录")

        sqlite_session.close()
        pg_session.close()

        return migrated_count

    except Exception as e:
        pg_session.rollback()
        print(f"  [ERROR] 迁移 {table_name} 失败: {str(e)}")
        raise


def migrate_association_table(sqlite_engine, pg_engine, table_name, table_obj):
    """
    迁移关联表（多对多关系表）

    Args:
        sqlite_engine: SQLite 引擎
        pg_engine: PostgreSQL 引擎
        table_name: 表名
        table_obj: SQLAlchemy Table 对象
    """
    print(f"\n[MIGRATING] {table_name} (关联表)...")

    try:
        # 获取 SQLite 数据
        with sqlite_engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table_name}"))
            columns = result.keys()
            rows = result.fetchall()

        if not rows:
            print(f"  [SKIP] {table_name} 表为空，跳过")
            return 0

        # 获取列名（排除自动生成的）
        table_columns = [col.name for col in table_obj.columns]

        # 插入到 PostgreSQL
        with pg_engine.connect() as conn:
            migrated_count = 0
            for row in rows:
                # 构建数据字典
                data = {}
                for i, col in enumerate(columns):
                    if col in table_columns:
                        value = row[i]
                        # 处理 created_at 字段
                        if col == 'created_at' and value is None:
                            value = datetime.utcnow()
                        data[col] = value

                # 构建 INSERT 语句
                col_names = ', '.join(data.keys())
                placeholders = ', '.join([f':{k}' for k in data.keys()])
                sql = text(f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})")
                conn.execute(sql, data)
                migrated_count += 1

            conn.commit()

        print(f"  [OK] 迁移 {migrated_count} 条记录")
        return migrated_count

    except Exception as e:
        print(f"  [ERROR] 迁移 {table_name} 失败: {str(e)}")
        raise


def verify_migration(sqlite_engine, pg_engine, skip=False):
    """验证迁移结果"""
    if skip:
        print("\n[SKIP] 跳过验证")
        return True

    print("\n[STEP] 验证迁移结果...")

    tables_to_verify = [
        ('categories', 'categories'),
        ('tags', 'tags'),
        ('global_variables', 'global_variables'),
        ('environments', 'environments'),
        ('scripts', 'scripts'),
        ('script_versions', 'script_versions'),
        ('script_tags', 'script_tags'),
        ('executions', 'executions'),
        ('schedules', 'schedules'),
        ('webhooks', 'webhooks'),
        ('webhook_logs', 'webhook_logs'),
        ('workflows', 'workflows'),
        ('workflow_nodes', 'workflow_nodes'),
        ('workflow_edges', 'workflow_edges'),
        ('workflow_executions', 'workflow_executions'),
        ('workflow_node_executions', 'workflow_node_executions'),
        ('workflow_templates', 'workflow_templates'),
        ('ai_configs', 'ai_configs'),
    ]

    all_valid = True
    for sqlite_table, pg_table in tables_to_verify:
        sqlite_count = get_table_count(sqlite_engine, sqlite_table)
        pg_count = get_table_count(pg_engine, pg_table)

        status = "OK" if sqlite_count == pg_count else "MISMATCH"
        if status == "MISMATCH":
            all_valid = False

        print(f"  {sqlite_table}: SQLite={sqlite_count}, PostgreSQL={pg_count} [{status}]")

    return all_valid


def print_report(results):
    """打印迁移报告"""
    print("\n" + "=" * 60)
    print("迁移报告")
    print("=" * 60)

    total_records = 0
    for table_name, count in results.items():
        print(f"  {table_name}: {count} 条记录")
        total_records += count

    print("-" * 60)
    print(f"  总计: {total_records} 条记录")
    print("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='SQLite 到 PostgreSQL 数据迁移脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python migrate_to_postgres.py
    python migrate_to_postgres.py --sqlite-path /path/to/database.db
    python migrate_to_postgres.py --skip-verify

环境变量 (PostgreSQL 连接配置):
    DB_HOST: 数据库主机 (默认: localhost)
    DB_PORT: 数据库端口 (默认: 5432)
    DB_USER: 数据库用户 (默认: postgres)
    DB_PASSWORD: 数据库密码 (默认: 空)
    DB_NAME: 数据库名称 (默认: confmanage)
        """
    )

    parser.add_argument(
        '--sqlite-path',
        type=str,
        default=None,
        help='SQLite 数据库文件路径 (默认: data/database.db)'
    )

    parser.add_argument(
        '--skip-verify',
        action='store_true',
        help='跳过迁移验证'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("SQLite 到 PostgreSQL 数据迁移")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 检查 PostgreSQL 环境变量配置
    print("\n[CONFIG] PostgreSQL 连接配置:")
    print(f"  DB_HOST: {os.environ.get('DB_HOST', 'localhost')}")
    print(f"  DB_PORT: {os.environ.get('DB_PORT', '5432')}")
    print(f"  DB_USER: {os.environ.get('DB_USER', 'postgres')}")
    print(f"  DB_NAME: {os.environ.get('DB_NAME', 'confmanage')}")

    # 创建数据库引擎
    print("\n[STEP] 创建数据库连接...")
    try:
        sqlite_engine = get_sqlite_engine(args.sqlite_path)
        pg_engine = get_postgres_engine()
    except Exception as e:
        print(f"[ERROR] 创建数据库连接失败: {str(e)}")
        sys.exit(1)

    # 创建 PostgreSQL 表结构
    try:
        create_postgres_tables(pg_engine)
    except Exception as e:
        print(f"[ERROR] 创建表结构失败: {str(e)}")
        sys.exit(1)

    # 定义迁移顺序（按依赖关系排序）
    tables_order = [
        # (表名, 模型类, JSON字段列表)
        ('categories', Category, None),
        ('tags', Tag, None),
        ('global_variables', GlobalVariable, None),
        ('environments', Environment, None),
        ('scripts', Script, None),
        ('script_versions', ScriptVersion, None),
        # script_tags 是关联表，特殊处理
        ('script_tags', None, None),
        ('executions', Execution, ['params']),
        ('schedules', Schedule, ['params']),
        ('webhooks', Webhook, None),
        ('webhook_logs', WebhookLog, None),
        ('workflows', Workflow, ['config']),
        ('workflow_nodes', WorkflowNode, ['config']),
        ('workflow_edges', WorkflowEdge, ['condition']),
        ('workflow_executions', WorkflowExecution, ['params']),
        ('workflow_node_executions', WorkflowNodeExecution, ['output']),
        ('workflow_templates', WorkflowTemplate, ['template_config']),
        ('ai_configs', AIConfig, None),
    ]

    # 执行迁移
    print("\n[STEP] 开始数据迁移...")
    results = {}

    for item in tables_order:
        table_name = item[0]
        model_class = item[1]
        json_fields = item[2] if len(item) > 2 else None

        try:
            if table_name == 'script_tags':
                # 关联表特殊处理
                count = migrate_association_table(
                    sqlite_engine, pg_engine,
                    'script_tags', script_tags
                )
            else:
                count = migrate_table(
                    sqlite_engine, pg_engine,
                    model_class, json_fields
                )
            results[table_name] = count

        except Exception as e:
            print(f"[ERROR] 迁移 {table_name} 时出错: {str(e)}")
            print("[WARNING] 继续迁移其他表...")
            results[table_name] = 0

    # 验证迁移
    verify_ok = verify_migration(sqlite_engine, pg_engine, args.skip_verify)

    # 打印报告
    print_report(results)

    # 完成
    print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if verify_ok:
        print("\n[SUCCESS] 迁移完成!")
        sys.exit(0)
    else:
        print("\n[WARNING] 迁移完成，但验证发现不一致，请检查数据!")
        sys.exit(1)


if __name__ == '__main__':
    main()