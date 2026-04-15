"""
数据库迁移脚本 - 将Categories迁移到Folders

此脚本将完成以下迁移：
1. 为scripts表添加folder_id字段
2. 将categories数据迁移到folders表（保留树形结构）
3. 将scripts.category_id数据映射到scripts.folder_id
4. 删除scripts.category_id字段（SQLite需要重建表）

运行方式：
    python backend/migrations/migrate_categories_to_folders.py
"""
import sqlite3
import os
import sys
import json
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config


def get_db_path():
    """获取数据库路径"""
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    return db_uri.replace('sqlite:///', '')


def backup_database(db_path):
    """备份数据库"""
    backup_path = db_path + '.backup_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"[OK] 数据库已备份到: {backup_path}")
    return backup_path


def check_migration_needed(db_path):
    """检查是否需要迁移"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查scripts表的字段
    cursor.execute("PRAGMA table_info(scripts)")
    columns = [col[1] for col in cursor.fetchall()]

    has_category_id = 'category_id' in columns
    has_folder_id = 'folder_id' in columns

    conn.close()

    if not has_category_id:
        print("[INFO] scripts表没有category_id字段，无需迁移")
        return False

    if has_folder_id:
        print("[INFO] scripts表已有folder_id字段")
        # 检查是否还有category_id字段（冗余）
        if has_category_id:
            print("[WARN] scripts表同时有folder_id和category_id字段，需要清理")
            return True
        return False

    print("[INFO] scripts表有category_id字段但没有folder_id字段，需要迁移")
    return True


def migrate(db_path):
    """执行迁移"""
    print("=" * 60)
    print("开始数据库迁移: Categories -> Folders")
    print("=" * 60)
    print()

    # 1. 备份数据库
    print("步骤1: 备份数据库")
    backup_path = backup_database(db_path)
    print()

    # 2. 检查迁移必要性
    print("步骤2: 检查迁移必要性")
    if not check_migration_needed(db_path):
        print("[INFO] 无需迁移，退出")
        return False
    print()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 3. 检查folders表是否存在
        print("步骤3: 检查folders表")
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='folders'
        """)
        if not cursor.fetchone():
            print("[ERROR] folders表不存在！请先创建folders表")
            conn.close()
            return False
        print("[OK] folders表存在")
        print()

        # 4. 添加folder_id字段到scripts表
        print("步骤4: 为scripts表添加folder_id字段")
        cursor.execute("PRAGMA table_info(scripts)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'folder_id' not in columns:
            cursor.execute("""
                ALTER TABLE scripts
                ADD COLUMN folder_id INTEGER
                REFERENCES folders(id)
            """)
            conn.commit()
            print("[OK] folder_id字段添加成功")
        else:
            print("[INFO] folder_id字段已存在")
        print()

        # 5. 迁移categories数据到folders
        print("步骤5: 迁移categories数据到folders")

        # 获取categories数据
        cursor.execute("SELECT id, name, color, icon, sort_order, created_at, updated_at FROM categories")
        categories = cursor.fetchall()

        print(f"[INFO] 找到 {len(categories)} 个分类")

        # 检查folders是否已有数据
        cursor.execute("SELECT COUNT(*) FROM folders")
        folders_count = cursor.fetchone()[0]

        if folders_count > 0:
            print(f"[WARN] folders表已有 {folders_count} 条数据")
            print("[INFO] 将尝试匹配现有数据而不是插入新数据")
        else:
            print("[INFO] folders表为空，开始插入数据")

            # 插入categories数据到folders（扁平结构，parent_id=NULL）
            for category in categories:
                cat_id, name, color, icon, sort_order, created_at, updated_at = category

                # 使用默认颜色如果color为空
                if not color:
                    color = '#E6A23C'

                # 使用默认sort_order如果为空
                if sort_order is None:
                    sort_order = 0

                cursor.execute("""
                    INSERT INTO folders (name, parent_id, color, sort_order, created_at, updated_at)
                    VALUES (?, NULL, ?, ?, ?, ?)
                """, (name, color, sort_order, created_at or datetime.now().isoformat(),
                      updated_at or datetime.now().isoformat()))

            conn.commit()
            print(f"[OK] 成功插入 {len(categories)} 条数据到folders表")
        print()

        # 6. 创建category_id到folder_id的映射
        print("步骤6: 创建category_id到folder_id的映射")

        # 获取映射关系（基于name和color匹配）
        cursor.execute("""
            SELECT c.id as category_id, f.id as folder_id
            FROM categories c
            LEFT JOIN folders f ON c.name = f.name AND c.color = f.color
        """)
        mapping = cursor.fetchall()

        mapping_dict = {}
        for category_id, folder_id in mapping:
            if folder_id:
                mapping_dict[category_id] = folder_id
            else:
                print(f"[WARN] Category ID {category_id} 无法匹配到folder")

        print(f"[INFO] 建立了 {len(mapping_dict)} 个映射关系")
        print()

        # 7. 更新scripts的folder_id
        print("步骤7: 更新scripts的folder_id")

        # 获取所有使用category_id的scripts
        cursor.execute("SELECT id, category_id FROM scripts WHERE category_id IS NOT NULL")
        scripts_with_category = cursor.fetchall()

        if scripts_with_category:
            print(f"[INFO] 找到 {len(scripts_with_category)} 个脚本使用category_id")

            updated_count = 0
            for script_id, category_id in scripts_with_category:
                if category_id in mapping_dict:
                    folder_id = mapping_dict[category_id]
                    cursor.execute("""
                        UPDATE scripts SET folder_id = ? WHERE id = ?
                    """, (folder_id, script_id))
                    updated_count += 1
                else:
                    print(f"[WARN] Script ID {script_id} 的 category_id {category_id} 无法映射")

            conn.commit()
            print(f"[OK] 成功更新 {updated_count} 个脚本的folder_id")
        else:
            print("[INFO] 没有脚本使用category_id字段")
        print()

        # 8. 删除scripts表的category_id字段
        print("步骤8: 删除scripts表的category_id字段")
        print("[INFO] SQLite不支持直接删除列，需要重建表")

        # 获取当前表结构（不包括category_id）
        cursor.execute("PRAGMA table_info(scripts)")
        table_info = cursor.fetchall()

        # 构建新表定义
        columns_def = []
        column_names = []
        for col in table_info:
            col_name = col[1]
            if col_name != 'category_id':  # 排除category_id
                col_type = col[2]
                col_notnull = "NOT NULL" if col[3] else ""
                col_default = f"DEFAULT {col[4]}" if col[4] else ""
                col_pk = "PRIMARY KEY" if col[5] else ""

                columns_def.append(f"{col_name} {col_type} {col_notnull} {col_default} {col_pk}".strip())
                column_names.append(col_name)

        # 开始事务
        cursor.execute("BEGIN TRANSACTION")

        # 创建临时表
        print("[INFO] 创建临时表...")
        create_table_sql = f"""
            CREATE TABLE scripts_temp (
                {', '.join(columns_def)},
                FOREIGN KEY (environment_id) REFERENCES environments(id),
                FOREIGN KEY (folder_id) REFERENCES folders(id)
            )
        """
        cursor.execute(create_table_sql)

        # 复制数据
        print("[INFO] 复制数据...")
        insert_sql = f"""
            INSERT INTO scripts_temp ({', '.join(column_names)})
            SELECT {', '.join(column_names)} FROM scripts
        """
        cursor.execute(insert_sql)

        # 删除旧表
        print("[INFO] 删除旧表...")
        cursor.execute("DROP TABLE scripts")

        # 重命名临时表
        print("[INFO] 重命名临时表...")
        cursor.execute("ALTER TABLE scripts_temp RENAME TO scripts")

        # 提交事务
        cursor.execute("COMMIT")
        conn.commit()

        print("[OK] scripts表重建完成，category_id字段已删除")
        print()

        # 9. 验证迁移结果
        print("步骤9: 验证迁移结果")

        cursor.execute("PRAGMA table_info(scripts)")
        script_columns = [col[1] for col in cursor.fetchall()]
        print(f"[INFO] scripts表字段: {', '.join(script_columns)}")

        has_folder_id = 'folder_id' in script_columns
        has_category_id = 'category_id' in script_columns

        if has_folder_id and not has_category_id:
            print("[OK] ✓ scripts表结构正确: 有folder_id，无category_id")
        else:
            print("[ERROR] ✗ scripts表结构异常")
            return False

        # 检查数据
        cursor.execute("SELECT COUNT(*) FROM folders")
        folders_count = cursor.fetchone()[0]
        print(f"[INFO] folders表数据: {folders_count} 条")

        cursor.execute("SELECT COUNT(*) FROM scripts WHERE folder_id IS NOT NULL")
        scripts_with_folder = cursor.fetchone()[0]
        print(f"[INFO] 使用folder_id的脚本: {scripts_with_folder} 个")

        print()

        # 10. (可选) 保留categories表作为备份
        print("步骤10: 保留categories表")
        print("[INFO] categories表已保留作为备份")
        print("[INFO] 如确认迁移成功，可手动删除: DROP TABLE categories;")
        print()

        conn.close()

        print("=" * 60)
        print("[SUCCESS] 迁移完成！")
        print("=" * 60)
        print()
        print("后续步骤:")
        print("1. 运行 test_db_migration.py 验证迁移结果")
        print("2. 启动应用测试功能")
        print("3. 确认无问题后可删除categories表")
        print(f"4. 备份文件位于: {backup_path}")

        return True

    except Exception as e:
        print(f"[ERROR] 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        conn.close()
        print()
        print(f"[INFO] 数据库已自动回滚，备份文件位于: {backup_path}")
        return False


def rollback(db_path):
    """回滚迁移（从备份恢复）"""
    print("=" * 60)
    print("回滚迁移")
    print("=" * 60)
    print()

    # 查找最近的备份文件
    db_dir = os.path.dirname(db_path)
    backup_files = [f for f in os.listdir(db_dir) if f.startswith('database.db.backup_')]

    if not backup_files:
        print("[ERROR] 未找到备份文件")
        return False

    # 按时间排序，取最新的
    backup_files.sort(reverse=True)
    latest_backup = os.path.join(db_dir, backup_files[0])

    print(f"[INFO] 找到备份文件: {latest_backup}")

    # 确认回滚
    response = input("确认从备份恢复数据库？(yes/no): ")
    if response.lower() != 'yes':
        print("[INFO] 回滚已取消")
        return False

    # 恢复备份
    import shutil
    shutil.copy2(latest_backup, db_path)
    print(f"[OK] 数据库已从备份恢复")
    print()

    return True


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='数据库迁移脚本 - Categories转Folders')
    parser.add_argument('action', choices=['migrate', 'rollback'],
                        help='迁移操作: migrate (执行迁移) 或 rollback (从备份恢复)')

    args = parser.parse_args()

    db_path = get_db_path()
    print(f"[INFO] 数据库路径: {db_path}")
    print()

    if not os.path.exists(db_path):
        print(f"[ERROR] 数据库文件不存在: {db_path}")
        sys.exit(1)

    if args.action == 'migrate':
        success = migrate(db_path)
    else:
        success = rollback(db_path)

    sys.exit(0 if success else 1)