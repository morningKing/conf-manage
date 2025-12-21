"""
数据库查看工具

快速查看数据库中的表和数据统计信息

使用方法：
    python view_database.py [数据库路径]

示例：
    python view_database.py                         # 查看当前数据库
    python view_database.py ../data/database.db     # 查看指定数据库
"""
import sys
import os
import sqlite3
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def view_database(db_path):
    """查看数据库信息"""
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return

    print("=" * 80)
    print(f"数据库: {db_path}")
    print("=" * 80)

    # 获取文件信息
    file_stat = os.stat(db_path)
    file_size = file_stat.st_size
    modified_time = datetime.fromtimestamp(file_stat.st_mtime)

    print(f"\n文件大小: {file_size / 1024 / 1024:.2f} MB")
    print(f"修改时间: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    print(f"\n数据库表: {len(tables)} 个")
    print("-" * 80)

    # 统计每个表的记录数
    total_records = 0
    table_stats = []

    for (table_name,) in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        total_records += count
        table_stats.append((table_name, count))

    # 按记录数排序
    table_stats.sort(key=lambda x: x[1], reverse=True)

    # 打印表统计
    print(f"{'表名':<35} {'记录数':>10}")
    print("-" * 80)

    for table_name, count in table_stats:
        if count > 0:
            print(f"{table_name:<35} {count:>10,}")

    print("-" * 80)
    print(f"{'总计':<35} {total_records:>10,}")

    # 打印详细表结构（可选）
    print("\n" + "=" * 80)
    print("表结构详情")
    print("=" * 80)

    for (table_name,) in tables:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        if columns:
            print(f"\n表: {table_name}")
            print(f"  {'列名':<25} {'类型':<15} {'非空':<5} {'默认值':<15} {'主键':<5}")
            print("  " + "-" * 70)

            for col in columns:
                col_id, col_name, col_type, not_null, default_value, pk = col
                not_null_str = '是' if not_null else '否'
                pk_str = '是' if pk else '否'
                default_str = str(default_value) if default_value is not None else ''

                print(f"  {col_name:<25} {col_type:<15} {not_null_str:<5} {default_str:<15} {pk_str:<5}")

    conn.close()

    print("\n" + "=" * 80)


def main():
    """主函数"""
    # 获取数据库路径
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # 默认路径
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, 'data', 'database.db')

    view_database(db_path)


if __name__ == '__main__':
    main()
