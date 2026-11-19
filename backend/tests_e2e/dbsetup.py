# -*- coding: utf-8 -*-
"""
E2E 数据库装配（pytest 与 Playwright 共用）

确保存在独立测试库 confmanage_e2e（绝不触碰用户业务库 confmanage）：
- PostgreSQL 可达：DROP IF EXISTS (FORCE) + CREATE，保证每次全量干净
- 不可达：回退 SQLite 文件库 backend/e2e_test.db

命令行入口供 Playwright webServer 在启动后端前调用：
    python tests_e2e/dbsetup.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 注意：不要在此导入 config —— run_server.py 需在设置环境变量之后再加载 app/config

PG_HOST = os.environ.get('DB_HOST', 'localhost')
PG_PORT = os.environ.get('DB_PORT', '5432')
PG_USER = os.environ.get('DB_USER', 'postgres')
PG_PASSWORD = os.environ.get('DB_PASSWORD', 'jay123')
E2E_DB_NAME = os.environ.get('E2E_DB_NAME', 'confmanage_e2e')


def build_pg_url(dbname):
    return f'postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{dbname}'


def ensure_e2e_database():
    """
    返回 (database_url, engine_name)。
    """
    try:
        import psycopg2
    except ImportError:
        return _sqlite_url(), 'sqlite'

    try:
        conn = psycopg2.connect(host=PG_HOST, port=PG_PORT, user=PG_USER,
                                password=PG_PASSWORD, dbname='postgres', connect_timeout=3)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = %s AND pid <> pg_backend_pid()", (E2E_DB_NAME,))
        cur.execute(f'DROP DATABASE IF EXISTS "{E2E_DB_NAME}"')
        cur.execute(f'CREATE DATABASE "{E2E_DB_NAME}"')
        cur.close()
        conn.close()
        return build_pg_url(E2E_DB_NAME), 'postgresql'
    except Exception as e:
        print(f'[dbsetup] PostgreSQL 不可用（{e}），回退 SQLite')
        return _sqlite_url(), 'sqlite'


def _sqlite_url():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'e2e_test.db')
    if os.path.exists(path):
        os.remove(path)
    return 'sqlite:///' + path.replace('\\', '/')


def server_env():
    """启动被测服务所需的环境变量"""
    url, engine = ensure_e2e_database()
    env = os.environ.copy()
    env['DATABASE_URL'] = url
    env['HOST_PORT'] = os.environ.get('E2E_PORT', '5101')
    env['HOST_DEBUG'] = 'false'
    print(f'[dbsetup] engine={engine} port={env["HOST_PORT"]}')
    return env


if __name__ == '__main__':
    server_env()
