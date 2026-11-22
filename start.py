#!/usr/bin/env python3
"""
一键启动前后端

流程：
  1. 加载根目录 .env（不覆盖已有环境变量）
  2. 预检：Python/Node 可用、PostgreSQL 可达、后端/前端端口空闲
  3. Python 依赖缺失时给出安装指引；frontend/node_modules 缺失时提示先 npm install
  4. 通过 Alembic Python API 执行迁移（等价的 alembic upgrade head，幂等）
  5. 并行启动后端（app.py）与前端（node 直启 vite），Ctrl+C / 任一子进程退出即整体停止

用法：
  python start.py                 # 默认：后端端口取 HOST_PORT（5001），前端 5177
  python start.py --skip-migrate  # 跳过数据库迁移（例如已手动迁移过）
"""
import argparse
import os
import shutil
import socket
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT, 'backend')
FRONTEND_DIR = os.path.join(ROOT, 'frontend')
FRONTEND_PORT = 5177


def log(tag, msg):
    print(f'[{tag}] {msg}', flush=True)


def load_env_file():
    """加载仓库根目录 .env（不覆盖已有环境变量）"""
    env_path = os.path.join(ROOT, '.env')
    if not os.path.exists(env_path):
        log('warn', '未找到 .env，使用默认配置（可 `cp .env.example .env` 后修改）')
        return
    with open(env_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    log('env', '已加载 .env')


def port_in_use(port, host='127.0.0.1'):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def ensure_python_deps():
    """检查后端运行依赖；缺失时给出明确的安装指引"""
    missing = []
    for module in ('flask', 'flask_sqlalchemy', 'sqlalchemy', 'psycopg2', 'alembic'):
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    if missing:
        sys.exit('[error] 缺少 Python 依赖: ' + ', '.join(missing) +
                 '\n        请先执行: pip install -r requirements.txt')


def check_frontend_deps():
    """检查 node 与 vite（前端依赖由用户在 frontend 目录 npm install）"""
    node = shutil.which('node')
    if not node:
        sys.exit('[error] 未找到 Node.js，请先安装')
    vite_main = os.path.join(FRONTEND_DIR, 'node_modules', 'vite', 'bin', 'vite.js')
    if not os.path.isfile(vite_main):
        sys.exit('[error] 前端依赖缺失，请先执行：cd frontend && npm install')
    return node, vite_main


def check_postgres():
    host = os.environ.get('DB_HOST', 'localhost')
    try:
        port = int(os.environ.get('DB_PORT', '5432'))
    except ValueError:
        port = 5432
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(2)
        if s.connect_ex((host, port)) != 0:
            sys.exit(f'[error] 无法连接 PostgreSQL {host}:{port}，请确认数据库已启动且 .env 配置正确')
    log('check', f'PostgreSQL 可达 {host}:{port}')


def run_migrations():
    """经 Alembic Python API 执行 upgrade head（不经过子进程/shell）"""
    log('db', '执行迁移：upgrade head ...')
    sys.path.insert(0, BACKEND_DIR)
    from alembic import command
    from alembic.config import Config as AlembicConfig
    cfg = AlembicConfig(os.path.join(BACKEND_DIR, 'alembic.ini'))
    cfg.set_main_option('script_location', os.path.join(BACKEND_DIR, 'migrations'))
    command.upgrade(cfg, 'head')
    log('db', '迁移完成')


def main():
    parser = argparse.ArgumentParser(description='一键启动前后端')
    parser.add_argument('--skip-migrate', action='store_true', help='跳过 Alembic 迁移')
    args = parser.parse_args()

    load_env_file()
    backend_port = int(os.environ.get('HOST_PORT', '5001'))

    for name, port in (('后端', backend_port), ('前端', FRONTEND_PORT)):
        if port_in_use(port):
            sys.exit(f'[error] {name}端口 {port} 已被占用，请先释放（netstat -ano | findstr :{port}）')

    ensure_python_deps()
    node_exe, vite_main = check_frontend_deps()
    check_postgres()
    if not args.skip_migrate:
        run_migrations()

    log('run', f'启动后端 http://localhost:{backend_port}')
    backend = subprocess.Popen([sys.executable, 'app.py'], cwd=BACKEND_DIR)

    frontend_env = os.environ.copy()
    frontend_env['VITE_PROXY_TARGET'] = f'http://localhost:{backend_port}'
    log('run', f'启动前端 http://localhost:{FRONTEND_PORT}')
    frontend = subprocess.Popen(
        [node_exe, vite_main, '--port', str(FRONTEND_PORT), '--strictPort'],
        cwd=FRONTEND_DIR, env=frontend_env)

    print('=' * 60, flush=True)
    print(f'  前端入口: http://localhost:{FRONTEND_PORT}', flush=True)
    print(f'  后端健康: http://localhost:{backend_port}/health', flush=True)
    print('  按 Ctrl+C 停止全部服务', flush=True)
    print('=' * 60, flush=True)

    try:
        while True:
            if backend.poll() is not None:
                log('exit', f'后端已退出（code={backend.returncode}），停止前端')
                break
            if frontend.poll() is not None:
                log('exit', f'前端已退出（code={frontend.returncode}），停止后端')
                break
            time.sleep(1)
    except KeyboardInterrupt:
        log('stop', '收到 Ctrl+C，正在停止 ...')
    finally:
        for proc in (frontend, backend):
            if proc.poll() is None:
                proc.terminate()
        log('stop', '已停止')


if __name__ == '__main__':
    main()
