"""
数据库迁移测试脚本

用于测试迁移工具是否能正常工作
"""
import os
import sys
import sqlite3
import shutil
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def create_test_database():
    """创建测试用的老数据库"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_db_path = os.path.join(base_dir, 'data', 'test_old_database.db')

    # 删除已存在的测试数据库
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    print(f"创建测试数据库: {test_db_path}")

    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    # 创建测试表和数据
    # Category 表
    cursor.execute('''
        CREATE TABLE category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL
        )
    ''')
    cursor.execute(
        "INSERT INTO category (name, description, created_at) VALUES (?, ?, ?)",
        ('测试分类1', '测试描述1', datetime.utcnow().isoformat())
    )
    cursor.execute(
        "INSERT INTO category (name, description, created_at) VALUES (?, ?, ?)",
        ('测试分类2', '测试描述2', datetime.utcnow().isoformat())
    )

    # Tag 表
    cursor.execute('''
        CREATE TABLE tag (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    cursor.execute(
        "INSERT INTO tag (name, created_at) VALUES (?, ?)",
        ('测试标签1', datetime.utcnow().isoformat())
    )
    cursor.execute(
        "INSERT INTO tag (name, created_at) VALUES (?, ?)",
        ('测试标签2', datetime.utcnow().isoformat())
    )

    # Environment 表
    cursor.execute('''
        CREATE TABLE environment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            value TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL
        )
    ''')
    cursor.execute(
        "INSERT INTO environment (name, value, description, created_at) VALUES (?, ?, ?, ?)",
        ('TEST_VAR', 'test_value', '测试环境变量', datetime.utcnow().isoformat())
    )

    # Script 表
    cursor.execute('''
        CREATE TABLE script (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category_id INTEGER,
            script_type TEXT DEFAULT 'python',
            content TEXT NOT NULL,
            params_schema TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            version INTEGER DEFAULT 1
        )
    ''')
    cursor.execute('''
        INSERT INTO script
        (name, description, category_id, script_type, content, created_at, updated_at, version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        '测试脚本1',
        '这是一个测试脚本',
        1,
        'python',
        'print("Hello World")',
        datetime.utcnow().isoformat(),
        datetime.utcnow().isoformat(),
        1
    ))

    # Execution 表
    cursor.execute('''
        CREATE TABLE execution (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            script_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            output TEXT,
            error TEXT,
            params TEXT,
            created_at TEXT NOT NULL,
            started_at TEXT,
            finished_at TEXT,
            progress INTEGER DEFAULT 0,
            stage TEXT DEFAULT 'pending'
        )
    ''')
    cursor.execute('''
        INSERT INTO execution
        (script_id, status, output, created_at, progress, stage)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        1,
        'success',
        'Hello World',
        datetime.utcnow().isoformat(),
        100,
        'completed'
    ))

    conn.commit()
    conn.close()

    print("✓ 测试数据库创建完成")
    print(f"  - 2 个分类")
    print(f"  - 2 个标签")
    print(f"  - 1 个环境变量")
    print(f"  - 1 个脚本")
    print(f"  - 1 条执行记录")

    return test_db_path


def test_migration():
    """测试迁移功能"""
    print("=" * 60)
    print("数据库迁移测试")
    print("=" * 60)
    print()

    # 步骤1: 创建测试数据库
    print("步骤1: 创建测试数据库")
    test_db_path = create_test_database()
    print()

    # 步骤2: 备份当前数据库
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    current_db_path = os.path.join(base_dir, 'data', 'database.db')
    backup_db_path = None

    if os.path.exists(current_db_path):
        print("步骤2: 备份当前数据库")
        backup_db_path = current_db_path + '.test_backup'
        shutil.copy2(current_db_path, backup_db_path)
        print(f"✓ 已备份到: {backup_db_path}")
        print()

    # 步骤3: 执行迁移
    print("步骤3: 执行迁移")
    print(f"运行命令: python migrate_database.py {test_db_path}")
    print()

    # 导入并运行迁移
    from migrate_database import DatabaseMigration
    from app import create_app

    # 删除现有数据库
    if os.path.exists(current_db_path):
        os.remove(current_db_path)

    app = create_app()
    migration = DatabaseMigration(test_db_path, app)
    migration.run()

    print()

    # 步骤4: 验证迁移结果
    print("步骤4: 验证迁移结果")
    from view_database import view_database
    view_database(current_db_path)
    print()

    # 步骤5: 清理
    print("步骤5: 清理测试文件")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"✓ 已删除测试数据库: {test_db_path}")

    # 恢复备份
    if backup_db_path and os.path.exists(backup_db_path):
        if os.path.exists(current_db_path):
            os.remove(current_db_path)
        shutil.move(backup_db_path, current_db_path)
        print(f"✓ 已恢复原数据库")

    print()
    print("=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)


if __name__ == '__main__':
    test_migration()
