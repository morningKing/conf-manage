"""
pytest 共享 fixture

冒烟测试使用 SQLite 内存库，无需外部 PostgreSQL 依赖；
仅覆盖路由层与模型层的可用性，不覆盖 PG 特有行为。
"""
import os
import sys

import pytest

# backend 目录加入 sys.path，便于直接 import app/models/config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from models import db  # noqa: E402


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
