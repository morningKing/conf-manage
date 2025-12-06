"""
工作流模板数据模型
"""
from datetime import datetime
from models import db
import json


class WorkflowTemplate(db.Model):
    """工作流模板模型"""
    __tablename__ = 'workflow_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # 模板分类：数据处理、API调用、文件操作等
    icon = db.Column(db.String(50))  # 图标名称
    template_config = db.Column(db.Text, nullable=False)  # JSON格式的模板配置（节点和边）
    is_builtin = db.Column(db.Boolean, default=False)  # 是否为内置模板
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        template_config = json.loads(self.template_config) if self.template_config else {}
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'icon': self.icon,
            'template_config': template_config,
            'is_builtin': self.is_builtin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
