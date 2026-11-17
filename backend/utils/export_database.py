#!/usr/bin/env python3
"""
数据库导出工具（PostgreSQL）

功能：
- export_database: 通过 pg_dump 导出数据库为 SQL 文件
- get_database_info: 通过 SQLAlchemy 反射获取表清单与记录数
"""
import os
import sys
import shutil
import datetime
import subprocess

# 将backend目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from utils.safe_io import safe_open


def _database_url():
    """从配置解析数据库连接信息（密码不落入日志）"""
    from sqlalchemy.engine import make_url
    return make_url(Config.SQLALCHEMY_DATABASE_URI)


def export_database(output_file=None):
    """
    使用 pg_dump 导出数据库为 SQL 文件

    Args:
        output_file: 输出文件路径，如果为None则自动生成

    Returns:
        str: 导出的文件路径
    """
    pg_dump = shutil.which('pg_dump')
    if not pg_dump:
        raise RuntimeError('未找到 pg_dump，请安装 PostgreSQL 客户端工具并确保其在 PATH 中')

    if output_file is None:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(Config.BACKUPS_DIR, f'database_export_{timestamp}.sql')
    else:
        # 指定输出文件时，约束其必须位于备份目录内，防止任意路径写入
        output_file = os.path.join(Config.BACKUPS_DIR, os.path.basename(output_file))

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    url = _database_url()
    env = os.environ.copy()
    if url.password:
        env['PGPASSWORD'] = url.password

    print(f"开始导出数据库: {url.database}@{url.host}:{url.port}")
    print(f"输出文件: {output_file}")
    print("-" * 70)

    # 参数列表形式调用 pg_dump（shell=False），无 shell 字符串拼接
    with safe_open(output_file, 'w', base_dir=Config.BACKUPS_DIR, encoding='utf-8') as f:
        result = subprocess.run([
            pg_dump,
            '--host', str(url.host or 'localhost'),
            '--port', str(url.port or 5432),
            '--username', str(url.username or 'postgres'),
            '--format', 'plain',
            '--no-password',
            str(url.database),
        ], stdout=f, stderr=subprocess.PIPE, env=env, shell=False)

    if result.returncode != 0:
        # 导出失败时清理不完整的文件
        try:
            os.remove(output_file)
        except OSError:
            pass
        stderr_text = result.stderr.decode('utf-8', errors='replace').strip()
        raise RuntimeError(f'pg_dump 导出失败: {stderr_text}')

    file_size = os.path.getsize(output_file)
    print("-" * 70)
    print("✓ 导出完成")
    print(f"✓ 文件大小: {file_size / (1024 * 1024):.2f} MB ({file_size:,} 字节)")
    print(f"✓ 保存位置: {output_file}")

    return output_file


def get_database_info():
    """
    获取数据库信息（表清单与记录数）

    通过 SQLAlchemy 反射取表对象并用 select(func.count()) 统计，
    不拼接任何原生 SQL 字符串。
    """
    from sqlalchemy import MetaData, func, select
    from models import db

    url = _database_url()

    metadata = MetaData()
    metadata.reflect(bind=db.engine)

    info = {
        'database': str(url.database),
        'host': str(url.host),
        'port': url.port or 5432,
        'tables': [],
        'total_records': 0,
    }

    for name in sorted(metadata.tables):
        table = metadata.tables[name]
        count = db.session.execute(select(func.count()).select_from(table)).scalar() or 0
        info['tables'].append({
            'name': name,
            'count': count
        })
        info['total_records'] += count

    return info


def main():
    """主函数"""
    print("=" * 70)
    print("数据库导出工具（PostgreSQL）")
    print("=" * 70)
    print()

    try:
        info = get_database_info()
        print(f"数据库: {info['database']}@{info['host']}:{info['port']}")
        print(f"总记录数: {info['total_records']}")
        print("\n数据表统计:")
        for table in info['tables']:
            print(f"  - {table['name']}: {table['count']} 条记录")
        print()

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
