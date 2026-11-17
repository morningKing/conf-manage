"""
Flask应用入口
"""
import logging
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from models import db
from api import api_bp
from api.errors import register_error_handlers
from services.scheduler import scheduler_manager
from services.cleanup_service import run_cleanup_if_needed
from websocket import socketio


def _setup_logging():
    """应用日志：RotatingFileHandler(logs/app.log) + stderr；幂等，防止重复初始化"""
    root = logging.getLogger()
    if any(getattr(h, '_confman_app_log', False) for h in root.handlers):
        return
    root.setLevel(logging.INFO)
    fmt = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s')

    fh = logging.handlers.RotatingFileHandler(
        os.path.join(Config.LOGS_DIR, 'app.log'),
        maxBytes=5 * 1024 * 1024, backupCount=5, encoding='utf-8')
    fh.setFormatter(fmt)
    fh._confman_app_log = True

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    sh._confman_app_log = True

    root.addHandler(fh)
    root.addHandler(sh)


def create_app(config_class=Config):
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化配置（确保 logs 等目录存在）
    config_class.init_app(app)

    # 配置日志
    _setup_logging()

    # 初始化数据库
    db.init_app(app)

    # 配置CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": config_class.CORS_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # 初始化WebSocket
    socketio.init_app(app)

    # 注册蓝图
    app.register_blueprint(api_bp)

    # 统一错误处理（404/405/异常兜底统一返回 JSON）
    register_error_handlers(app)

    # 健康检查
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok'})

    # 创建数据库表
    with app.app_context():
        db.create_all()
        # 设置调度器的应用实例
        scheduler_manager.set_app(app)
        # 重新加载定时任务
        scheduler_manager.reload_schedules()
        # 执行清理检查
        run_cleanup_if_needed()

    return app


if __name__ == '__main__':
    app = create_app()
    print('=' * 60)
    print('脚本工具管理系统后端服务')
    print('=' * 60)
    print(f'服务地址: http://localhost:{Config.HOST_PORT}')
    print(f'API地址: http://localhost:{Config.HOST_PORT}/api')
    print(f'健康检查: http://localhost:{Config.HOST_PORT}/health')
    print(f'WebSocket: ws://localhost:{Config.HOST_PORT}/excel')
    print('=' * 60)
    # 使用 use_reloader=False 防止定时任务在调试模式下被多次初始化
    # allow_unsafe_werkzeug=True 用于开发环境
    socketio.run(app, host=Config.HOST_BIND, port=Config.HOST_PORT,
                 debug=Config.HOST_DEBUG, use_reloader=False, allow_unsafe_werkzeug=True)
