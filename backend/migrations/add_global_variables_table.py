"""
创建全局变量表的迁移脚本
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, GlobalVariable

def migrate():
    """执行迁移"""
    app = create_app()

    with app.app_context():
        # 创建表
        print('创建 global_variables 表...')
        db.create_all()
        print('✓ global_variables 表创建完成')

        print('\n迁移完成！')

if __name__ == '__main__':
    migrate()
