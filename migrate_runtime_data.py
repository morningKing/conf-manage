#!/usr/bin/env python3
"""
项目数据迁移脚本
用于将一个项目的运行时数据（日志、执行空间、数据库等）迁移到新的项目目录中

使用方式:
    python migrate_runtime_data.py --source /path/to/source/project --target /path/to/target/project [--skip-db]

参数:
    --source: 源项目目录路径（包含运行时数据的项目）
    --target: 目标项目目录路径（新项目）
    --skip-db: (可选) 跳过数据库迁移，仅迁移日志和执行空间
    --skip-logs: (可选) 跳过日志迁移
    --skip-spaces: (可选) 跳过执行空间迁移
    --dry-run: (可选) 模拟迁移，不实际复制文件
"""

import os
import sys
import shutil
import argparse
import json
from datetime import datetime
from pathlib import Path
import sqlite3


class RuntimeDataMigrator:
    """运行时数据迁移工具"""

    def __init__(self, source_dir, target_dir, skip_db=False, skip_logs=False, skip_spaces=False, dry_run=False):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.skip_db = skip_db
        self.skip_logs = skip_logs
        self.skip_spaces = skip_spaces
        self.dry_run = dry_run
        self.log_entries = []
        self.migration_summary = {
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'source': str(source_dir),
            'target': str(target_dir),
            'logs_migrated': 0,
            'execution_spaces_migrated': 0,
            'uploads_migrated': 0,
            'database_migrated': False,
            'total_size': 0,
            'errors': []
        }

    def log(self, message, level='INFO'):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f'[{timestamp}] [{level}] {message}'
        print(log_message)
        self.log_entries.append(log_message)

    def validate_paths(self):
        """验证源和目标目录"""
        self.log('验证目录路径...')

        # 检查源目录
        if not self.source_dir.exists():
            self.log(f'源目录不存在: {self.source_dir}', 'ERROR')
            return False

        # 检查源目录是否是项目目录
        if not (self.source_dir / 'backend').exists():
            self.log(f'源目录不是有效的项目目录（缺少backend文件夹）: {self.source_dir}', 'ERROR')
            return False

        # 检查目标目录
        if not self.target_dir.exists():
            self.log(f'目标目录不存在: {self.target_dir}', 'ERROR')
            return False

        if not (self.target_dir / 'backend').exists():
            self.log(f'目标目录不是有效的项目目录（缺少backend文件夹）: {self.target_dir}', 'ERROR')
            return False

        self.log('✓ 目录验证成功', 'SUCCESS')
        return True

    def migrate_logs(self):
        """迁移日志文件"""
        if self.skip_logs:
            self.log('跳过日志迁移', 'INFO')
            return True

        self.log('开始迁移日志文件...')

        source_logs = self.source_dir / 'logs'
        target_logs = self.target_dir / 'logs'

        if not source_logs.exists():
            self.log(f'源日志目录不存在: {source_logs}', 'WARNING')
            return True

        try:
            # 创建目标日志目录
            if not self.dry_run:
                target_logs.mkdir(parents=True, exist_ok=True)

            log_files = list(source_logs.glob('*.log'))
            self.log(f'找到 {len(log_files)} 个日志文件')

            for log_file in log_files:
                try:
                    target_file = target_logs / log_file.name
                    file_size = log_file.stat().st_size

                    if self.dry_run:
                        self.log(f'  [模拟] 复制日志: {log_file.name} ({self._format_size(file_size)})', 'INFO')
                    else:
                        shutil.copy2(log_file, target_file)
                        self.log(f'  ✓ 复制日志: {log_file.name} ({self._format_size(file_size)})', 'INFO')

                    self.migration_summary['total_size'] += file_size
                    self.migration_summary['logs_migrated'] += 1

                except Exception as e:
                    error_msg = f'复制日志失败: {log_file.name} - {str(e)}'
                    self.log(error_msg, 'ERROR')
                    self.migration_summary['errors'].append(error_msg)

            self.log(f'✓ 日志迁移完成，共迁移 {self.migration_summary["logs_migrated"]} 个文件', 'SUCCESS')
            return True

        except Exception as e:
            error_msg = f'日志迁移失败: {str(e)}'
            self.log(error_msg, 'ERROR')
            self.migration_summary['errors'].append(error_msg)
            return False

    def migrate_execution_spaces(self):
        """迁移执行空间"""
        if self.skip_spaces:
            self.log('跳过执行空间迁移', 'INFO')
            return True

        self.log('开始迁移执行空间...')

        source_spaces = self.source_dir / 'execution_spaces'
        target_spaces = self.target_dir / 'execution_spaces'

        if not source_spaces.exists():
            self.log(f'源执行空间目录不存在: {source_spaces}', 'WARNING')
            return True

        try:
            if not self.dry_run:
                target_spaces.mkdir(parents=True, exist_ok=True)

            space_dirs = [d for d in source_spaces.iterdir() if d.is_dir()]
            self.log(f'找到 {len(space_dirs)} 个执行空间目录')

            for space_dir in space_dirs:
                try:
                    target_space = target_spaces / space_dir.name
                    space_size = self._get_dir_size(space_dir)

                    if self.dry_run:
                        self.log(f'  [模拟] 复制执行空间: {space_dir.name} ({self._format_size(space_size)})', 'INFO')
                    else:
                        if target_space.exists():
                            shutil.rmtree(target_space)
                        shutil.copytree(space_dir, target_space)
                        self.log(f'  ✓ 复制执行空间: {space_dir.name} ({self._format_size(space_size)})', 'INFO')

                    self.migration_summary['total_size'] += space_size
                    self.migration_summary['execution_spaces_migrated'] += 1

                except Exception as e:
                    error_msg = f'复制执行空间失败: {space_dir.name} - {str(e)}'
                    self.log(error_msg, 'ERROR')
                    self.migration_summary['errors'].append(error_msg)

            self.log(f'✓ 执行空间迁移完成，共迁移 {self.migration_summary["execution_spaces_migrated"]} 个目录', 'SUCCESS')
            return True

        except Exception as e:
            error_msg = f'执行空间迁移失败: {str(e)}'
            self.log(error_msg, 'ERROR')
            self.migration_summary['errors'].append(error_msg)
            return False

    def migrate_uploads(self):
        """迁移上传的文件"""
        self.log('开始迁移上传文件...')

        source_uploads = self.source_dir / 'data' / 'uploads'
        target_uploads = self.target_dir / 'data' / 'uploads'

        if not source_uploads.exists():
            self.log(f'源上传文件目录不存在: {source_uploads}', 'WARNING')
            return True

        try:
            if not self.dry_run:
                target_uploads.mkdir(parents=True, exist_ok=True)

            upload_files = list(source_uploads.glob('*'))
            self.log(f'找到 {len(upload_files)} 个上传文件')

            for upload_file in upload_files:
                try:
                    target_file = target_uploads / upload_file.name

                    if upload_file.is_file():
                        file_size = upload_file.stat().st_size
                        if self.dry_run:
                            self.log(f'  [模拟] 复制文件: {upload_file.name} ({self._format_size(file_size)})', 'INFO')
                        else:
                            shutil.copy2(upload_file, target_file)
                            self.log(f'  ✓ 复制文件: {upload_file.name} ({self._format_size(file_size)})', 'INFO')
                        self.migration_summary['total_size'] += file_size

                    elif upload_file.is_dir():
                        dir_size = self._get_dir_size(upload_file)
                        if self.dry_run:
                            self.log(f'  [模拟] 复制目录: {upload_file.name} ({self._format_size(dir_size)})', 'INFO')
                        else:
                            if target_file.exists():
                                shutil.rmtree(target_file)
                            shutil.copytree(upload_file, target_file)
                            self.log(f'  ✓ 复制目录: {upload_file.name} ({self._format_size(dir_size)})', 'INFO')
                        self.migration_summary['total_size'] += dir_size

                    self.migration_summary['uploads_migrated'] += 1

                except Exception as e:
                    error_msg = f'复制上传文件失败: {upload_file.name} - {str(e)}'
                    self.log(error_msg, 'ERROR')
                    self.migration_summary['errors'].append(error_msg)

            self.log(f'✓ 上传文件迁移完成，共迁移 {self.migration_summary["uploads_migrated"]} 个项目', 'SUCCESS')
            return True

        except Exception as e:
            error_msg = f'上传文件迁移失败: {str(e)}'
            self.log(error_msg, 'ERROR')
            self.migration_summary['errors'].append(error_msg)
            return False

    def migrate_database(self):
        """迁移数据库"""
        if self.skip_db:
            self.log('跳过数据库迁移', 'INFO')
            return True

        self.log('开始迁移数据库...')

        source_db = self.source_dir / 'data' / 'database.db'
        target_db = self.target_dir / 'data' / 'database.db'

        if not source_db.exists():
            self.log(f'源数据库不存在: {source_db}', 'WARNING')
            return True

        try:
            db_size = source_db.stat().st_size
            self.log(f'找到数据库文件，大小: {self._format_size(db_size)}')

            if self.dry_run:
                self.log(f'[模拟] 复制数据库: database.db ({self._format_size(db_size)})', 'INFO')
            else:
                # 创建备份（如果目标数据库已存在）
                if target_db.exists():
                    backup_db = target_db.parent / f'database.db.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                    shutil.copy2(target_db, backup_db)
                    self.log(f'✓ 创建数据库备份: {backup_db.name}', 'INFO')

                # 复制数据库
                target_db.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_db, target_db)
                self.log(f'✓ 复制数据库: database.db ({self._format_size(db_size)})', 'INFO')

            self.migration_summary['total_size'] += db_size
            self.migration_summary['database_migrated'] = True
            return True

        except Exception as e:
            error_msg = f'数据库迁移失败: {str(e)}'
            self.log(error_msg, 'ERROR')
            self.migration_summary['errors'].append(error_msg)
            return False

    def migrate_workflow_spaces(self):
        """迁移工作流执行空间"""
        self.log('开始迁移工作流执行空间...')

        source_spaces = self.source_dir / 'workflow_execution_spaces'
        target_spaces = self.target_dir / 'workflow_execution_spaces'

        if not source_spaces.exists():
            self.log(f'源工作流执行空间目录不存在: {source_spaces}', 'WARNING')
            return True

        try:
            if not self.dry_run:
                target_spaces.mkdir(parents=True, exist_ok=True)

            space_dirs = [d for d in source_spaces.iterdir() if d.is_dir()]
            self.log(f'找到 {len(space_dirs)} 个工作流执行空间目录')

            migrated_count = 0
            for space_dir in space_dirs:
                try:
                    target_space = target_spaces / space_dir.name
                    space_size = self._get_dir_size(space_dir)

                    if self.dry_run:
                        self.log(f'  [模拟] 复制工作流空间: {space_dir.name} ({self._format_size(space_size)})', 'INFO')
                    else:
                        if target_space.exists():
                            shutil.rmtree(target_space)
                        shutil.copytree(space_dir, target_space)
                        self.log(f'  ✓ 复制工作流空间: {space_dir.name} ({self._format_size(space_size)})', 'INFO')

                    self.migration_summary['total_size'] += space_size
                    migrated_count += 1

                except Exception as e:
                    error_msg = f'复制工作流执行空间失败: {space_dir.name} - {str(e)}'
                    self.log(error_msg, 'ERROR')
                    self.migration_summary['errors'].append(error_msg)

            self.log(f'✓ 工作流执行空间迁移完成，共迁移 {migrated_count} 个目录', 'SUCCESS')
            return True

        except Exception as e:
            error_msg = f'工作流执行空间迁移失败: {str(e)}'
            self.log(error_msg, 'ERROR')
            self.migration_summary['errors'].append(error_msg)
            return False

    def save_migration_report(self):
        """保存迁移报告"""
        self.migration_summary['end_time'] = datetime.now().isoformat()
        self.migration_summary['total_size_human'] = self._format_size(self.migration_summary['total_size'])

        report_file = self.target_dir / f'migration_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

        try:
            if not self.dry_run:
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump(self.migration_summary, f, indent=2, ensure_ascii=False)

            self.log(f'迁移报告已保存: {report_file}', 'SUCCESS')
        except Exception as e:
            self.log(f'保存迁移报告失败: {str(e)}', 'WARNING')

    def run(self):
        """执行迁移"""
        self.log('=' * 60)
        self.log('开始项目运行时数据迁移')
        self.log('=' * 60)
        self.log(f'源项目: {self.source_dir}')
        self.log(f'目标项目: {self.target_dir}')
        if self.dry_run:
            self.log('模式: DRY_RUN（模拟迁移，不实际复制）', 'WARNING')
        self.log('=' * 60)

        # 验证路径
        if not self.validate_paths():
            self.log('路径验证失败，迁移中止', 'ERROR')
            return False

        # 执行迁移
        results = {
            'logs': self.migrate_logs(),
            'execution_spaces': self.migrate_execution_spaces(),
            'uploads': self.migrate_uploads(),
            'workflow_spaces': self.migrate_workflow_spaces(),
            'database': self.migrate_database(),
        }

        # 保存报告
        self.save_migration_report()

        # 输出总结
        self.log('=' * 60)
        self.log('迁移总结', 'SUCCESS')
        self.log('=' * 60)
        self.log(f'日志文件: {self.migration_summary["logs_migrated"]} 个')
        self.log(f'执行空间: {self.migration_summary["execution_spaces_migrated"]} 个')
        self.log(f'上传文件: {self.migration_summary["uploads_migrated"]} 个')
        self.log(f'数据库: {"已迁移" if self.migration_summary["database_migrated"] else "未迁移"}')
        self.log(f'总数据量: {self.migration_summary["total_size_human"]}')

        if self.migration_summary['errors']:
            self.log(f'错误数: {len(self.migration_summary["errors"])}', 'ERROR')
            for error in self.migration_summary['errors']:
                self.log(f'  - {error}', 'ERROR')

        success = all(results.values())
        if success:
            self.log('✓ 迁移完成', 'SUCCESS')
        else:
            self.log('⚠ 迁移完成，但存在错误', 'WARNING')

        self.log('=' * 60)
        return success

    @staticmethod
    def _get_dir_size(path):
        """计算目录大小"""
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.isfile(filepath):
                        total += os.path.getsize(filepath)
        except:
            pass
        return total

    @staticmethod
    def _format_size(size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f'{size_bytes:.2f}{unit}'
            size_bytes /= 1024
        return f'{size_bytes:.2f}TB'


def main():
    parser = argparse.ArgumentParser(
        description='项目运行时数据迁移脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 完整迁移（包含数据库）
  python migrate_runtime_data.py --source /path/to/old/project --target /path/to/new/project

  # 跳过数据库迁移
  python migrate_runtime_data.py --source /path/to/old/project --target /path/to/new/project --skip-db

  # 模拟迁移（不实际复制文件）
  python migrate_runtime_data.py --source /path/to/old/project --target /path/to/new/project --dry-run

  # 只迁移日志
  python migrate_runtime_data.py --source /path/to/old/project --target /path/to/new/project --skip-spaces --skip-db
        '''
    )

    parser.add_argument('--source', required=True, help='源项目目录路径')
    parser.add_argument('--target', required=True, help='目标项目目录路径')
    parser.add_argument('--skip-db', action='store_true', help='跳过数据库迁移')
    parser.add_argument('--skip-logs', action='store_true', help='跳过日志迁移')
    parser.add_argument('--skip-spaces', action='store_true', help='跳过执行空间迁移')
    parser.add_argument('--dry-run', action='store_true', help='模拟迁移，不实际复制文件')

    args = parser.parse_args()

    migrator = RuntimeDataMigrator(
        args.source,
        args.target,
        skip_db=args.skip_db,
        skip_logs=args.skip_logs,
        skip_spaces=args.skip_spaces,
        dry_run=args.dry_run
    )

    success = migrator.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
