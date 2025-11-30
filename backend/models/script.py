"""
脚本模型
"""
from datetime import datetime
from . import db


class Script(db.Model):
    """脚本表"""
    __tablename__ = 'scripts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    type = db.Column(db.String(20), nullable=False)  # python, javascript
    code = db.Column(db.Text, nullable=False)
    dependencies = db.Column(db.Text)  # JSON格式存储依赖
    parameters = db.Column(db.Text)  # JSON格式存储参数定义 [{"key": "param1", "description": "参数说明", "default_value": "默认值", "required": true}]
    version = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    versions = db.relationship('ScriptVersion', backref='script', lazy='dynamic', cascade='all, delete-orphan')
    executions = db.relationship('Execution', backref='script', lazy='dynamic', cascade='all, delete-orphan')
    schedules = db.relationship('Schedule', backref='script', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'code': self.code,
            'dependencies': self.dependencies,
            'parameters': self.parameters,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ScriptVersion(db.Model):
    """脚本版本表"""
    __tablename__ = 'script_versions'

    id = db.Column(db.Integer, primary_key=True)
    script_id = db.Column(db.Integer, db.ForeignKey('scripts.id'), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    code = db.Column(db.Text, nullable=False)
    dependencies = db.Column(db.Text)  # JSON格式存储依赖
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'script_id': self.script_id,
            'version': self.version,
            'code': self.code,
            'dependencies': self.dependencies,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
