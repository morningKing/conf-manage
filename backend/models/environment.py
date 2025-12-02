from . import db
from datetime import datetime

class Environment(db.Model):
    """执行环境模型"""
    __tablename__ = 'environments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # 环境名称
    type = db.Column(db.String(20), nullable=False)  # python 或 javascript
    executable_path = db.Column(db.String(500), nullable=False)  # 解释器路径
    description = db.Column(db.Text)  # 描述
    is_default = db.Column(db.Boolean, default=False)  # 是否为默认环境
    version = db.Column(db.String(50))  # 版本信息（自动检测）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'executable_path': self.executable_path,
            'description': self.description,
            'is_default': self.is_default,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
