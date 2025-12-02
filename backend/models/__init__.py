"""
数据模型初始化
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .script import Script, ScriptVersion
from .execution import Execution
from .schedule import Schedule
from .environment import Environment

__all__ = ['db', 'Script', 'ScriptVersion', 'Execution', 'Schedule', 'Environment']
