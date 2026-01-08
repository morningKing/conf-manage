#!/usr/bin/env python3
"""
系统备份工具

功能：备份脚本文件、执行空间、工作流目录、日志文件等
"""
import os
import sys
import shutil
import datetime
import tarfile

# 将backend目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config


def get_directory_size(path):
    """计算目录大小"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
    except Exception as e:
        print(f"  ⚠ 计算大小失败: {e}")
    return total_size


def count_files(path):
    """计算目录中的文件数"""
    total_files = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            total_files += len(filenames)
    except:
        pass
    return total_files


def backup_system(backup_name=None, include_logs=False, include_execution_spaces=True):
    """
    备份系统文件

    Args:
        backup_name: 备份文件名（不含扩展名），如果为None则自动生成
        include_logs: 是否包含日志文件
        include_execution_spaces: 是否包含执行空间

    Returns:
        str: 备份文件路径
    """
    # 生成备份文件名
    if not backup_name:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'system_backup_{timestamp}'

    backup_file = os.path.join(Config.BACKUPS_DIR, f'{backup_name}.tar.gz')

    # 确保备份目录存在
    os.makedirs(Config.BACKUPS_DIR, exist_ok=True)

    print("=" * 70)
    print("系统备份工具")
    print("=" * 70)
    print()

    # 定义需要备份的目录
    backup_items = []

    # 1. 脚本目录
    if os.path.exists(Config.SCRIPTS_DIR):
        backup_items.append({
            'path': Config.SCRIPTS_DIR,
            'arcname': 'scripts',
            'name': '脚本文件'
        })

    # 2. 数据目录
    if os.path.exists(Config.DATA_DIR):
        backup_items.append({
            'path': Config.DATA_DIR,
            'arcname': 'data',
            'name': '数据文件'
        })

    # 3. 执行空间
    if include_execution_spaces:
        if os.path.exists(Config.EXECUTION_SPACES_DIR):
            backup_items.append({
                'path': Config.EXECUTION_SPACES_DIR,
                'arcname': 'execution_spaces',
                'name': '执行空间'
            })

        # 工作流执行空间
        workflow_spaces = os.path.join(os.path.dirname(Config.BASE_DIR), 'workflow_execution_spaces')
        if os.path.exists(workflow_spaces):
            backup_items.append({
                'path': workflow_spaces,
                'arcname': 'workflow_execution_spaces',
                'name': '工作流执行空间'
            })

        # 工作空间
        workspaces = os.path.join(os.path.dirname(Config.BASE_DIR), 'workspaces')
        if os.path.exists(workspaces):
            backup_items.append({
                'path': workspaces,
                'arcname': 'workspaces',
                'name': '工作空间'
            })

    # 4. 日志文件
    if include_logs and os.path.exists(Config.LOGS_DIR):
        backup_items.append({
            'path': Config.LOGS_DIR,
            'arcname': 'logs',
            'name': '日志文件'
        })

    # 5. 数据库文件
    if os.path.exists(Config.DATABASE_PATH):
        backup_items.append({
            'path': Config.DATABASE_PATH,
            'arcname': 'database/database.db',
            'name': '数据库文件'
        })

    # 显示备份项统计
    print("备份项目统计:")
    total_size = 0
    total_files = 0

    for item in backup_items:
        if os.path.isfile(item['path']):
            size = os.path.getsize(item['path'])
            files = 1
        else:
            size = get_directory_size(item['path'])
            files = count_files(item['path'])

        total_size += size
        total_files += files

        size_mb = size / (1024 * 1024)
        print(f"  ✓ {item['name']}: {files} 个文件, {size_mb:.2f} MB")

    print(f"\n总计: {total_files} 个文件, {total_size / (1024*1024):.2f} MB")
    print()

    # 创建备份
    print(f"开始创建备份: {backup_file}")
    print("-" * 70)

    with tarfile.open(backup_file, 'w:gz') as tar:
        for item in backup_items:
            print(f"  正在备份: {item['name']}...")
            try:
                tar.add(item['path'], arcname=item['arcname'])
            except Exception as e:
                print(f"  ⚠ 备份失败: {e}")

    # 获取备份文件大小
    backup_size = os.path.getsize(backup_file)
    backup_size_mb = backup_size / (1024 * 1024)
    compression_ratio = (1 - backup_size / total_size) * 100 if total_size > 0 else 0

    print("-" * 70)
    print(f"✓ 备份完成")
    print(f"✓ 备份文件: {backup_file}")
    print(f"✓ 备份大小: {backup_size_mb:.2f} MB ({backup_size:,} 字节)")
    print(f"✓ 压缩率: {compression_ratio:.1f}%")
    print()

    return backup_file


def list_backups():
    """列出所有备份文件"""
    if not os.path.exists(Config.BACKUPS_DIR):
        return []

    backups = []
    for filename in os.listdir(Config.BACKUPS_DIR):
        if filename.endswith('.tar.gz') or filename.endswith('.sql'):
            filepath = os.path.join(Config.BACKUPS_DIR, filename)
            stat = os.stat(filepath)
            backups.append({
                'name': filename,
                'path': filepath,
                'size': stat.st_size,
                'created': datetime.datetime.fromtimestamp(stat.st_mtime)
            })

    # 按创建时间倒序排序
    backups.sort(key=lambda x: x['created'], reverse=True)
    return backups


def delete_old_backups(keep_days=30):
    """删除旧备份文件"""
    if not os.path.exists(Config.BACKUPS_DIR):
        return 0

    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=keep_days)
    deleted_count = 0

    for filename in os.listdir(Config.BACKUPS_DIR):
        if filename.endswith('.tar.gz') or filename.endswith('.sql'):
            filepath = os.path.join(Config.BACKUPS_DIR, filename)
            file_time = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))

            if file_time < cutoff_date:
                try:
                    os.remove(filepath)
                    deleted_count += 1
                    print(f"  ✓ 已删除旧备份: {filename}")
                except Exception as e:
                    print(f"  ✗ 删除失败: {filename} - {e}")

    return deleted_count


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='系统备份工具')
    parser.add_argument('--name', help='备份文件名（不含扩展名）')
    parser.add_argument('--include-logs', action='store_true', help='包含日志文件')
    parser.add_argument('--exclude-executions', action='store_true', help='排除执行空间')
    parser.add_argument('--list', action='store_true', help='列出所有备份')
    parser.add_argument('--clean', type=int, metavar='DAYS', help='删除N天前的旧备份')

    args = parser.parse_args()

    try:
        # 列出备份
        if args.list:
            backups = list_backups()
            if not backups:
                print("没有找到备份文件")
                return 0

            print("=" * 70)
            print("备份文件列表")
            print("=" * 70)
            for backup in backups:
                size_mb = backup['size'] / (1024 * 1024)
                created = backup['created'].strftime('%Y-%m-%d %H:%M:%S')
                print(f"\n文件名: {backup['name']}")
                print(f"  大小: {size_mb:.2f} MB")
                print(f"  创建时间: {created}")
            return 0

        # 清理旧备份
        if args.clean:
            print(f"清理 {args.clean} 天前的旧备份...")
            deleted = delete_old_backups(args.clean)
            print(f"\n✓ 已删除 {deleted} 个旧备份文件")
            return 0

        # 执行备份
        backup_file = backup_system(
            backup_name=args.name,
            include_logs=args.include_logs,
            include_execution_spaces=not args.exclude_executions
        )

        print("=" * 70)
        print("备份成功完成!")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"\n✗ 备份失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
