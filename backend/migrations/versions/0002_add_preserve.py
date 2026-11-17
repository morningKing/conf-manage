"""补充 scripts/schedules 的 preserve（清理白名单）列

此前 preserve 列仅存在于模型定义，db.create_all() 不会为存量库加列，
导致存量 PostgreSQL 库启动后相关接口报 column does not exist。
幂等实现：列已存在时跳过（新库由 0001 基线直接建出）。

Revision ID: 0002_add_preserve
Revises: 0001_baseline
"""
import sqlalchemy as sa
from alembic import op

revision = '0002_add_preserve'
down_revision = '0001_baseline'
branch_labels = None
depends_on = None


def _has_column(table, column):
    inspector = sa.inspect(op.get_bind())
    return column in [c['name'] for c in inspector.get_columns(table)]


def upgrade():
    if not _has_column('scripts', 'preserve'):
        op.add_column('scripts', sa.Column('preserve', sa.Boolean(), nullable=False,
                                           server_default=sa.false()))
    if not _has_column('schedules', 'preserve'):
        op.add_column('schedules', sa.Column('preserve', sa.Boolean(), nullable=False,
                                             server_default=sa.false()))


def downgrade():
    if _has_column('schedules', 'preserve'):
        op.drop_column('schedules', 'preserve')
    if _has_column('scripts', 'preserve'):
        op.drop_column('scripts', 'preserve')
