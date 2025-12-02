"""
执行记录模型
"""
from datetime import datetime
from . import db


class Execution(db.Model):
    """执行记录表"""
    __tablename__ = 'executions'

    id = db.Column(db.Integer, primary_key=True)
    script_id = db.Column(db.Integer, db.ForeignKey('scripts.id'), nullable=False)
    environment_id = db.Column(db.Integer, db.ForeignKey('environments.id'), nullable=True)  # 实际使用的执行环境
    status = db.Column(db.String(20), nullable=False)  # pending, running, success, failed
    progress = db.Column(db.Integer, default=0)  # 执行进度 0-100
    stage = db.Column(db.String(50), default='pending')  # 执行阶段: pending, preparing, installing_deps, running, finishing
    pid = db.Column(db.Integer)  # 进程ID，用于中断执行
    params = db.Column(db.Text)  # JSON格式存储参数
    output = db.Column(db.Text)  # 执行输出
    error = db.Column(db.Text)  # 错误信息
    log_file = db.Column(db.String(255))  # 日志文件路径
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    environment = db.relationship('Environment', backref='executions', foreign_keys=[environment_id])

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'script_id': self.script_id,
            'script_name': self.script.name if self.script else None,
            'environment_id': self.environment_id,
            'environment_name': self.environment.name if self.environment else None,
            'status': self.status,
            'progress': self.progress or 0,
            'stage': self.stage or 'pending',
            'pid': self.pid,
            'params': self.params,
            'output': self.output,
            'error': self.error,
            'log_file': self.log_file,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
