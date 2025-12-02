"""
API路由初始化
"""
from flask import Blueprint

# 创建蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

# 导入路由
from . import scripts, executions, schedules, files, environments

__all__ = ['api_bp']
