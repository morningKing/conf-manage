"""
AI配置模型
"""
from datetime import datetime, timezone
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
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'provider': self.provider,
            'api_key': ('...' + self.api_key[-4:]) if self.api_key else '',  # 仅返回尾 4 位掩码
            'is_configured': bool(self.api_key),
            'base_url': self.base_url,
            'model': self.model,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
