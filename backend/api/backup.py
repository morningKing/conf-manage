#!/usr/bin/env python3
"""
备份和导出API
"""
import os
import sys
from flask import jsonify, request, send_file

# 将utils目录添加到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from . import api_bp
from utils.export_database import export_database, get_database_info
from utils.backup_system import backup_system, list_backups, delete_old_backups
from config import Config


@api_bp.route('/backup/database-export', methods=['POST'])
def create_database_export():
    """
    导出数据库
    POST /api/backup/database-export
    """
    try:
        # 获取数据库信息
        db_info = get_database_info()

        # 执行导出
        output_file = export_database()

        # 获取文件信息
        file_size = os.path.getsize(output_file)
        filename = os.path.basename(output_file)

        return jsonify({
            'code': 0,
            'message': '数据库导出成功',
            'data': {
                'filename': filename,
                'filepath': output_file,
                'size': file_size,
                'database_info': db_info
            }
        })
    except Exception as e:
        return jsonify({
            'code': 1,
            'message': f'操作失败: {str(e)}'
        }), 500


@api_bp.route('/backup/system-backup', methods=['POST'])
def create_system_backup():
    """
    创建系统备份
    POST /api/backup/system-backup

    Body参数：
    - backup_name: 备份名称（可选）
    - include_logs: 是否包含日志（默认false）
    - include_execution_spaces: 是否包含执行空间（默认true）
    """
    try:
        data = request.get_json() or {}

        backup_name = data.get('backup_name') or None
        include_logs = data.get('include_logs', False)
        include_execution_spaces = data.get('include_execution_spaces', True)

        # 执行备份
        backup_file = backup_system(
            backup_name=backup_name,
            include_logs=include_logs,
            include_execution_spaces=include_execution_spaces
        )

        # 获取文件信息
        file_size = os.path.getsize(backup_file)
        filename = os.path.basename(backup_file)

        return jsonify({
            'code': 0,
            'message': '系统备份成功',
            'data': {
                'filename': filename,
                'filepath': backup_file,
                'size': file_size
            }
        })
    except Exception as e:
        return jsonify({
            'code': 1,
            'message': f'操作失败: {str(e)}'
        }), 500


@api_bp.route('/backup/list', methods=['GET'])
def get_backup_list():
    """
    获取所有备份文件列表
    GET /api/backup/list
    """
    try:
        backups = list_backups()

        # 格式化返回数据
        backup_list = []
        for backup in backups:
            backup_list.append({
                'name': backup['name'],
                'path': backup['path'],
                'size': backup['size'],
                'size_mb': round(backup['size'] / (1024 * 1024), 2),
                'created': backup['created'].strftime('%Y-%m-%d %H:%M:%S'),
                'type': 'database' if backup['name'].endswith('.sql') else 'system'
            })

        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'items': backup_list,
                'total': len(backup_list)
            }
        })
    except Exception as e:
        return jsonify({
            'code': 1,
            'message': f'操作失败: {str(e)}'
        }), 500


@api_bp.route('/backup/download/<filename>', methods=['GET'])
def download_backup(filename):
    """
    下载备份文件
    GET /api/backup/download/<filename>
    """
    try:
        # 安全检查：防止路径遍历攻击
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({
                'code': 1,
                'message': '非法的文件名'
            }), 400

        file_path = os.path.join(Config.BACKUPS_DIR, filename)

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({
                'code': 1,
                'message': '备份文件不存在'
            }), 404

        # 发送文件
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({
            'code': 1,
            'message': f'操作失败: {str(e)}'
        }), 500


@api_bp.route('/backup/<filename>', methods=['DELETE'])
def delete_backup(filename):
    """
    删除备份文件
    DELETE /api/backup/<filename>
    """
    try:
        # 安全检查：防止路径遍历攻击
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({
                'code': 1,
                'message': '非法的文件名'
            }), 400

        file_path = os.path.join(Config.BACKUPS_DIR, filename)

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({
                'code': 1,
                'message': '备份文件不存在'
            }), 404

        # 删除文件
        os.remove(file_path)

        return jsonify({
            'code': 0,
            'message': '删除成功'
        })
    except Exception as e:
        return jsonify({
            'code': 1,
            'message': f'操作失败: {str(e)}'
        }), 500


@api_bp.route('/backup/clean', methods=['POST'])
def clean_old_backups_api():
    """
    清理旧备份
    POST /api/backup/clean

    Body参数：
    - keep_days: 保留最近N天的备份（默认30天）
    """
    try:
        data = request.get_json() or {}
        keep_days = data.get('keep_days', 30)

        # 验证参数
        if not isinstance(keep_days, int) or keep_days < 1:
            return jsonify({
                'code': 1,
                'message': '保留天数必须是大于0的整数'
            }), 400

        # 执行清理
        deleted_count = delete_old_backups(keep_days)

        return jsonify({
            'code': 0,
            'message': f'清理完成，删除了 {deleted_count} 个旧备份',
            'data': {
                'deleted_count': deleted_count,
                'keep_days': keep_days
            }
        })
    except Exception as e:
        return jsonify({
            'code': 1,
            'message': f'操作失败: {str(e)}'
        }), 500


@api_bp.route('/backup/database-info', methods=['GET'])
def get_db_info():
    """
    获取数据库信息
    GET /api/backup/database-info
    """
    try:
        info = get_database_info()

        if not info:
            return jsonify({
                'code': 1,
                'message': '数据库文件不存在'
            }), 404

        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'path': info['path'],
                'size': info['size'],
                'size_mb': round(info['size'] / (1024 * 1024), 2),
                'tables': info['tables']
            }
        })
    except Exception as e:
        return jsonify({
            'code': 1,
            'message': f'操作失败: {str(e)}'
        }), 500
