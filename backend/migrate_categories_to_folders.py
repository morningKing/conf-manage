"""
数据迁移脚本：将 categories 表迁移为 folders 表
运行方式: python backend/migrate_categories_to_folders.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'database.db')

def migrate():
    if not os.path.exists(DB_PATH):
        print("数据库文件不存在，跳过迁移")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 检查 categories 表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categories'")
        has_categories = cursor.fetchone() is not None

        # 检查 folders 表是否已存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='folders'")
        has_folders = cursor.fetchone() is not None

        if has_categories and not has_folders:
            # 创建 folders 表
            cursor.execute('''
                CREATE TABLE folders (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    parent_id INTEGER REFERENCES folders(id),
                    color VARCHAR(20) DEFAULT '#E6A23C',
                    sort_order INTEGER DEFAULT 0,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''')

            # 从 categories 迁移数据
            cursor.execute('SELECT id, name, sort_order, created_at, updated_at FROM categories')
            rows = cursor.fetchall()
            for row in rows:
                cursor.execute(
                    'INSERT INTO folders (id, name, parent_id, sort_order, created_at, updated_at) VALUES (?, ?, NULL, ?, ?, ?)',
                    (row[0], row[1], row[2], row[3], row[4])
                )
            print(f"迁移了 {len(rows)} 个分类到文件夹")

            # 检查 scripts 表是否有 category_id 列
            cursor.execute("PRAGMA table_info(scripts)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'category_id' in columns and 'folder_id' not in columns:
                cursor.execute("ALTER TABLE scripts RENAME COLUMN category_id TO folder_id")
                print("已将 scripts.category_id 重命名为 folder_id")

            conn.commit()
            print("分类迁移完成！")

        elif has_folders:
            print("folders 表已存在，跳过分类迁移")
        else:
            print("categories 表不存在，跳过分类迁移")

    except Exception as e:
        conn.rollback()
        print(f"分类迁移失败: {e}")
    finally:
        conn.close()

    # 第二阶段：为 folders 表添加 color 列（幂等）
    add_color_column()


def add_color_column():
    if not os.path.exists(DB_PATH):
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='folders'")
        if not cursor.fetchone():
            conn.close()
            return

        cursor.execute("PRAGMA table_info(folders)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'color' not in columns:
            cursor.execute("ALTER TABLE folders ADD COLUMN color VARCHAR(20) DEFAULT '#E6A23C'")
            conn.commit()
            print("已为 folders 表添加 color 列")
        else:
            print("folders 表已有 color 列，跳过")
    except Exception as e:
        conn.rollback()
        print(f"添加 color 列失败: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
