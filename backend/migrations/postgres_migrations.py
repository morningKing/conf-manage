"""
PostgreSQL 数据库迁移脚本
统一管理所有数据库迁移操作
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from config import Config

# 数据库连接配置
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'jay123'),
    'database': os.environ.get('DB_NAME', 'confmanage')
}


def get_connection():
    """获取数据库连接"""
    return psycopg2.connect(**DB_CONFIG)


def check_column_exists(table_name, column_name):
    """检查字段是否存在"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
    """, (table_name, column_name))
    exists = cur.fetchone() is not None
    conn.close()
    return exists


def check_table_exists(table_name):
    """检查表是否存在"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public' AND tablename = %s
    """, (table_name,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists


def add_column(table_name, column_name, column_type):
    """添加字段"""
    if check_column_exists(table_name, column_name):
        print(f'[SKIP] {table_name}.{column_name} already exists')
        return False

    conn = get_connection()
    cur = conn.cursor()
    print(f'[ADD] Adding {table_name}.{column_name} ({column_type})...')
    cur.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}')
    conn.commit()
    conn.close()
    print(f'[OK] {table_name}.{column_name} added')
    return True


def create_table(table_name, columns_def):
    """创建表"""
    if check_table_exists(table_name):
        print(f'[SKIP] Table {table_name} already exists')
        return False

    conn = get_connection()
    cur = conn.cursor()
    print(f'[CREATE] Creating table {table_name}...')
    cur.execute(f'CREATE TABLE {table_name} ({columns_def})')
    conn.commit()
    conn.close()
    print(f'[OK] Table {table_name} created')
    return True


def migrate_preserve_fields():
    """迁移 preserve 字段到 scripts 和 schedules 表"""
    print('\n=== Migrating preserve fields ===')
    add_column('scripts', 'preserve', 'BOOLEAN DEFAULT FALSE NOT NULL')
    add_column('schedules', 'preserve', 'BOOLEAN DEFAULT FALSE NOT NULL')


def migrate_execution_fields():
    """迁移执行进度相关字段"""
    print('\n=== Migrating execution progress fields ===')
    add_column('executions', 'progress', 'INTEGER DEFAULT 0')
    add_column('executions', 'stage', "VARCHAR(50) DEFAULT 'pending'")
    add_column('executions', 'pid', 'INTEGER')
    add_column('executions', 'environment_id', 'INTEGER REFERENCES environments(id)')


def migrate_script_fields():
    """迁移脚本相关字段"""
    print('\n=== Migrating script fields ===')
    add_column('scripts', 'parameters', 'TEXT')
    add_column('scripts', 'environment_id', 'INTEGER REFERENCES environments(id)')
    add_column('scripts', 'folder_id', 'INTEGER REFERENCES folders(id)')
    add_column('scripts', 'is_favorite', 'BOOLEAN DEFAULT FALSE')


def migrate_schedule_fields():
    """迁移定时任务相关字段"""
    print('\n=== Migrating schedule fields ===')
    add_column('schedules', 'description', 'TEXT')


def run_all_migrations():
    """执行所有迁移"""
    print('=' * 60)
    print('PostgreSQL Database Migration')
    print('=' * 60)

    # 按依赖顺序执行迁移
    migrate_preserve_fields()
    migrate_execution_fields()
    migrate_script_fields()
    migrate_schedule_fields()

    print('\n' + '=' * 60)
    print('[DONE] All migrations completed')
    print('=' * 60)


def show_table_structure():
    """显示当前表结构"""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
    tables = [row[0] for row in cur.fetchall()]

    print('\n=== Current Table Structure ===')
    for table in tables:
        cur.execute(f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = '{table}'
            ORDER BY ordinal_position
        """)
        columns = cur.fetchall()
        print(f'\n{table}:')
        for col_name, dtype, nullable in columns:
            print(f'  {col_name}: {dtype} ({nullable})')

    conn.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='PostgreSQL Database Migration Tool')
    parser.add_argument('action', choices=['migrate', 'status', 'check'],
                        help='Action: migrate (run migrations), status (show structure), check (check missing)')
    parser.add_argument('--table', help='Specific table to check')

    args = parser.parse_args()

    if args.action == 'migrate':
        run_all_migrations()
    elif args.action == 'status':
        show_table_structure()
    elif args.action == 'check':
        if args.table:
            print(f'\n=== Checking {args.table} ===')
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(f"""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = '{args.table}' ORDER BY ordinal_position
            """)
            columns = [row[0] for row in cur.fetchall()]
            print(f'{args.table}: {columns}')
            conn.close()
        else:
            print('Please specify --table')