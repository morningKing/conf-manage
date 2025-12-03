"""
手动添加脚本表的新列

运行方式:
PYTHONPATH=/mnt/e/Code/ccr/conf-manage/backend:$PYTHONPATH python3 backend/migrations/add_script_columns.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db

def migrate():
    """添加category_id和is_favorite列到scripts表"""
    app = create_app()

    with app.app_context():
        print("开始添加列到scripts表...")

        try:
            # 检查列是否已存在
            with db.engine.connect() as conn:
                # 尝试添加category_id列
                try:
                    conn.execute(db.text("ALTER TABLE scripts ADD COLUMN category_id INTEGER"))
                    print("  - 添加 category_id 列")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        print("  - category_id 列已存在")
                    else:
                        print(f"  - 添加 category_id 列失败: {e}")

                # 尝试添加is_favorite列
                try:
                    conn.execute(db.text("ALTER TABLE scripts ADD COLUMN is_favorite BOOLEAN DEFAULT 0"))
                    print("  - 添加 is_favorite 列")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        print("  - is_favorite 列已存在")
                    else:
                        print(f"  - 添加 is_favorite 列失败: {e}")

                conn.commit()

            print("迁移完成!")
        except Exception as e:
            print(f"迁移失败: {e}")
            raise

if __name__ == '__main__':
    migrate()
