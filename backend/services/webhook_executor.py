"""
Webhook执行服务
"""
import os
import json
import time
from datetime import datetime
from models import db, Webhook, WebhookLog, Execution
from services.executor import execute_script
from config import Config
from threading import Thread, Event
from flask import current_app


def execute_webhook(webhook_id, request_data, request_context):
    """
    执行Webhook

    Args:
        webhook_id: Webhook ID
        request_data: 请求数据 {
            'method': 'POST',
            'headers': {...},
            'body': {...},
            'query': {...},
            'ip': '127.0.0.1'
        }
        request_context: Flask请求上下文

    Returns:
        (status, result_data, response_code)
    """
    start_time = time.time()

    try:
        # 获取webhook配置
        webhook = Webhook.query.get(webhook_id)
        if not webhook:
            return 'failed', {'error': 'Webhook不存在'}, 404

        if not webhook.enabled:
            return 'failed', {'error': 'Webhook已禁用'}, 403

        # 更新统计信息
        webhook.call_count += 1
        webhook.last_called_at = datetime.utcnow()

        # 准备执行参数
        params = prepare_execution_params(webhook, request_data)

        # 创建执行记录
        execution = Execution(
            script_id=webhook.script_id,
            status='pending',
            params=json.dumps(params)
        )
        db.session.add(execution)
        db.session.flush()

        # 保存请求信息到执行空间
        if webhook.pass_full_request:
            save_request_info(execution.id, request_data)

        # 创建Webhook日志
        log = WebhookLog(
            webhook_id=webhook.id,
            execution_id=execution.id,
            request_method=request_data.get('method'),
            request_headers=json.dumps(request_data.get('headers', {})),
            request_body=json.dumps(request_data.get('body', {})),
            request_query=json.dumps(request_data.get('query', {})),
            request_ip=request_data.get('ip'),
            status='pending'
        )
        db.session.add(log)
        db.session.commit()

        # 根据执行模式处理
        if webhook.execution_mode == 'sync':
            # 同步执行
            result = execute_webhook_sync(execution.id, webhook.timeout)

            # 更新统计和日志
            duration_ms = int((time.time() - start_time) * 1000)
            update_webhook_stats_and_log(webhook, log, result, duration_ms)

            return result['status'], result['data'], result['code']

        else:
            # 异步执行
            app = current_app._get_current_object()

            def run_async():
                with app.app_context():
                    execute_script(execution.id)
                    # 异步执行完成后更新日志
                    db.session.refresh(execution)
                    duration_ms = int((time.time() - start_time) * 1000)
                    log.status = execution.status
                    log.duration_ms = duration_ms
                    log.response_code = 200 if execution.status == 'success' else 500
                    log.error_message = execution.error
                    db.session.commit()

                    # 更新统计
                    if execution.status == 'success':
                        webhook.success_count += 1
                    else:
                        webhook.failed_count += 1
                    db.session.commit()

            thread = Thread(target=run_async)
            thread.start()

            # 立即返回
            duration_ms = int((time.time() - start_time) * 1000)
            log.duration_ms = duration_ms
            log.status = 'success'
            log.response_code = 202
            log.response_body = json.dumps({
                'execution_id': execution.id,
                'message': '脚本执行已启动'
            })
            db.session.commit()

            return 'success', {
                'execution_id': execution.id,
                'message': '脚本执行已启动，请通过execution_id查询执行结果'
            }, 202

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        if 'log' in locals():
            log.status = 'failed'
            log.error_message = str(e)
            log.response_code = 500
            log.duration_ms = duration_ms
            db.session.commit()

        if 'webhook' in locals():
            webhook.failed_count += 1
            db.session.commit()

        return 'failed', {'error': str(e)}, 500


def prepare_execution_params(webhook, request_data):
    """
    准备执行参数
    将请求数据转换为脚本环境变量

    优先级：
    1. request body中的字段直接作为环境变量
    2. 预定义的元数据环境变量（WEBHOOK_*）
    """
    params = {}

    # 从request body提取字段作为环境变量
    body = request_data.get('body', {})
    if isinstance(body, dict):
        for key, value in body.items():
            # 转换为大写的环境变量名
            env_key = key.upper() if not key.startswith('WEBHOOK_') else key
            params[env_key] = str(value)

    # 添加Webhook元数据环境变量
    params['WEBHOOK_ID'] = str(webhook.id)
    params['WEBHOOK_NAME'] = webhook.name
    params['WEBHOOK_METHOD'] = request_data.get('method', 'POST')
    params['WEBHOOK_IP'] = request_data.get('ip', '')

    # 添加query参数
    query = request_data.get('query', {})
    if query:
        params['WEBHOOK_QUERY'] = json.dumps(query)
        # 同时将query参数展开为独立环境变量
        for key, value in query.items():
            params[f'QUERY_{key.upper()}'] = str(value)

    return params


def save_request_info(execution_id, request_data):
    """
    保存完整请求信息到执行空间
    """
    execution_space = Config.ensure_execution_space(execution_id)
    request_file = os.path.join(execution_space, 'webhook_request.json')

    with open(request_file, 'w', encoding='utf-8') as f:
        json.dump(request_data, f, ensure_ascii=False, indent=2)


def execute_webhook_sync(execution_id, timeout):
    """
    同步执行webhook（阻塞等待结果）
    """
    result = {'status': 'failed', 'data': {}, 'code': 500}
    execution_done = Event()

    def run_with_timeout():
        try:
            execute_script(execution_id)
            execution = Execution.query.get(execution_id)
            db.session.refresh(execution)

            if execution.status == 'success':
                result['status'] = 'success'
                result['code'] = 200
                result['data'] = {
                    'execution_id': execution.id,
                    'output': execution.output[:1000] if execution.output else '',
                    'status': 'success'
                }
            else:
                result['status'] = 'failed'
                result['code'] = 500
                result['data'] = {
                    'execution_id': execution.id,
                    'error': execution.error or '执行失败',
                    'status': 'failed'
                }
        except Exception as e:
            result['data'] = {'error': str(e)}
        finally:
            execution_done.set()

    thread = Thread(target=run_with_timeout)
    thread.start()

    # 等待执行完成或超时
    if not execution_done.wait(timeout=timeout):
        # 超时处理
        result['status'] = 'failed'
        result['code'] = 408
        result['data'] = {
            'execution_id': execution_id,
            'error': f'执行超时（{timeout}秒）',
            'status': 'timeout'
        }

    return result


def update_webhook_stats_and_log(webhook, log, result, duration_ms):
    """更新webhook统计和日志"""
    log.status = result['status']
    log.response_code = result['code']
    log.response_body = json.dumps(result['data'])
    log.duration_ms = duration_ms

    if result['status'] == 'success':
        webhook.success_count += 1
    else:
        webhook.failed_count += 1
        log.error_message = result['data'].get('error', '')

    db.session.commit()
