"""
统一 API 错误处理

- ApiError：业务错误，路由层 raise ApiError('消息', status=400) 即可
- HTTPException：404/405 等统一返回 JSON（不再被 try/except 吞成 500）
- Exception：全局兜底
"""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """业务错误：携带 HTTP 状态码，由全局 handler 转为统一 JSON 响应"""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def register_error_handlers(app):
    """注册全局错误处理（替代各路由重复的 try/except 样板）"""

    @app.errorhandler(ApiError)
    def handle_api_error(e):
        return jsonify({'code': 1, 'message': e.message}), e.status

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        code = e.code or 500
        message = '资源不存在' if code == 404 else (e.description or str(e))
        return jsonify({'code': 1, 'message': message}), code

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        logger.exception('未处理异常: %s', e)
        return jsonify({'code': 1, 'message': str(e)}), 500
