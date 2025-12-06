"""
全局变量数据模型
"""
from datetime import datetime
from models import db


class GlobalVariable(db.Model):
    """全局变量模型"""
    __tablename__ = 'global_variables'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), nullable=False, unique=True)  # 变量名（唯一）
    value = db.Column(db.Text, nullable=False)  # 变量值
    description = db.Column(db.Text)  # 描述
    is_encrypted = db.Column(db.Boolean, default=False)  # 是否加密存储
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, show_value=True):
        """转换为字典"""
        result = {
            'id': self.id,
            'key': self.key,
            'description': self.description,
            'is_encrypted': self.is_encrypted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        # 如果是加密变量，默认不返回值（除非明确要求）
        if self.is_encrypted and not show_value:
            result['value'] = '******'
        else:
            result['value'] = self.value

        return result
