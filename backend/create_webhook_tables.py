"""
创建Webhook相关数据库表的脚本
"""
import sys
import os

# 将backend目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Webhook, WebhookLog

app = create_app()

with app.app_context():
    # 创建表
    db.create_all()
    print("数据库表创建成功！")
    print("已创建表:")
    print("- webhooks")
    print("- webhook_logs")
