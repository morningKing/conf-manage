"""
数据模型初始化
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .script import Script, ScriptVersion
from .execution import Execution
from .schedule import Schedule
from .environment import Environment
from .category import Category, Tag, script_tags
from .workflow import Workflow, WorkflowNode, WorkflowEdge, WorkflowExecution, WorkflowNodeExecution
from .workflow_template import WorkflowTemplate
from .global_variable import GlobalVariable

__all__ = [
    'db', 'Script', 'ScriptVersion', 'Execution', 'Schedule', 'Environment',
    'Category', 'Tag', 'script_tags', 'Workflow', 'WorkflowNode', 'WorkflowEdge',
    'WorkflowExecution', 'WorkflowNodeExecution', 'WorkflowTemplate', 'GlobalVariable'
]
