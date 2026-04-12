"""
临时文件上传API
"""
from flask import request, jsonify
import os
import uuid
from datetime import datetime
from . import api_bp

@api_bp.route('/upload/temp', methods=['POST'])
def upload_temp_file():
    """
    上传临时文件供参数使用
    返回文件路径供脚本参数注入环境变量
    """
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'code': 1, 'message': '未找到文件'}), 400

        # 检查文件名是否为空
        if not file.filename:
            return jsonify({'code': 1, 'message': '文件名为空'}), 400

        # 创建临时目录
        temp_dir = os.path.join(os.getcwd(), 'temp_upload')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # 生成唯一文件名（避免冲突）
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = uuid.uuid4().hex[:8]
        # 保持原始文件扩展名
        original_ext = file.filename.split('.')[-1] if '.' in file.filename else ''
        filename = f"{timestamp}_{unique_id}_{file.filename}"
        file_path = os.path.join(temp_dir, filename)

        # 保存文件
        file.save(file_path)

        # 验证文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'code': 1, 'message': '文件保存失败'}), 500

        return jsonify({
            'code': 0,
            'data': {
                'file_path': file_path,
                'filename': file.filename,
                'size': os.path.getsize(file_path)
            },
            'message': '上传成功'
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': f'上传失败: {str(e)}'}), 500


@api_bp.route('/upload/cleanup', methods=['POST'])
def cleanup_temp_files():
    """
    清理临时上传文件（定时任务调用）
    清理超过24小时的临时文件
    """
    try:
        temp_dir = os.path.join(os.getcwd(), 'temp_upload')
        if not os.path.exists(temp_dir):
            return jsonify({'code': 0, 'message': '临时目录不存在'}), 200

        # 获取当前时间
        now = datetime.now()

        # 清理超过24小时的文件
        cleaned_count = 0
        cleaned_size = 0

        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)

            # 获取文件修改时间
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            age_hours = (now - file_mtime).total_seconds() / 3600

            # 如果文件超过24小时，删除
            if age_hours > 24:
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                cleaned_count += 1
                cleaned_size += file_size

        return jsonify({
            'code': 0,
            'data': {
                'cleaned_count': cleaned_count,
                'cleaned_size': cleaned_size
            },
            'message': f'清理了 {cleaned_count} 个临时文件，共 {cleaned_size / 1024 / 1024:.2f} MB'
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': f'清理失败: {str(e)}'}), 500