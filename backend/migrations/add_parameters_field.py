"""
数据库迁移脚本 - 添加参数字段
运行此脚本为 scripts 表添加 parameters 字段
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

        # 检查 parameters 字段是否已存在
        cursor.execute("PRAGMA table_info(scripts)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'parameters' in columns:
            print("parameters 字段已存在，无需迁移")
            return True

        # 添加 parameters 字段
        print("正在添加 parameters 字段...")
        cursor.execute("""
            ALTER TABLE scripts
            ADD COLUMN parameters TEXT
        """)

        conn.commit()
        print("✓ 迁移成功！parameters 字段已添加到 scripts 表")

        # 验证迁移
        cursor.execute("PRAGMA table_info(scripts)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"当前 scripts 表字段: {', '.join(columns)}")

        conn.close()
        return True

    except Exception as e:
        print(f"✗ 迁移失败: {str(e)}")
        return False


def rollback():
    """回滚迁移（删除 parameters 字段）"""
    # 从SQLALCHEMY_DATABASE_URI提取数据库路径
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    db_path = db_uri.replace('sqlite:///', '')

    print(f"正在连接数据库: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查字段是否存在
        cursor.execute("PRAGMA table_info(scripts)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'parameters' not in columns:
            print("parameters 字段不存在，无需回滚")
            return True

        print("警告: SQLite 不支持直接删除列")
        print("需要重建表来删除 parameters 字段")

        # 获取表结构（不包括 parameters）
        cursor.execute("PRAGMA table_info(scripts)")
        table_info = cursor.fetchall()

        # 创建新表（不包含 parameters 字段）
        columns_def = []
        column_names = []
        for col in table_info:
            col_name = col[1]
            if col_name != 'parameters':
                col_type = col[2]
                col_notnull = "NOT NULL" if col[3] else ""
                col_default = f"DEFAULT {col[4]}" if col[4] else ""
                col_pk = "PRIMARY KEY" if col[5] else ""

                columns_def.append(f"{col_name} {col_type} {col_notnull} {col_default} {col_pk}".strip())
                column_names.append(col_name)

        # 开始事务
        cursor.execute("BEGIN TRANSACTION")

        # 创建临时表
        cursor.execute(f"""
            CREATE TABLE scripts_temp (
                {', '.join(columns_def)}
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

        # 提交事务
        conn.commit()

        print("✓ 回滚成功！parameters 字段已从 scripts 表删除")

        conn.close()
        return True

    except Exception as e:
        print(f"✗ 回滚失败: {str(e)}")
        if conn:
            conn.rollback()
        return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='数据库迁移脚本')
    parser.add_argument('action', choices=['migrate', 'rollback'],
                       help='迁移操作: migrate (应用迁移) 或 rollback (回滚迁移)')

    args = parser.parse_args()

    if args.action == 'migrate':
        success = migrate()
    else:
        success = rollback()

    sys.exit(0 if success else 1)
