"""基线：按当前模型创建全部表

新库通过 `alembic upgrade head` 建表；
存量库（此前由 db.create_all() 建表）使用 `alembic stamp 0001_baseline` 跳过本迁移。

Revision ID: 0001_baseline
Revises:
"""
from alembic import op

revision = '0001_baseline'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    from models import db
    db.metadata.create_all(bind=op.get_bind())


def downgrade():
    from models import db
    db.metadata.drop_all(bind=op.get_bind())
