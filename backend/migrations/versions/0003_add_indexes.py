"""热点列补索引（executions / webhook_logs / workflow_node_executions）

与模型定义中的 index=True 对应；幂等：索引已存在时跳过。

Revision ID: 0003_add_indexes
Revises: 0002_add_preserve
"""
import sqlalchemy as sa
from alembic import op

revision = '0003_add_indexes'
down_revision = '0002_add_preserve'
branch_labels = None
depends_on = None

INDEXES = [
    ('ix_executions_script_id', 'executions', ['script_id']),
    ('ix_executions_status', 'executions', ['status']),
    ('ix_executions_created_at', 'executions', ['created_at']),
    ('ix_webhook_logs_webhook_id', 'webhook_logs', ['webhook_id']),
    ('ix_webhook_logs_created_at', 'webhook_logs', ['created_at']),
    ('ix_workflow_node_executions_workflow_execution_id', 'workflow_node_executions', ['workflow_execution_id']),
]


def _existing_indexes(table):
    return {i['name'] for i in sa.inspect(op.get_bind()).get_indexes(table)}


def upgrade():
    for name, table, cols in INDEXES:
        if name not in _existing_indexes(table):
            op.create_index(name, table, cols)


def downgrade():
    for name, table, cols in reversed(INDEXES):
        if name in _existing_indexes(table):
            op.drop_index(name, table)
