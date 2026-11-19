# -*- coding: utf-8 -*-
"""
E2E 测试夹具：启动真实服务进程（子进程，端口 5101，独立 PG 库 confmanage_e2e），
通过 HTTP 验证完整链路（真实 Werkzeug/SocketIO 服务、真实子进程脚本执行、SSE 流）。
"""
import os
import subprocess
import sys
import tempfile
import time

import pytest
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dbsetup import server_env  # noqa: E402

BASE_PORT = os.environ.get('E2E_PORT', '5101')
BASE_URL = f'http://localhost:{BASE_PORT}'
STARTUP_TIMEOUT = 60

_server_proc = None


def _assert_port_free():
    """端口预检：Windows 的 SO_REUSEADDR 语义允许多进程绑定同一端口，
    旧进程残留会导致请求被路由到僵尸进程而全部超时。"""
    import socket
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        probe.bind(('127.0.0.1', int(BASE_PORT)))
    except OSError:
        raise RuntimeError(
            f'端口 {BASE_PORT} 已被占用（可能有残留的服务进程），'
            f'请先清理: netstat -ano | findstr :{BASE_PORT}')
    finally:
        probe.close()


def _start_server():
    global _server_proc
    _assert_port_free()
    env = server_env()
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 服务输出写入文件（不能接 PIPE：无人读取时写满缓冲会阻塞整个服务）
    log_path = os.path.join(tempfile.gettempdir(), f'e2e_server_{BASE_PORT}.log')
    log_fh = open(log_path, 'w', encoding='utf-8')
    proc = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd=backend_dir, env=env,
        stdout=log_fh, stderr=subprocess.STDOUT,
    )
    deadline = time.time() + STARTUP_TIMEOUT
    while time.time() < deadline:
        if proc.poll() is not None:
            log_fh.close()
            with open(log_path, encoding='utf-8') as f:
                out = f.read()
            raise RuntimeError(f'E2E 服务启动失败:\n{out[-2000:]}')
        try:
            r = requests.get(f'{BASE_URL}/health', timeout=2)
            if r.status_code == 200:
                return proc
        except requests.ConnectionError:
            time.sleep(0.5)
    proc.kill()
    log_fh.close()
    raise RuntimeError(f'E2E 服务 {STARTUP_TIMEOUT}s 内未就绪, 日志: {log_path}')


def _stop_server(proc):
    if proc is None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except Exception:
        proc.kill()


@pytest.fixture(scope='session', autouse=True)
def e2e_server():
    global _server_proc
    _server_proc = _start_server()
    yield BASE_URL
    _stop_server(_server_proc)
    _server_proc = None


@pytest.fixture(scope='session')
def base_url():
    return BASE_URL


@pytest.fixture(scope='session')
def api():
    """带统一 payload 解包的 HTTP 客户端"""
    from helpers import Api
    return Api(BASE_URL)
