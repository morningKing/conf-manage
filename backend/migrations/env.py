"""
Alembic 迁移环境

连接串从 backend/config.py 读取（数据库参数或 DATABASE_URL 环境变量）。
target_metadata 使用 Flask-SQLAlchemy 的 db.metadata，与模型定义保持单一来源。
"""
import os
import sys

from alembic import context

# 确保 backend 目录可导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config  # noqa: E402
from models import db  # noqa: E402

config = context.config

# 用应用配置覆盖 ini 中的占位连接串
config.set_main_option('sqlalchemy.url', Config.SQLALCHEMY_DATABASE_URI)

target_metadata = db.metadata


def run_migrations_offline():
    """离线模式：仅生成 SQL，不连接数据库"""
    context.configure(
        url=config.get_main_option('sqlalchemy.url'),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """在线模式：连接数据库执行迁移"""
    from sqlalchemy import create_engine

    connectable = create_engine(config.get_main_option('sqlalchemy.url'))
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
