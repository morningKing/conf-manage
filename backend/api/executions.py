"""
执行记录API
"""
from flask import request, jsonify, Response, stream_with_context
from werkzeug.utils import secure_filename
from . import api_bp
from models import db, Execution, Script
from services.executor import execute_script
import json
import os
import time
from datetime import datetime


@api_bp.route('/scripts/<int:script_id>/execute', methods=['POST'])
def execute_script_api(script_id):
    """执行脚本"""
    try:
        script = Script.query.get_or_404(script_id)

        # 获取其他参数（如果有的话）
        params = {}
        if request.form.get('params'):
            params = json.loads(request.form.get('params'))

        # 创建执行记录（先创建以获取execution_id）
        execution = Execution(
            script_id=script_id,
            status='pending',
            params=json.dumps(params) if params else None
        )
        db.session.add(execution)
        db.session.commit()

        # 处理文件上传 - 直接保存到执行空间
        files = []
        if request.files:
            from config import Config
            # 为当前执行创建独立的执行空间
            execution_space = Config.ensure_execution_space(execution.id)
            print(f"为执行 {execution.id} 创建执行空间: {execution_space}")

            for file_key in request.files:
                file = request.files[file_key]
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    # 直接保存到执行空间,使用原始文件名
                    filepath = os.path.join(execution_space, filename)
                    file.save(filepath)
                    files.append({
                        'original_name': filename,
                        'saved_name': filename,
                        'path': os.path.abspath(filepath)
                    })
                    print(f"文件已保存到执行空间: {filename}")

        # 将文件信息添加到参数中
        if files:
            params['uploaded_files'] = files
            execution.params = json.dumps(params)
            db.session.commit()

        # 异步执行脚本
        from threading import Thread
        from flask import current_app

        # 获取当前应用实例
        app = current_app._get_current_object()

        def run_script_with_context():
            with app.app_context():
                execute_script(execution.id)

        thread = Thread(target=run_script_with_context)
        thread.start()

        return jsonify({
            'code': 0,
            'data': execution.to_dict(),
            'message': '脚本执行已启动'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions', methods=['GET'])
def get_executions():
    """获取执行历史列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        script_id = request.args.get('script_id', type=int)

        query = Execution.query
        if script_id:
            query = query.filter_by(script_id=script_id)

        pagination = query.order_by(Execution.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'code': 0,
            'data': {
                'items': [execution.to_dict() for execution in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions/<int:execution_id>', methods=['GET'])
def get_execution(execution_id):
    """获取执行详情"""
    try:
        execution = Execution.query.get_or_404(execution_id)
        return jsonify({
            'code': 0,
            'data': execution.to_dict()
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions/<int:execution_id>/logs', methods=['GET'])
def get_execution_logs(execution_id):
    """获取执行日志"""
    try:
        execution = Execution.query.get_or_404(execution_id)

        if not execution.log_file or not os.path.exists(execution.log_file):
            return jsonify({
                'code': 0,
                'data': {
                    'logs': execution.output or '',
                    'error': execution.error or ''
                }
            })

        # 读取日志文件
        with open(execution.log_file, 'r', encoding='utf-8') as f:
            logs = f.read()

        return jsonify({
            'code': 0,
            'data': {
                'logs': logs,
                'error': execution.error or ''
            }
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions/<int:execution_id>/logs/stream', methods=['GET'])
def stream_execution_logs(execution_id):
    """实时流式传输执行日志 (Server-Sent Events)"""
    def generate():
        execution = Execution.query.get(execution_id)
        if not execution:
            yield f"data: {json.dumps({'error': '执行记录不存在'})}\n\n"
            return

        # 等待日志文件创建
        max_wait = 10  # 最多等待10秒
        waited = 0
        while not execution.log_file or not os.path.exists(execution.log_file):
            if waited >= max_wait:
                yield f"data: {json.dumps({'error': '日志文件未创建'})}\n\n"
                return
            time.sleep(0.5)
            waited += 0.5
            db.session.refresh(execution)

        # 流式读取日志
        with open(execution.log_file, 'r', encoding='utf-8') as f:
            # 发送已有内容
            content = f.read()
            if content:
                yield f"data: {json.dumps({'type': 'log', 'content': content})}\n\n"

            # 持续读取新内容
            while True:
                db.session.refresh(execution)

                # 检查执行状态
                if execution.status in ['success', 'failed']:
                    # 读取剩余内容
                    new_content = f.read()
                    if new_content:
                        yield f"data: {json.dumps({'type': 'log', 'content': new_content})}\n\n"

                    # 发送完成信息
                    yield f"data: {json.dumps({'type': 'status', 'status': execution.status, 'error': execution.error or ''})}\n\n"
                    break

                # 读取新内容
                new_content = f.read()
                if new_content:
                    yield f"data: {json.dumps({'type': 'log', 'content': new_content})}\n\n"

                time.sleep(0.5)  # 每0.5秒检查一次

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@api_bp.route('/executions/<int:execution_id>', methods=['DELETE'])
def delete_execution(execution_id):
    """删除执行记录"""
    try:
        from config import Config
        import shutil

        execution = Execution.query.get_or_404(execution_id)

        # 删除日志文件
        if execution.log_file and os.path.exists(execution.log_file):
            os.remove(execution.log_file)

        # 删除执行空间（包含所有上传的文件和输出文件）
        execution_space = Config.get_execution_space(execution_id)
        if os.path.exists(execution_space):
            shutil.rmtree(execution_space)
            print(f"删除执行 {execution_id} 的执行空间: {execution_space}")

        db.session.delete(execution)
        db.session.commit()

        return jsonify({
            'code': 0,
            'message': '执行记录已删除'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions/<int:execution_id>/files', methods=['GET'])
def get_execution_files(execution_id):
    """获取执行空间的文件列表"""
    try:
        from config import Config

        execution = Execution.query.get_or_404(execution_id)
        execution_space = Config.get_execution_space(execution_id)

        if not os.path.exists(execution_space):
            return jsonify({
                'code': 0,
                'data': {
                    'files': [],
                    'total_size': 0,
                    'space_path': execution_space
                }
            })

        # 递归获取所有文件
        files = []
        total_size = 0

        for root, dirs, filenames in os.walk(execution_space):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, execution_space)
                stat = os.stat(filepath)

                files.append({
                    'name': filename,
                    'path': rel_path,
                    'size': stat.st_size,
                    'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'is_text': is_text_file(filepath)
                })
                total_size += stat.st_size

        # 按路径排序
        files.sort(key=lambda x: x['path'])

        return jsonify({
            'code': 0,
            'data': {
                'files': files,
                'total_size': total_size,
                'space_path': execution_space,
                'execution_id': execution_id
            }
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions/<int:execution_id>/files/<path:file_path>', methods=['GET'])
def get_execution_file(execution_id, file_path):
    """获取执行空间中的文件（预览或下载）"""
    try:
        from config import Config
        from flask import send_file

        execution = Execution.query.get_or_404(execution_id)
        execution_space = Config.get_execution_space(execution_id)

        # 安全检查：防止路径遍历攻击
        safe_path = os.path.normpath(file_path)
        if safe_path.startswith('..') or os.path.isabs(safe_path):
            return jsonify({'code': 1, 'message': '非法的文件路径'}), 400

        full_path = os.path.join(execution_space, safe_path)

        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            return jsonify({'code': 1, 'message': '文件不存在'}), 404

        # 检查是否请求下载
        download = request.args.get('download', 'false').lower() == 'true'

        if download:
            # 下载文件
            return send_file(
                full_path,
                as_attachment=True,
                download_name=os.path.basename(file_path)
            )
        else:
            # 预览文件
            if is_text_file(full_path):
                # 文本文件：返回内容
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read(10000)  # 限制10000字符
                        return jsonify({
                            'code': 0,
                            'data': {
                                'content': content,
                                'type': 'text',
                                'size': os.path.getsize(full_path)
                            }
                        })
                except UnicodeDecodeError:
                    return jsonify({
                        'code': 0,
                        'data': {
                            'content': '无法预览：文件编码不支持',
                            'type': 'binary',
                            'size': os.path.getsize(full_path)
                        }
                    })
            else:
                # 二进制文件：返回文件信息
                return jsonify({
                    'code': 0,
                    'data': {
                        'content': '二进制文件，请下载查看',
                        'type': 'binary',
                        'size': os.path.getsize(full_path)
                    }
                })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


def is_text_file(filepath):
    """判断文件是否为文本文件"""
    text_extensions = {
        '.txt', '.py', '.js', '.json', '.xml', '.html', '.css', '.md',
        '.yml', '.yaml', '.ini', '.conf', '.log', '.csv', '.sql',
        '.sh', '.bat', '.c', '.cpp', '.h', '.java', '.go', '.rs',
        '.ts', '.tsx', '.jsx', '.vue', '.php', '.rb', '.pl', '.r'
    }

    ext = os.path.splitext(filepath)[1].lower()
    return ext in text_extensions

