"""
定时任务模型
"""
from datetime import datetime
from . import db


class Schedule(db.Model):
    """定时任务表"""
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    script_id = db.Column(db.Integer, db.ForeignKey('scripts.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    cron = db.Column(db.String(100), nullable=False)  # Cron表达式
    params = db.Column(db.Text)  # JSON格式存储参数
    enabled = db.Column(db.Boolean, default=True)
    last_run = db.Column(db.DateTime)  # 上次执行时间
    next_run = db.Column(db.DateTime)  # 下次执行时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'script_id': self.script_id,
            'script_name': self.script.name if self.script else None,
            'name': self.name,
            'description': self.description,
            'cron': self.cron,
            'params': self.params,
            'enabled': self.enabled,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
