"""
数据模型初始化
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .script import Script, ScriptVersion
from .execution import Execution
from .schedule import Schedule
from .environment import Environment
from .folder import Folder
from .category import Tag, script_tags
from .workflow import Workflow, WorkflowNode, WorkflowEdge, WorkflowExecution, WorkflowNodeExecution
from .workflow_template import WorkflowTemplate
from .global_variable import GlobalVariable
from .ai_config import AIConfig
from .webhook import Webhook, WebhookLog
from .selection_session import SelectionSession

__all__ = [
    'db', 'Script', 'ScriptVersion', 'Execution', 'Schedule', 'Environment',
    'Folder', 'Tag', 'script_tags', 'Workflow', 'WorkflowNode', 'WorkflowEdge',
    'WorkflowExecution', 'WorkflowNodeExecution', 'WorkflowTemplate', 'GlobalVariable',
    'AIConfig', 'Webhook', 'WebhookLog', 'SelectionSession'
]
