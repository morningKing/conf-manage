"""
执行记录API
"""
from flask import request, jsonify, Response, stream_with_context, current_app
from werkzeug.exceptions import HTTPException
from utils import safe_filename
from utils.file_utils import is_text_file
from . import api_bp
from models import db, Execution, Script
from services.executor import execute_script
from services.execution_service import delete_execution_record, kill_process_tree, retry_execution
import json
import os
import time
import psutil
from threading import Thread
from datetime import datetime, timezone


@api_bp.route('/scripts/<int:script_id>/execute', methods=['POST'])
def execute_script_api(script_id):
    """执行脚本"""
    try:
        script = Script.query.get_or_404(script_id)

        # 获取其他参数（如果有的话）
        params = {}
        params_values = {}

        if request.form.get('params'):
            try:
                params_values = json.loads(request.form.get('params'))
            except json.JSONDecodeError:
                return jsonify({'code': 1, 'message': '参数格式错误'}), 400

        # 验证参数值（根据脚本参数定义）
        if script.parameters:
            try:
                script_params = json.loads(script.parameters)

                for param_def in script_params:
                    param_key = param_def.get('key')
                    param_type = param_def.get('type', 'text')
                    param_required = param_def.get('required', False)
                    param_value = params_values.get(param_key)

                    # 校验必填参数
                    if param_required and not param_value:
                        return jsonify({'code': 1, 'message': f'参数 {param_key} 为必填项'}), 400

                    # 校验文件类型参数（检查文件路径是否存在）
                    if param_type == 'file' and param_value:
                        if not os.path.exists(param_value):
                            return jsonify({'code': 1, 'message': f'参数 {param_key} 的文件不存在'}), 400

                    # 校验数字范围
                    if param_type == 'number' and param_value:
                        validation = param_def.get('validation', {})
                        min_value = validation.get('min_value')
                        max_value = validation.get('max_value')

                        try:
                            num_value = float(param_value)
                            if min_value and num_value < min_value:
                                return jsonify({'code': 1, 'message': f'参数 {param_key} 值 {num_value} 小于最小值 {min_value}'}), 400
                            if max_value and num_value > max_value:
                                return jsonify({'code': 1, 'message': f'参数 {param_key} 值 {num_value} 大于最大值 {max_value}'}), 400
                        except (ValueError, TypeError):
                            return jsonify({'code': 1, 'message': f'参数 {param_key} 必须为数字'}), 400

                    # 校验文本长度
                    if param_type in ['text', 'textarea', 'password'] and param_value:
                        validation = param_def.get('validation', {})
                        min_length = validation.get('min_length')
                        max_length = validation.get('max_length')

                        str_value = str(param_value)
                        if min_length and len(str_value) < min_length:
                            return jsonify({'code': 1, 'message': f'参数 {param_key} 长度小于最小长度 {min_length}'}), 400
                        if max_length and len(str_value) > max_length:
                            return jsonify({'code': 1, 'message': f'参数 {param_key} 长度大于最大长度 {max_length}'}), 400

                    # 校验选择类型参数（检查值是否在options中）
                    if param_type in ['select', 'multiselect', 'radio', 'checkbox'] and param_value:
                        options = param_def.get('options', [])
                        valid_values = [opt['value'] for opt in options]

                        if param_type in ['select', 'radio']:
                            # 单选类型
                            if param_value not in valid_values:
                                return jsonify({'code': 1, 'message': f'参数 {param_key} 的值不在有效选项中'}), 400
                        else:
                            # 多选类型
                            if not isinstance(param_value, list):
                                return jsonify({'code': 1, 'message': f'参数 {param_key} 必须为数组类型'}), 400
                            for v in param_value:
                                if v not in valid_values:
                                    return jsonify({'code': 1, 'message': f'参数 {param_key} 的值 {v} 不在有效选项中'}), 400

                    # 使用校验后的值
                    params[param_key] = param_value if param_value else param_def.get('default_value', '')

            except json.JSONDecodeError:
                return jsonify({'code': 1, 'message': '脚本参数定义格式错误'}), 400
        else:
            # 如果脚本没有参数定义，直接使用传入的参数值
            params = params_values

        # 获取执行环境ID（如果指定）
        environment_id = request.form.get('environment_id', type=int)

        # 创建执行记录（先创建以获取execution_id）
        execution = Execution(
            script_id=script_id,
            environment_id=environment_id,
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
                    filename = safe_filename(file.filename)
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

        # 先准备好返回数据，避免线程启动后懒加载冲突
        execution_data = {
            'id': execution.id,
            'script_id': execution.script_id,
            'script_name': script.name,
            'environment_id': execution.environment_id,
            'status': execution.status,
            'params': execution.params,
            'created_at': execution.created_at.isoformat() if execution.created_at else None
        }

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
            'data': execution_data,
            'message': '脚本执行已启动'
        })
    except HTTPException:
        raise
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions', methods=['GET'])
def get_executions():
    """获取执行历史列表（包括脚本执行和工作流执行）"""
    try:
        from models.workflow import WorkflowExecution

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        script_id = request.args.get('script_id', type=int)
        exec_type = request.args.get('type', '')  # 'script', 'workflow', 或空字符串表示全部

        # 有界查询：两张表各取前 page*per_page 条（按创建时间倒序），
        # 合并排序后切片分页，避免全表加载
        fetch_limit = page * per_page

        # 获取脚本执行记录
        script_executions = []
        if exec_type != 'workflow':
            query = Execution.query.order_by(Execution.created_at.desc())
            if script_id:
                query = query.filter_by(script_id=script_id)
            for execution in query.limit(fetch_limit).all():
                item = execution.to_dict()
                item['execution_type'] = 'script'
                item['type_name'] = '脚本执行'
                script_executions.append(item)

        # 获取工作流执行记录
        workflow_executions = []
        if exec_type != 'script':
            for wf_execution in WorkflowExecution.query.order_by(
                    WorkflowExecution.created_at.desc()).limit(fetch_limit).all():
                item = wf_execution.to_dict()
                item['execution_type'] = 'workflow'
                item['type_name'] = '工作流执行'
                # 添加工作流名称作为 script_name，保持前端兼容
                item['script_name'] = item.get('workflow', {}).get('name', '未知工作流')
                workflow_executions.append(item)

        # 合并并按创建时间排序后分页
        all_executions = script_executions + workflow_executions
        all_executions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        start = (page - 1) * per_page
        items = all_executions[start:start + per_page]

        # 真实总数用于分页元信息（COUNT 查询，代价远小于全表加载）
        if exec_type == 'workflow':
            total = WorkflowExecution.query.count()
        else:
            count_q = Execution.query
            if script_id:
                count_q = count_q.filter_by(script_id=script_id)
            total = count_q.count()
            if exec_type != 'script':
                total += WorkflowExecution.query.count()

        return jsonify({
            'code': 0,
            'data': {
                'items': items,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            }
        })
    except HTTPException:
        raise
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
    except HTTPException:
        raise
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
    except HTTPException:
        raise
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

                # 发送进度更新
                progress_data = {
                    'type': 'progress',
                    'progress': execution.progress or 0,
                    'stage': execution.stage or 'pending'
                }
                yield f"data: {json.dumps(progress_data)}\n\n"

                # 检查执行状态
                if execution.status in ['success', 'failed']:
                    # 读取剩余内容
                    new_content = f.read()
                    if new_content:
                        yield f"data: {json.dumps({'type': 'log', 'content': new_content})}\n\n"

                    # 发送完成信息
                    completion_data = {
                        'type': 'status',
                        'status': execution.status,
                        'progress': execution.progress or 100,
                        'stage': execution.stage or ('completed' if execution.status == 'success' else 'failed'),
                        'error': execution.error or ''
                    }
                    yield f"data: {json.dumps(completion_data)}\n\n"
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
        execution = Execution.query.get_or_404(execution_id)
        delete_execution_record(execution)

        return jsonify({
            'code': 0,
            'message': '执行记录已删除'
        })
    except HTTPException:
        raise
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions/batch', methods=['POST'])
def batch_manage_executions():
    """批量管理执行记录（delete / cancel / retry）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 1, 'message': '请求数据不能为空'}), 400

        action = data.get('action')
        execution_ids = data.get('execution_ids', [])

        if not action:
            return jsonify({'code': 1, 'message': '操作类型不能为空'}), 400
        if not execution_ids:
            return jsonify({'code': 1, 'message': '执行ID列表不能为空'}), 400
        if not isinstance(execution_ids, list):
            return jsonify({'code': 1, 'message': '执行ID必须是数组格式'}), 400

        executions = Execution.query.filter(Execution.id.in_(execution_ids)).all()
        found_ids = [e.id for e in executions]
        missing_ids = [eid for eid in execution_ids if eid not in found_ids]
        if missing_ids:
            return jsonify({'code': 1, 'message': f'以下执行记录不存在: {missing_ids}'}), 404

        result = {
            'action': action,
            'total': len(execution_ids),
            'success': 0,
            'failed': 0,
            'details': []
        }

        if action == 'delete':
            _batch_delete(executions, result)
        elif action == 'cancel':
            _batch_cancel(executions, result)
        elif action == 'retry':
            _batch_retry(executions, result)
        else:
            return jsonify({'code': 1, 'message': f'不支持的操作类型: {action}'}), 400

        return jsonify({
            'code': 0,
            'data': result,
            'message': f'批量{action}操作完成: 成功{result["success"]}个，失败{result["failed"]}个'
        })
    except HTTPException:
        raise
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


def _batch_delete(executions, result):
    """批量删除执行记录"""
    for execution in executions:
        try:
            delete_execution_record(execution)
            result['success'] += 1
            result['details'].append({'id': execution.id, 'status': 'success', 'message': '删除成功'})
        except Exception as e:
            result['failed'] += 1
            result['details'].append({'id': execution.id, 'status': 'failed', 'message': str(e)})


def _batch_cancel(executions, result):
    """批量取消运行中的执行"""
    for execution in executions:
        if execution.status != 'running':
            result['failed'] += 1
            result['details'].append({
                'id': execution.id,
                'status': 'failed',
                'message': f'只能取消正在运行的执行，当前状态: {execution.status}'
            })
            continue

        try:
            if execution.pid:
                try:
                    kill_process_tree(execution.pid)
                except psutil.NoSuchProcess:
                    pass

            execution.status = 'failed'
            execution.stage = 'cancelled'
            execution.progress = 100
            execution.error = '执行已被批量取消'
            execution.end_time = datetime.now(timezone.utc)

            result['success'] += 1
            result['details'].append({'id': execution.id, 'status': 'success', 'message': '取消成功'})
        except Exception as e:
            result['failed'] += 1
            result['details'].append({'id': execution.id, 'status': 'failed', 'message': str(e)})

    if result['success'] > 0:
        db.session.commit()


def _batch_retry(executions, result):
    """批量重试失败/取消的执行"""
    for execution in executions:
        if execution.status not in ['failed', 'cancelled']:
            result['failed'] += 1
            result['details'].append({
                'id': execution.id,
                'status': 'failed',
                'message': f'只能重试失败或取消的执行，当前状态: {execution.status}'
            })
            continue

        try:
            new_execution = retry_execution(execution)
            new_exec_id = new_execution.id
            # 先提交，确保新线程能查到这条记录
            db.session.commit()

            app = current_app._get_current_object()
            thread = Thread(target=_run_script_with_context, args=(app, new_exec_id))
            thread.start()

            result['success'] += 1
            result['details'].append({
                'id': execution.id,
                'status': 'success',
                'message': f'重试成功，新执行ID: {new_exec_id}'
            })
        except Exception as e:
            result['failed'] += 1
            result['details'].append({'id': execution.id, 'status': 'failed', 'message': str(e)})


def _run_script_with_context(app, execution_id):
    """在新线程中以应用上下文执行脚本"""
    with app.app_context():
        execute_script(execution_id)


@api_bp.route('/executions/statistics', methods=['GET'])
def get_executions_statistics():
    """获取执行记录统计信息"""
    try:
        # 基本统计
        total_executions = Execution.query.count()
        success_executions = Execution.query.filter_by(status='success').count()
        failed_executions = Execution.query.filter_by(status='failed').count()
        running_executions = Execution.query.filter_by(status='running').count()
        pending_executions = Execution.query.filter_by(status='pending').count()

        # 按脚本统计
        from sqlalchemy import case
        script_stats = db.session.query(
            Script.name,
            db.func.count(Execution.id).label('total'),
            db.func.sum(
                case(
                    (Execution.status == 'success', 1),
                    else_=0
                )
            ).label('success'),
            db.func.sum(
                case(
                    (Execution.status == 'failed', 1),
                    else_=0
                )
            ).label('failed')
        ).join(Execution, Script.id == Execution.script_id).group_by(Script.name).all()

        # 按日期统计（最近7天）
        from datetime import datetime, timedelta
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        daily_stats = db.session.query(
            db.func.date(Execution.created_at).label('date'),
            db.func.count(Execution.id).label('total'),
            db.func.sum(
                case(
                    (Execution.status == 'success', 1),
                    else_=0
                )
            ).label('success'),
            db.func.sum(
                case(
                    (Execution.status == 'failed', 1),
                    else_=0
                )
            ).label('failed')
        ).filter(Execution.created_at >= seven_days_ago).group_by(db.func.date(Execution.created_at)).all()

        # 按状态统计
        status_stats = db.session.query(
            Execution.status,
            db.func.count(Execution.id).label('count')
        ).group_by(Execution.status).all()

        return jsonify({
            'code': 0,
            'data': {
                'summary': {
                    'total': total_executions,
                    'success': success_executions,
                    'failed': failed_executions,
                    'running': running_executions,
                    'pending': pending_executions,
                    'success_rate': round(success_executions / max(1, total_executions) * 100, 2)
                },
                'by_script': [
                    {
                        'script_name': stat.name,
                        'total': stat.total,
                        'success': stat.success or 0,
                        'failed': stat.failed or 0,
                        'success_rate': round((stat.success or 0) / max(1, stat.total) * 100, 2)
                    }
                    for stat in script_stats
                ],
                'by_date': [
                    {
                        'date': stat.date.isoformat() if hasattr(stat.date, 'isoformat') else str(stat.date),
                        'total': stat.total,
                        'success': stat.success or 0,
                        'failed': stat.failed or 0
                    }
                    for stat in daily_stats
                ],
                'by_status': [
                    {
                        'status': stat.status,
                        'count': stat.count
                    }
                    for stat in status_stats
                ]
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions/<int:execution_id>/cancel', methods=['POST'])
def cancel_execution(execution_id):
    """中断执行"""
    try:
        import signal
        import psutil

        execution = Execution.query.get_or_404(execution_id)

        if execution.status != 'running':
            return jsonify({
                'code': 1,
                'message': '只能中断正在运行的执行'
            }), 400

        if not execution.pid:
            return jsonify({
                'code': 1,
                'message': '未找到进程ID'
            }), 400

        try:
            # 终止进程及其全部子进程（先温和终止，超时后强杀）
            kill_process_tree(execution.pid)
        except psutil.NoSuchProcess:
            # 进程已经不存在
            pass

        # 更新执行状态
        execution.status = 'failed'
        execution.stage = 'cancelled'
        execution.progress = 100
        execution.error = '执行已被用户中断'
        execution.end_time = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify({
            'code': 0,
            'message': '执行已中断'
        })
    except HTTPException:
        raise
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
    except HTTPException:
        raise
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions/<int:execution_id>/files/<path:file_path>', methods=['GET'])
def get_execution_file(execution_id, file_path):
    """获取执行空间中的文件（预览或下载）"""
    try:
        from config import Config
        from flask import send_file

        # 检查是否是Excel API请求（通过查询参数）
        if request.args.get('excel', 'false').lower() == 'true':
            from api.excel import get_excel_file_internal
            return get_excel_file_internal(execution_id, file_path)

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
            ext = os.path.splitext(full_path)[1].lower()

            # 图片文件：直接返回图片
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico']:
                return send_file(full_path, mimetype=f'image/{ext[1:]}')

            # 文本文件：返回内容
            if is_text_file(full_path):
                try:
                    # 尝试多种编码
                    encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
                    content = None

                    for encoding in encodings:
                        try:
                            with open(full_path, 'r', encoding=encoding) as f:
                                content = f.read(100000)  # 限制100KB
                            break
                        except UnicodeDecodeError:
                            continue

                    if content is None:
                        return jsonify({
                            'code': 0,
                            'data': {
                                'content': '无法预览：文件编码不支持',
                                'type': 'binary',
                                'size': os.path.getsize(full_path)
                            }
                        })

                    return jsonify({
                        'code': 0,
                        'data': {
                            'content': content,
                            'type': 'text',
                            'size': os.path.getsize(full_path)
                        }
                    })
                except Exception as e:
                    return jsonify({
                        'code': 0,
                        'data': {
                            'content': f'无法预览：{str(e)}',
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
    except HTTPException:
        raise
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions/<int:execution_id>/re-execute', methods=['POST'])
def re_execute_script(execution_id):
    """重新执行脚本（支持所有非运行状态）"""
    try:
        execution = Execution.query.get_or_404(execution_id)

        # 检查状态（running状态不能重新执行）
        if execution.status == 'running':
            return jsonify({
                'code': 1,
                'message': '正在运行的执行不能重新执行，请先中断'
            }), 400

        # 新建执行记录并复制原执行空间的文件
        new_execution = retry_execution(execution)
        new_exec_id = new_execution.id
        original_exec_id = execution.id
        script_name = execution.script.name if execution.script else None

        # 先提交，确保新线程能查到这条记录
        db.session.commit()

        # 异步执行脚本
        app = current_app._get_current_object()
        thread = Thread(target=_run_script_with_context, args=(app, new_exec_id))
        thread.start()

        return jsonify({
            'code': 0,
            'data': {
                'new_execution_id': new_exec_id,
                'original_execution_id': original_exec_id,
                'script_name': script_name
            },
            'message': '已创建新执行记录并启动执行'
        })
    except HTTPException:
        raise
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500



