"""
数据库迁移脚本 - 为执行记录添加进度和阶段字段
添加 progress, stage, pid 字段用于实时进度显示和执行中断
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

        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(executions)")
        columns = [col[1] for col in cursor.fetchall()]

        fields_to_add = []
        if 'progress' not in columns:
            fields_to_add.append(('progress', 'INTEGER DEFAULT 0'))
        if 'stage' not in columns:
            fields_to_add.append(('stage', "VARCHAR(50) DEFAULT 'pending'"))
        if 'pid' not in columns:
            fields_to_add.append(('pid', 'INTEGER'))

        if not fields_to_add:
            print("所有字段已存在，无需迁移")
            return True

        # 添加字段
        print(f"正在添加字段: {', '.join([f[0] for f in fields_to_add])}...")
        for field_name, field_type in fields_to_add:
            cursor.execute(f"ALTER TABLE executions ADD COLUMN {field_name} {field_type}")
            print(f"[OK] 已添加字段: {field_name}")

        conn.commit()
        print("[OK] 迁移成功！进度相关字段已添加")

        # 验证迁移
        cursor.execute("PRAGMA table_info(executions)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"当前 executions 表字段: {', '.join(columns)}")

        conn.close()
        return True

    except Exception as e:
        print(f"[ERROR] 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def rollback():
    """回滚迁移"""
    print("警告: SQLite 不支持直接删除列")
    print("如需回滚，请手动重建表或使用备份恢复数据库")
    return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='数据库迁移脚本 - 执行进度字段')
    parser.add_argument('action', choices=['migrate', 'rollback'],
                       help='迁移操作: migrate (应用迁移) 或 rollback (回滚迁移)')

    args = parser.parse_args()

    if args.action == 'migrate':
        success = migrate()
    else:
        success = rollback()

    sys.exit(0 if success else 1)
