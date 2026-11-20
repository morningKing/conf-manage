# -*- coding: utf-8 -*-
"""
MCP (Model Context Protocol) 服务器

把本系统的脚本/工作流执行能力以 MCP 工具对外提供服务，
与 REST API 共用同一执行链路（隔离执行空间、日志、统计）。

传输模式：
- streamable-http（默认）：远程/多客户端接入，python mcp_server.py
- stdio：本地客户端（如 Claude Desktop）直连，python mcp_server.py --transport stdio

鉴权（仅 http 模式）：设置环境变量 MCP_TOKEN 后，请求必须携带 Bearer <token>；
未设置则不启用鉴权（仅建议本机/内网使用）。

定时任务去重：MCP 进程内会清空 APScheduler 任务，避免与主服务重复触发 cron。
"""
import argparse
import hmac
import json
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _load_env_file():
    """加载仓库根目录的 .env（不覆盖已有环境变量），便于 stdio 客户端直启"""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root, '.env')
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_env_file()

from mcp.server.mcpserver import MCPServer  # noqa: E402
from psycopg2.errors import UndefinedTable  # noqa: E402

from app import create_app  # noqa: E402
from models import (  # noqa: E402
    db, Script, Execution, Workflow, WorkflowExecution,
)
from services.execution_service import kill_process_tree  # noqa: E402
from services.workflow_executor import execute_workflow_async  # noqa: E402

TERMINAL_STATUSES = {'success', 'failed', 'cancelled'}

server = MCPServer(
    name='script-tool-manager',
    title='脚本工具管理系统',
    description='脚本管理与执行、工作流编排能力（隔离执行空间、实时日志）',
)

# 应用实例：工具函数统一通过 _ctx() 进入应用上下文
app = create_app()

# 关键：清空本进程内的定时任务，避免与主服务（5001）重复触发 cron
with app.app_context():
    from services.scheduler import scheduler_manager
    scheduler_manager.scheduler.remove_all_jobs()


def _ctx():
    """为每个工具调用提供应用上下文（MCP 线程与 Flask 请求线程隔离）"""
    return app.app_context()


def _json(data):
    return json.dumps(data, ensure_ascii=False, default=str)


def _wait_terminal(model_cls, record_id, timeout_seconds):
    """轮询到终态；超时返回 None

    populate_existing=True 强制绕过 SQLAlchemy 身份映射缓存 ——
    状态由后台线程/另一进程提交，同 session 内的 get 默认返回缓存对象。
    """
    deadline = time.time() + max(1, timeout_seconds)
    while time.time() < deadline:
        record = db.session.get(model_cls, record_id, populate_existing=True)
        if record is None:
            raise ValueError(f'记录不存在: {record_id}')
        if record.status in TERMINAL_STATUSES:
            return record
        time.sleep(1)
    return None


# ---------------- 工具定义 ----------------


@server.tool()
def list_scripts(keyword: str = None, limit: int = 20) -> str:
    """列出脚本（可按名称关键字过滤），返回 id/名称/类型/描述/更新时间"""
    with _ctx():
        query = Script.query
        if keyword:
            query = query.filter(Script.name.ilike(f'%{keyword}%'))
        scripts = query.order_by(Script.updated_at.desc()).limit(max(1, min(limit, 100))).all()
        return _json([{
            'id': s.id, 'name': s.name, 'type': s.type,
            'description': s.description, 'updated_at': s.updated_at.isoformat() if s.updated_at else None,
        } for s in scripts])


@server.tool()
def get_script(script_id: int) -> str:
    """获取脚本详情（含代码、参数定义、依赖）"""
    with _ctx():
        script = db.session.get(Script, script_id)
        if script is None:
            raise ValueError(f'脚本不存在: {script_id}')
        return _json(script.to_dict())


@server.tool()
def run_script(script_id: int = None, script_name: str = None,
               params: dict = None, wait_seconds: int = 60) -> str:
    """执行脚本（二选一传 script_id 或 script_name）。

    params 为脚本参数字典（环境变量注入，执行参数优先于全局变量）。
    默认等待最多 60 秒；超时未结束会返回 execution_id（status=running），
    用 wait_execution/get_execution 继续跟踪。
    """
    with _ctx():
        if script_id:
            script = db.session.get(Script, script_id)
        elif script_name:
            script = Script.query.filter_by(name=script_name).first()
        else:
            raise ValueError('必须提供 script_id 或 script_name')
        if script is None:
            raise ValueError('脚本不存在')

        execution = Execution(
            script_id=script.id,
            status='pending',
            params=json.dumps(params or {}, ensure_ascii=False) if params else None,
        )
        db.session.add(execution)
        db.session.commit()
        exec_id = execution.id

    # 后台线程必须携带应用上下文（与 REST API 相同模式）
    app_obj = app

    def _run():
        with app_obj.app_context():
            from services.executor import execute_script
            execute_script(exec_id)

    threading.Thread(target=_run, daemon=True).start()

    with _ctx():
        final = _wait_terminal(Execution, exec_id, wait_seconds)
        if final is not None:
            return _json(_execution_brief(final))
        return _json({'status': 'running', 'execution_id': exec_id,
                      'message': f'{wait_seconds}s 内未结束，请用 wait_execution/get_execution 跟踪'})


@server.tool()
def wait_execution(execution_id: int, timeout_seconds: int = 120) -> str:
    """阻塞等待脚本执行到终态，返回状态/输出/错误"""
    with _ctx():
        final = _wait_terminal(Execution, execution_id, timeout_seconds)
        if final is None:
            return _json({'status': 'running', 'execution_id': execution_id,
                          'message': f'{timeout_seconds}s 内未结束'})
        return _json(_execution_brief(final))


@server.tool()
def get_execution(execution_id: int) -> str:
    """获取执行记录详情（状态/进度/输出/错误/日志路径）"""
    with _ctx():
        record = db.session.get(Execution, execution_id)
        if record is None:
            raise ValueError(f'执行记录不存在: {execution_id}')
        return _json(_execution_brief(record))


@server.tool()
def list_executions(limit: int = 10) -> str:
    """列出最近的执行记录（id/脚本名/状态/时间）"""
    with _ctx():
        rows = (Execution.query.order_by(Execution.created_at.desc())
                .limit(max(1, min(limit, 50))).all())
        return _json([{
            'id': e.id,
            'script_name': e.script.name if e.script else None,
            'status': e.status,
            'created_at': e.created_at.isoformat() if e.created_at else None,
        } for e in rows])


@server.tool()
def cancel_execution(execution_id: int) -> str:
    """取消运行中的脚本执行（终止进程树并标记为失败/取消）"""
    with _ctx():
        execution = db.session.get(Execution, execution_id)
        if execution is None:
            raise ValueError(f'执行记录不存在: {execution_id}')
        if execution.status != 'running':
            return _json({'status': execution.status, 'message': '仅运行中的执行可取消'})
        if execution.pid:
            try:
                kill_process_tree(execution.pid)
            except Exception:
                pass  # 进程可能已自行退出
        execution.status = 'failed'
        execution.stage = 'cancelled'
        execution.progress = 100
        execution.error = '执行已被 MCP 调用方中断'
        from datetime import datetime, timezone
        execution.end_time = datetime.now(timezone.utc)
        db.session.commit()
        return _json({'status': 'failed', 'execution_id': execution_id, 'message': '已取消'})


@server.tool()
def list_pipelines(keyword: str = None, limit: int = 20) -> str:
    """列出管道（工作流）清单：id/名称/描述/步骤数/启用状态"""
    with _ctx():
        query = Workflow.query
        if keyword:
            query = query.filter(Workflow.name.ilike(f'%{keyword}%'))
        rows = query.order_by(Workflow.updated_at.desc()).limit(max(1, min(limit, 100))).all()
        return _json([{
            'id': w.id,
            'name': w.name,
            'description': w.description,
            'steps': w.nodes.count(),
            'enabled': w.enabled,
            'updated_at': w.updated_at.isoformat() if w.updated_at else None,
        } for w in rows])


@server.tool()
def get_pipeline(pipeline_id: int) -> str:
    """获取管道详情：按执行顺序排列的步骤（脚本名/步骤参数/延时）"""
    with _ctx():
        wf = db.session.get(Workflow, pipeline_id)
        if wf is None:
            raise ValueError(f'管道不存在: {pipeline_id}')

        def _order(node_id):
            digits = ''.join(ch for ch in str(node_id) if ch.isdigit())
            return int(digits) if digits else 10 ** 6

        steps = []
        for node in sorted(wf.nodes.all(), key=lambda n: _order(n.node_id)):
            try:
                cfg = json.loads(node.config) if node.config else {}
            except (json.JSONDecodeError, TypeError):
                cfg = {}
            if node.node_type == 'delay':
                steps.append({'index': len(steps) + 1, 'type': 'delay', 'delay_seconds': cfg.get('delay', 0)})
            else:
                steps.append({
                    'index': len(steps) + 1,
                    'type': 'script',
                    'script_id': node.script_id,
                    'script_name': node.script.name if node.script else None,
                    'params': cfg.get('params') or {},
                })
        return _json({
            'id': wf.id,
            'name': wf.name,
            'description': wf.description,
            'enabled': wf.enabled,
            'steps': steps,
        })


@server.tool()
def run_workflow(workflow_id: int = None, workflow_name: str = None,
                 params: dict = None, wait_seconds: int = 60) -> str:
    """执行管道（线性工作流；二选一传 workflow_id 或 workflow_name）。

    params 为管道级参数（步骤级参数在管道定义中，优先级更高）。
    管道步骤顺序执行、失败即停，步骤间数据经共享工作流空间文件传递。
    超时未结束返回 workflow_execution_id（status=running），用
    wait_workflow_execution 跟踪。
    """
    with _ctx():
        if workflow_id:
            wf = db.session.get(Workflow, workflow_id)
        elif workflow_name:
            wf = Workflow.query.filter_by(name=workflow_name).first()
        else:
            raise ValueError('必须提供 workflow_id 或 workflow_name')
        if wf is None:
            raise ValueError('工作流不存在')
        if not wf.enabled:
            raise ValueError('工作流已禁用')

        execution = WorkflowExecution(
            workflow_id=wf.id,
            status='pending',
            params=json.dumps(params or {}, ensure_ascii=False),
        )
        db.session.add(execution)
        db.session.commit()
        wf_exec_id = execution.id

    app_obj = app

    def _run():
        with app_obj.app_context():
            execute_workflow_async(wf_exec_id)

    threading.Thread(target=_run, daemon=True).start()

    with _ctx():
        final = _wait_terminal(WorkflowExecution, wf_exec_id, wait_seconds)
        if final is not None:
            return _json(_workflow_brief(final))
        return _json({'status': 'running', 'workflow_execution_id': wf_exec_id,
                      'message': f'{wait_seconds}s 内未结束，请用 wait_workflow_execution 跟踪'})


@server.tool()
def wait_workflow_execution(workflow_execution_id: int, timeout_seconds: int = 120) -> str:
    """阻塞等待工作流执行到终态，返回总体状态与各节点状态"""
    with _ctx():
        final = _wait_terminal(WorkflowExecution, workflow_execution_id, timeout_seconds)
        if final is None:
            return _json({'status': 'running', 'workflow_execution_id': workflow_execution_id})
        return _json(_workflow_brief(final))


def _execution_brief(record):
    data = record.to_dict()
    # params 原文对 MCP 调用方意义不大，剔除以控制返回体积
    data.pop('params', None)
    return data


def _workflow_brief(record):
    node_execs = [
        {'node_id': ne.node_id, 'status': ne.status, 'error': ne.error}
        for ne in record.node_executions
    ] if hasattr(record, 'node_executions') else []
    return {
        'id': record.id,
        'workflow_id': record.workflow_id,
        'status': record.status,
        'error': record.error,
        'nodes': node_execs,
    }


# ---------------- 传输与鉴权 ----------------


class _TokenMiddleware:
    """Streamable HTTP 模式下的可选 Bearer 鉴权（MCP_TOKEN 设置后启用）"""

    def __init__(self, asgi_app, token):
        self.app = asgi_app
        self.token = token

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            headers = {k.decode('latin-1').lower(): v.decode('latin-1')
                       for k, v in scope.get('headers', [])}
            provided = headers.get('authorization', '')
            expected = f'Bearer {self.token}'
            if not hmac.compare_digest(provided, expected):
                body = json.dumps({'error': 'unauthorized',
                                   'message': '需要 Bearer MCP_TOKEN'}).encode()
                await send({'type': 'http.response.start', 'status': 401,
                            'headers': [(b'content-type', b'application/json'),
                                        (b'content-length', str(len(body)).encode())]})
                await send({'type': 'http.response.body', 'body': body})
                return
        await self.app(scope, receive, send)


def main():
    parser = argparse.ArgumentParser(description='脚本工具管理系统 MCP 服务器')
    parser.add_argument('--transport', choices=['streamable-http', 'stdio'],
                        default='streamable-http')
    args = parser.parse_args()

    if args.transport == 'stdio':
        server.run(transport='stdio')
        return

    host = os.environ.get('MCP_HOST', '127.0.0.1')
    port = int(os.environ.get('MCP_PORT', '8808'))
    token = os.environ.get('MCP_TOKEN', '').strip()

    asgi_app = server.streamable_http_app()
    if token:
        asgi_app = _TokenMiddleware(asgi_app, token)

    print(f'[MCP] http://{host}:{port}/mcp  鉴权: {"Bearer MCP_TOKEN" if token else "未启用"}')
    import uvicorn
    uvicorn.run(asgi_app, host=host, port=port, log_level='warning')


if __name__ == '__main__':
    main()
