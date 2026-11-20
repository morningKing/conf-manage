# -*- coding: utf-8 -*-
"""
MCP 服务器 E2E 测试

以独立子进程启动 MCP 服务器（streamable-http + Bearer 鉴权），
用 MCP 官方客户端走完整协议：列工具 → 无鉴权被拒 → 建脚本 →
run_script → 结果断言 → cancel 路径。
"""
import asyncio
import json
import os
import socket
import subprocess
import sys
import tempfile
import time

import pytest
import requests

MCP_PORT = int(os.environ.get('E2E_MCP_PORT', '5102'))
MCP_TOKEN = 'e2e-mcp-token'
STARTUP_TIMEOUT = 60

_server_proc = None


def _wait_port(port, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            if s.connect_ex(('127.0.0.1', port)) == 0:
                return True
        time.sleep(0.5)
    return False


@pytest.fixture(scope='module', autouse=True)
def mcp_server(db_url):
    global _server_proc
    assert db_url, 'MCP 测试依赖 E2E 数据库连接串'
    env = os.environ.copy()
    env.update({
        'DATABASE_URL': db_url,
        'MCP_PORT': str(MCP_PORT),
        'MCP_TOKEN': MCP_TOKEN,
        'HOST_DEBUG': 'false',
    })
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_path = os.path.join(tempfile.gettempdir(), f'e2e_mcp_{MCP_PORT}.log')
    log_fh = open(log_path, 'w', encoding='utf-8')
    proc = subprocess.Popen(
        [sys.executable, 'mcp_server.py', '--transport', 'streamable-http'],
        cwd=backend_dir, env=env,
        stdout=log_fh, stderr=subprocess.STDOUT,
    )
    if not _wait_port(MCP_PORT, STARTUP_TIMEOUT):
        proc.kill()
        log_fh.close()
        with open(log_path, encoding='utf-8') as f:
            raise RuntimeError(f'MCP 服务 {STARTUP_TIMEOUT}s 内未监听端口:\n{f.read()[-2000:]}')
    _server_proc = proc
    time.sleep(1)  # 等待 ASGI 应用完全就绪
    yield f'http://127.0.0.1:{MCP_PORT}/mcp'
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except Exception:
        proc.kill()
    _server_proc = None


def _mcp_call(tool, arguments, token=MCP_TOKEN, port=MCP_PORT):
    """同步封装：MCP 客户端调用工具，返回 CallToolResult"""
    import httpx
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    async def _inner():
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        async with streamable_http_client(
                f'http://127.0.0.1:{port}/mcp',
                http_client=httpx.AsyncClient(headers=headers, timeout=30)) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await session.call_tool(tool, arguments)

    return asyncio.run(_inner())


def _mcp_list_tools(token=MCP_TOKEN, port=MCP_PORT):
    import httpx
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    async def _inner():
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        async with streamable_http_client(
                f'http://127.0.0.1:{port}/mcp',
                http_client=httpx.AsyncClient(headers=headers, timeout=30)) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await session.list_tools()

    return asyncio.run(_inner())


def _result_text(result):
    assert not result.is_error, f'MCP 工具返回错误: {result.content}'
    assert result.content, 'MCP 工具返回为空'
    return result.content[0].text


def test_mcp_rejects_missing_token(mcp_server):
    with pytest.raises(Exception):
        _mcp_list_tools(token=None)
    with pytest.raises(Exception):
        _mcp_list_tools(token='wrong-token')


def test_mcp_lists_expected_tools(mcp_server):
    tools = _mcp_list_tools()
    names = {t.name for t in tools.tools}
    assert {'list_scripts', 'get_script', 'run_script', 'wait_execution',
            'get_execution', 'list_executions', 'cancel_execution',
            'run_workflow', 'wait_workflow_execution',
            'list_pipelines', 'get_pipeline'} <= names


def test_mcp_run_script_end_to_end(api, mcp_server):
    marker = f'mcp-marker-{int(time.time() * 1000)}'
    script = api.create_script(code=(
        'import os\n'
        'print("MCP OUTPUT:", os.environ.get("MCP_PARAM", ""))\n'
    ))
    try:
        result = _mcp_call('run_script', {
            'script_id': script['id'],
            'params': {'MCP_PARAM': marker},
            'wait_seconds': 90,
        })
        data = json.loads(_result_text(result))
        assert data['status'] == 'success', data
        assert f'MCP OUTPUT: {marker}' in (data.get('output') or '')

        # get_execution 复核
        detail = json.loads(_result_text(_mcp_call(
            'get_execution', {'execution_id': data['id']})))
        assert detail['status'] == 'success'
        assert 'MCP OUTPUT' in (detail.get('output') or '')
    finally:
        api.delete(script['id'])


def test_mcp_list_and_get_script(api, mcp_server):
    script = api.create_script(code='print("mcp query")',
                               name=f'mcp_query_{int(time.time() * 1000) % 10**9}')
    try:
        listed = json.loads(_result_text(_mcp_call(
            'list_scripts', {'keyword': script['name'][:10]})))
        assert any(s['id'] == script['id'] for s in listed)

        detail = json.loads(_result_text(_mcp_call(
            'get_script', {'script_id': script['id']})))
        assert detail['code'] == 'print("mcp query")'
    finally:
        api.delete(script['id'])


def test_mcp_cancel_running(api, mcp_server):
    script = api.create_script(code='import time\nprint("started")\ntime.sleep(60)\n')
    try:
        result = _mcp_call('run_script', {'script_id': script['id'], 'wait_seconds': 2})
        data = json.loads(_result_text(result))
        exec_id = data['execution_id'] if data['status'] == 'running' else data['id']

        cancel = json.loads(_result_text(_mcp_call(
            'cancel_execution', {'execution_id': exec_id})))
        assert cancel['status'] in ('failed', 'cancelled'), cancel
    finally:
        api.delete(script['id'])


def test_mcp_pipeline_tools(api, mcp_server):
    """MCP 管道工具：list_pipelines / get_pipeline / run_workflow"""
    s1 = api.create_script(code='print("mcp pipe a")')
    s2 = api.create_script(code='print("mcp pipe b")')
    name = f'mcp_pipe_{int(time.time() * 1000) % 10**9}'
    wf = api.payload(api.post('/workflows', {
        'name': name,
        'nodes': [
            {'node_id': 'node_1', 'node_type': 'script', 'script_id': s1['id'],
             'config': {'params': {'STEP': 'one'}}, 'position': {'x': 0, 'y': 0}},
            {'node_id': 'node_2', 'node_type': 'script', 'script_id': s2['id'],
             'config': {}, 'position': {'x': 100, 'y': 0}},
        ],
        'edges': [{'edge_id': 'edge_1', 'source': 'node_1', 'target': 'node_2'}],
        'enabled': True,
    }))
    try:
        # list_pipelines 能找到
        listed = json.loads(_result_text(_mcp_call(
            'list_pipelines', {'keyword': name[:12]})))
        assert any(p['id'] == wf['id'] and p['steps'] == 2 for p in listed), listed

        # get_pipeline 返回有序步骤与步骤参数
        detail = json.loads(_result_text(_mcp_call(
            'get_pipeline', {'pipeline_id': wf['id']})))
        assert [st['index'] for st in detail['steps']] == [1, 2]
        assert detail['steps'][0]['script_id'] == s1['id']
        assert detail['steps'][0]['params'] == {'STEP': 'one'}

        # run_workflow 端到端
        run = json.loads(_result_text(_mcp_call(
            'run_workflow', {'workflow_name': name, 'wait_seconds': 90})))
        assert run['status'] == 'success', run
        statuses = {n['node_id']: n['status'] for n in run['nodes']}
        assert statuses == {'node_1': 'success', 'node_2': 'success'}
    finally:
        api.delete(f"/workflows/{wf['id']}")
        api.delete(s1['id'])
        api.delete(s2['id'])
