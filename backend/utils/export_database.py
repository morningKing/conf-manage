#!/usr/bin/env python3
"""
数据库导出工具

功能：导出SQLite数据库的建表语句和数据为SQL文件
"""
import os
import sys
import sqlite3
import datetime

# 将backend目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config


def export_database(output_file=None):
    """
    导出数据库为SQL文件

    Args:
        output_file: 输出文件路径，如果为None则自动生成

    Returns:
        str: 导出的文件路径
    """
    # 生成输出文件名
    if output_file is None:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(Config.BACKUPS_DIR, f'database_export_{timestamp}.sql')

    # 确保备份目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # 连接数据库
    db_path = Config.DATABASE_PATH

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"数据库文件不存在: {db_path}")

    conn = sqlite3.connect(db_path)

    print(f"开始导出数据库: {db_path}")
    print(f"输出文件: {output_file}")
    print("-" * 70)

    # 打开输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        # 写入文件头注释
        f.write("-- " + "=" * 68 + "\n")
        f.write(f"-- 数据库导出文件\n")
        f.write(f"-- 导出时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- 数据库: {db_path}\n")
        f.write("-- " + "=" * 68 + "\n\n")

        # 导出所有内容
        for line in conn.iterdump():
            # 过滤掉一些不需要的语句
            if line.startswith('BEGIN TRANSACTION') or line.startswith('COMMIT'):
                continue

            f.write(f"{line}\n")

        f.write("\n-- 导出完成\n")

    conn.close()

    # 获取文件大小
    file_size = os.path.getsize(output_file)
    file_size_mb = file_size / (1024 * 1024)

    print("-" * 70)
    print(f"✓ 导出完成")
    print(f"✓ 文件大小: {file_size_mb:.2f} MB ({file_size:,} 字节)")
    print(f"✓ 保存位置: {output_file}")

    return output_file


def get_database_info():
    """获取数据库信息"""
    db_path = Config.DATABASE_PATH

    if not os.path.exists(db_path):
        return None

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    info = {
        'path': db_path,
        'size': os.path.getsize(db_path),
        'tables': []
    }

    # 获取每个表的记录数
    for (table_name,) in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        info['tables'].append({
            'name': table_name,
            'count': count
        })

    conn.close()
    return info


def main():
    """主函数"""
    print("=" * 70)
    print("数据库导出工具")
    print("=" * 70)
    print()

    try:
        # 显示数据库信息
        info = get_database_info()
        if info:
            print(f"数据库路径: {info['path']}")
            print(f"数据库大小: {info['size'] / (1024*1024):.2f} MB")
            print(f"\n数据表统计:")
            for table in info['tables']:
                print(f"  - {table['name']}: {table['count']} 条记录")
            print()

        # 执行导出
        output_file = export_database()

        print("\n" + "=" * 70)
        print("导出成功完成!")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"\n✗ 导出失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
