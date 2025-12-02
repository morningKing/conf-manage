"""
数据库迁移脚本 - 添加执行环境管理
1. 创建 environments 表
2. 为 scripts 表添加 environment_id 字段
"""
import sqlite3
import os
import sys

# 添加父目录到路径，以便导入config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config


def migrate():
    """执行数据库迁移"""
    # 从SQLALCHEMY_DATABASE_URI提取数据库路径
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    db_path = db_uri.replace('sqlite:///', '')

    print(f"正在连接数据库: {db_path}")

    # 检查数据库是否存在
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. 检查 environments 表是否已存在
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='environments'
        """)
        if cursor.fetchone():
            print("environments 表已存在")
        else:
            # 创建 environments 表
            print("正在创建 environments 表...")
            cursor.execute("""
                CREATE TABLE environments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    type VARCHAR(20) NOT NULL,
                    executable_path VARCHAR(500) NOT NULL,
                    description TEXT,
                    is_default BOOLEAN DEFAULT 0,
                    version VARCHAR(50),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✓ environments 表创建成功")

        # 2. 检查 scripts 表的 environment_id 字段是否已存在
        cursor.execute("PRAGMA table_info(scripts)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'environment_id' in columns:
            print("scripts.environment_id 字段已存在")
        else:
            # 添加 environment_id 字段
            print("正在添加 scripts.environment_id 字段...")
            cursor.execute("""
                ALTER TABLE scripts
                ADD COLUMN environment_id INTEGER
                REFERENCES environments(id)
            """)
            print("✓ scripts.environment_id 字段添加成功")

        conn.commit()
        print("\n✓ 迁移全部完成！")

        # 验证迁移
        print("\n验证迁移结果:")
        cursor.execute("PRAGMA table_info(environments)")
        env_columns = [col[1] for col in cursor.fetchall()]
        print(f"  environments 表字段: {', '.join(env_columns)}")

        cursor.execute("PRAGMA table_info(scripts)")
        script_columns = [col[1] for col in cursor.fetchall()]
        print(f"  scripts 表字段: {', '.join(script_columns)}")

        conn.close()
        return True

    except Exception as e:
        print(f"✗ 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def rollback():
    """回滚迁移"""
    # 从SQLALCHEMY_DATABASE_URI提取数据库路径
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    db_path = db_uri.replace('sqlite:///', '')

    print(f"正在连接数据库: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("警告: 此操作将删除 environments 表和 scripts.environment_id 字段")
        response = input("确认继续？(yes/no): ")
        if response.lower() != 'yes':
            print("回滚已取消")
            return False

        # 1. 删除 scripts 表的 environment_id 字段
        cursor.execute("PRAGMA table_info(scripts)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'environment_id' in columns:
            print("正在删除 scripts.environment_id 字段...")

            # SQLite 不支持直接删除列，需要重建表
            # 获取所有字段（除了 environment_id）
            cursor.execute("PRAGMA table_info(scripts)")
            table_info = cursor.fetchall()

            columns_def = []
            column_names = []
            for col in table_info:
                col_name = col[1]
                if col_name != 'environment_id':
                    column_names.append(col_name)

            # 开始事务
            cursor.execute("BEGIN TRANSACTION")

            # 创建临时表（不包含 environment_id）
            cursor.execute("""
                CREATE TABLE scripts_temp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    description TEXT,
                    type VARCHAR(20) NOT NULL,
                    code TEXT NOT NULL,
                    dependencies TEXT,
                    parameters TEXT,
                    version INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 复制数据
            cursor.execute(f"""
                INSERT INTO scripts_temp ({', '.join(column_names)})
                SELECT {', '.join(column_names)} FROM scripts
            """)

            # 删除旧表
            cursor.execute("DROP TABLE scripts")

            # 重命名临时表
            cursor.execute("ALTER TABLE scripts_temp RENAME TO scripts")

            cursor.execute("COMMIT")
            print("✓ scripts.environment_id 字段已删除")

        # 2. 删除 environments 表
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='environments'
        """)
        if cursor.fetchone():
            print("正在删除 environments 表...")
            cursor.execute("DROP TABLE environments")
            print("✓ environments 表已删除")

        conn.commit()
        print("\n✓ 回滚全部完成！")

        conn.close()
        return True

    except Exception as e:
        print(f"✗ 回滚失败: {str(e)}")
        if conn:
            conn.rollback()
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='数据库迁移脚本 - 执行环境管理')
    parser.add_argument('action', choices=['migrate', 'rollback'],
                       help='迁移操作: migrate (应用迁移) 或 rollback (回滚迁移)')

    args = parser.parse_args()

    if args.action == 'migrate':
        success = migrate()
    else:
        success = rollback()

    sys.exit(0 if success else 1)
