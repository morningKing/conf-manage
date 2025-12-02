"""
数据库迁移脚本 - 为执行记录添加执行环境字段
为 executions 表添加 environment_id 字段，记录每次执行实际使用的环境
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

        # 检查 executions 表的 environment_id 字段是否已存在
        cursor.execute("PRAGMA table_info(executions)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'environment_id' in columns:
            print("executions.environment_id 字段已存在，无需迁移")
            return True

        # 添加 environment_id 字段
        print("正在添加 executions.environment_id 字段...")
        cursor.execute("""
            ALTER TABLE executions
            ADD COLUMN environment_id INTEGER
            REFERENCES environments(id)
        """)

        conn.commit()
        print("✓ 迁移成功！executions.environment_id 字段已添加")

        # 验证迁移
        cursor.execute("PRAGMA table_info(executions)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"当前 executions 表字段: {', '.join(columns)}")

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

        # 检查字段是否存在
        cursor.execute("PRAGMA table_info(executions)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'environment_id' not in columns:
            print("executions.environment_id 字段不存在，无需回滚")
            return True

        print("警告: 此操作将删除 executions.environment_id 字段")
        response = input("确认继续？(yes/no): ")
        if response.lower() != 'yes':
            print("回滚已取消")
            return False

        print("正在删除 executions.environment_id 字段...")

        # SQLite 不支持直接删除列，需要重建表
        # 获取当前表的所有字段（除了 environment_id）
        cursor.execute("PRAGMA table_info(executions)")
        table_info = cursor.fetchall()

        column_names = []
        for col in table_info:
            col_name = col[1]
            if col_name != 'environment_id':
                column_names.append(col_name)

        # 开始事务
        cursor.execute("BEGIN TRANSACTION")

        # 创建临时表（不包含 environment_id）
        cursor.execute("""
            CREATE TABLE executions_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                script_id INTEGER NOT NULL,
                status VARCHAR(20) NOT NULL,
                params TEXT,
                output TEXT,
                error TEXT,
                log_file VARCHAR(255),
                start_time DATETIME,
                end_time DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (script_id) REFERENCES scripts(id)
            )
        """)

        # 复制数据
        cursor.execute(f"""
            INSERT INTO executions_temp ({', '.join(column_names)})
            SELECT {', '.join(column_names)} FROM executions
        """)

        # 删除旧表
        cursor.execute("DROP TABLE executions")

        # 重命名临时表
        cursor.execute("ALTER TABLE executions_temp RENAME TO executions")

        cursor.execute("COMMIT")
        print("✓ 回滚成功！executions.environment_id 字段已删除")

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

    parser = argparse.ArgumentParser(description='数据库迁移脚本 - 执行记录环境字段')
    parser.add_argument('action', choices=['migrate', 'rollback'],
                       help='迁移操作: migrate (应用迁移) 或 rollback (回滚迁移)')

    args = parser.parse_args()

    if args.action == 'migrate':
        success = migrate()
    else:
        success = rollback()

    sys.exit(0 if success else 1)
