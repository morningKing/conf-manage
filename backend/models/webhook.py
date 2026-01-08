"""
Webhook模型
"""
from datetime import datetime
from . import db
import secrets


class Webhook(db.Model):
    """Webhook表"""
    __tablename__ = 'webhooks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    script_id = db.Column(db.Integer, db.ForeignKey('scripts.id'), nullable=False)

    # Webhook唯一标识符（URL路径）
    webhook_key = db.Column(db.String(64), nullable=False, unique=True, index=True)

    # 安全配置
    token_enabled = db.Column(db.Boolean, default=False)  # 是否启用Token验证
    token = db.Column(db.String(128))  # 验证Token（启用时生成）

    # 执行模式
    execution_mode = db.Column(db.String(20), default='async')  # 'sync' 或 'async'
    timeout = db.Column(db.Integer, default=30)  # 同步模式超时时间（秒）

    # 参数传递配置
    pass_full_request = db.Column(db.Boolean, default=True)  # 是否保存完整请求信息

    # 状态和统计
    enabled = db.Column(db.Boolean, default=True)
    call_count = db.Column(db.Integer, default=0)  # 调用次数
    success_count = db.Column(db.Integer, default=0)  # 成功次数
    failed_count = db.Column(db.Integer, default=0)  # 失败次数
    last_called_at = db.Column(db.DateTime)  # 最后调用时间

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    script = db.relationship('Script', backref='webhooks')

    def __init__(self, **kwargs):
        super(Webhook, self).__init__(**kwargs)
        if not self.webhook_key:
            self.webhook_key = self.generate_webhook_key()
        if self.token_enabled and not self.token:
            self.token = self.generate_token()

    @staticmethod
    def generate_webhook_key():
        """生成唯一的webhook key"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_token():
        """生成验证token"""
        return secrets.token_urlsafe(48)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'script_id': self.script_id,
            'script_name': self.script.name if self.script else None,
            'webhook_key': self.webhook_key,
            'webhook_url': f'/api/webhook/{self.webhook_key}',
            'token_enabled': self.token_enabled,
            'token': self.token if self.token_enabled else None,
            'execution_mode': self.execution_mode,
            'timeout': self.timeout,
            'pass_full_request': self.pass_full_request,
            'enabled': self.enabled,
            'call_count': self.call_count,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'last_called_at': self.last_called_at.isoformat() if self.last_called_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class WebhookLog(db.Model):
    """Webhook调用日志表"""
    __tablename__ = 'webhook_logs'

    id = db.Column(db.Integer, primary_key=True)
    webhook_id = db.Column(db.Integer, db.ForeignKey('webhooks.id'), nullable=False)
    execution_id = db.Column(db.Integer, db.ForeignKey('executions.id'), nullable=True)

    # 请求信息
    request_method = db.Column(db.String(10))  # GET, POST, PUT等
    request_headers = db.Column(db.Text)  # JSON格式
    request_body = db.Column(db.Text)  # JSON格式
    request_query = db.Column(db.Text)  # JSON格式
    request_ip = db.Column(db.String(50))  # 请求IP

    # 响应信息
    status = db.Column(db.String(20))  # 'success', 'failed', 'unauthorized'
    response_code = db.Column(db.Integer)  # HTTP状态码
    response_body = db.Column(db.Text)  # 响应内容
    error_message = db.Column(db.Text)  # 错误信息

    # 执行时间
    duration_ms = db.Column(db.Integer)  # 执行耗时（毫秒）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    webhook = db.relationship('Webhook', backref='logs')
    execution = db.relationship('Execution', backref='webhook_logs')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'webhook_id': self.webhook_id,
            'execution_id': self.execution_id,
            'request_method': self.request_method,
            'request_headers': self.request_headers,
            'request_body': self.request_body,
            'request_query': self.request_query,
            'request_ip': self.request_ip,
            'status': self.status,
            'response_code': self.response_code,
            'response_body': self.response_body,
            'error_message': self.error_message,
            'duration_ms': self.duration_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
