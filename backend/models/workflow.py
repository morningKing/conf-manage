"""
工作流数据模型
"""
from datetime import datetime
from models import db
import json


class Workflow(db.Model):
    """工作流模型"""
    __tablename__ = 'workflows'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    config = db.Column(db.Text, nullable=False)  # JSON格式的工作流配置
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    nodes = db.relationship('WorkflowNode', backref='workflow', lazy='dynamic', cascade='all, delete-orphan')
    executions = db.relationship('WorkflowExecution', backref='workflow', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        """转换为字典"""
        config = json.loads(self.config) if self.config else {}
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'config': config,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'nodes_count': self.nodes.count()
        }


class WorkflowNode(db.Model):
    """工作流节点模型"""
    __tablename__ = 'workflow_nodes'

    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflows.id'), nullable=False)
    node_id = db.Column(db.String(50), nullable=False)  # 节点唯一标识
    node_type = db.Column(db.String(20), nullable=False)  # script, condition, parallel, delay
    script_id = db.Column(db.Integer, db.ForeignKey('scripts.id'), nullable=True)  # 脚本节点关联的脚本
    config = db.Column(db.Text)  # JSON格式的节点配置
    position_x = db.Column(db.Integer, default=0)  # 节点X坐标
    position_y = db.Column(db.Integer, default=0)  # 节点Y坐标
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    script = db.relationship('Script', backref='workflow_nodes')

    def to_dict(self):
        """转换为字典"""
        config = json.loads(self.config) if self.config else {}
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'node_id': self.node_id,
            'node_type': self.node_type,
            'script_id': self.script_id,
            'script': self.script.to_dict() if self.script else None,
            'config': config,
            'position': {
                'x': self.position_x,
                'y': self.position_y
            },
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class WorkflowEdge(db.Model):
    """工作流边（连接）模型"""
    __tablename__ = 'workflow_edges'

    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflows.id'), nullable=False)
    edge_id = db.Column(db.String(50), nullable=False)  # 边唯一标识
    source_node_id = db.Column(db.String(50), nullable=False)  # 源节点ID
    target_node_id = db.Column(db.String(50), nullable=False)  # 目标节点ID
    condition = db.Column(db.Text)  # JSON格式的条件配置
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    workflow = db.relationship('Workflow', backref='edges')

    def to_dict(self):
        """转换为字典"""
        condition = json.loads(self.condition) if self.condition else None
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'edge_id': self.edge_id,
            'source': self.source_node_id,
            'target': self.target_node_id,
            'condition': condition,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class WorkflowExecution(db.Model):
    """工作流执行记录模型"""
    __tablename__ = 'workflow_executions'

    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflows.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # pending, running, success, failed, cancelled
    params = db.Column(db.Text)  # JSON格式的执行参数
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    error = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    node_executions = db.relationship('WorkflowNodeExecution', backref='workflow_execution', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        """转换为字典"""
        params = json.loads(self.params) if self.params else {}
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'workflow': self.workflow.to_dict() if self.workflow else None,
            'status': self.status,
            'params': params,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'error': self.error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'duration': (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else None
        }


class WorkflowNodeExecution(db.Model):
    """工作流节点执行记录模型"""
    __tablename__ = 'workflow_node_executions'

    id = db.Column(db.Integer, primary_key=True)
    workflow_execution_id = db.Column(db.Integer, db.ForeignKey('workflow_executions.id'), nullable=False)
    node_id = db.Column(db.String(50), nullable=False)
    execution_id = db.Column(db.Integer, db.ForeignKey('executions.id'), nullable=True)  # 关联的脚本执行记录
    status = db.Column(db.String(20), nullable=False)  # pending, running, success, failed, skipped
    output = db.Column(db.Text)
    error = db.Column(db.Text)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    execution = db.relationship('Execution', backref='workflow_node_executions')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'workflow_execution_id': self.workflow_execution_id,
            'node_id': self.node_id,
            'execution_id': self.execution_id,
            'execution': self.execution.to_dict() if self.execution else None,
            'status': self.status,
            'output': self.output,
            'error': self.error,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'duration': (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else None
        }
