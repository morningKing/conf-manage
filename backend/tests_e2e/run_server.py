# -*- coding: utf-8 -*-
"""
Playwright webServer 入口：先装配 E2E 数据库，再以 E2E 环境启动后端。

确保被测服务绝不连接用户的业务库 confmanage。
"""
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(HERE)

sys.path.insert(0, HERE)
from dbsetup import server_env  # noqa: E402

os.environ.update(server_env())
runpy.run_path(os.path.join(BACKEND_DIR, 'app.py'), run_name='__main__')
