"""
创建工作流相关表的迁移脚本
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db

def upgrade():
    """创建工作流相关表"""
    app = create_app()
    with app.app_context():
        # 创建表
        db.create_all()
        print('✅ 工作流表创建成功！')
        print('创建的表:')
        print('  - workflows (工作流表)')
        print('  - workflow_nodes (工作流节点表)')
        print('  - workflow_edges (工作流边表)')
        print('  - workflow_executions (工作流执行记录表)')
        print('  - workflow_node_executions (节点执行记录表)')

if __name__ == '__main__':
    upgrade()
