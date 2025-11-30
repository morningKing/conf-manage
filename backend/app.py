"""
Flask应用入口
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from models import db
from api import api_bp
from services.scheduler import scheduler_manager


def create_app(config_class=Config):
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化配置
    config_class.init_app(app)

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

    # 注册蓝图
    app.register_blueprint(api_bp)

    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'code': 1, 'message': '资源不存在'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'code': 1, 'message': '服务器内部错误'}), 500

    # 健康检查
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok'})

    # 创建数据库表
    with app.app_context():
        db.create_all()
        # 重新加载定时任务
        scheduler_manager.reload_schedules()

    return app


if __name__ == '__main__':
    app = create_app()
    print('=' * 60)
    print('脚本工具管理系统后端服务')
    print('=' * 60)
    print(f'服务地址: http://localhost:5000')
    print(f'API地址: http://localhost:5000/api')
    print(f'健康检查: http://localhost:5000/health')
    print('=' * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
