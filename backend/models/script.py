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
    environment_id = db.Column(db.Integer, db.ForeignKey('environments.id'), nullable=True)  # 执行环境ID
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)  # 分类ID
    is_favorite = db.Column(db.Boolean, default=False)  # 是否收藏
    version = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    environment = db.relationship('Environment', backref='scripts', foreign_keys=[environment_id])
    category = db.relationship('Category', backref='scripts', foreign_keys=[category_id])
    tags = db.relationship('Tag', secondary='script_tags', backref=db.backref('scripts', lazy='dynamic'))
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
            'environment_id': self.environment_id,
            'category_id': self.category_id,
            'is_favorite': self.is_favorite,
            'category': self.category.to_dict() if self.category else None,
            'tags': [tag.to_dict() for tag in self.tags] if self.tags else [],
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
