"""
AI配置模型
"""
from datetime import datetime
from . import db


class AIConfig(db.Model):
    """AI配置表"""
    __tablename__ = 'ai_configs'

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False, default='openai')  # openai, anthropic, custom
    api_key = db.Column(db.String(500), nullable=False)
    base_url = db.Column(db.String(500))
    model = db.Column(db.String(100), default='gpt-4')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'provider': self.provider,
            'api_key': self.api_key[:10] + '...' if self.api_key else '',  # 只返回前10位
            'base_url': self.base_url,
            'model': self.model,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
