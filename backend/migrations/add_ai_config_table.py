"""
添加AI配置表
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # 创建ai_configs表
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS ai_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider VARCHAR(50) NOT NULL DEFAULT 'openai',
            api_key VARCHAR(500) NOT NULL,
            base_url VARCHAR(500),
            model VARCHAR(100) DEFAULT 'gpt-4',
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """))

    db.session.commit()
    print("AI配置表创建成功！")
