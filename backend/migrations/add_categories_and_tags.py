"""
添加脚本分类和标签系统

运行方式:
python3 backend/migrations/add_categories_and_tags.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, Category, Tag

def migrate():
    """执行数据库迁移"""
    app = create_app()

    with app.app_context():
        print("开始迁移...")

        # 创建新表
        print("创建分类和标签表...")
        db.create_all()

        # 添加默认分类
        print("添加默认分类...")
        default_categories = [
            {'name': '数据处理', 'description': '数据清洗、转换、分析等脚本', 'color': '#409EFF', 'icon': 'DataAnalysis', 'sort_order': 1},
            {'name': 'API调用', 'description': 'REST API、GraphQL等接口调用脚本', 'color': '#67C23A', 'icon': 'Connection', 'sort_order': 2},
            {'name': '文件操作', 'description': '文件读写、处理、转换等脚本', 'color': '#E6A23C', 'icon': 'Document', 'sort_order': 3},
            {'name': '数据库操作', 'description': '数据库查询、更新、备份等脚本', 'color': '#F56C6C', 'icon': 'Coin', 'sort_order': 4},
            {'name': '自动化任务', 'description': '定时任务、批处理等自动化脚本', 'color': '#909399', 'icon': 'Timer', 'sort_order': 5},
            {'name': '监控告警', 'description': '系统监控、服务检查、告警通知等', 'color': '#C71585', 'icon': 'Bell', 'sort_order': 6},
            {'name': '网络爬虫', 'description': '网页抓取、数据采集等爬虫脚本', 'color': '#FF69B4', 'icon': 'Search', 'sort_order': 7},
            {'name': '其他', 'description': '其他类型的脚本', 'color': '#95A5A6', 'icon': 'More', 'sort_order': 99},
        ]

        for cat_data in default_categories:
            existing = Category.query.filter_by(name=cat_data['name']).first()
            if not existing:
                category = Category(**cat_data)
                db.session.add(category)
                print(f"  - 添加分类: {cat_data['name']}")

        # 添加默认标签
        print("添加默认标签...")
        default_tags = [
            {'name': 'Python', 'color': '#3776ab'},
            {'name': 'JavaScript', 'color': '#f7df1e'},
            {'name': '数据分析', 'color': '#FF6B6B'},
            {'name': 'Web', 'color': '#4ECDC4'},
            {'name': '定时任务', 'color': '#95E1D3'},
            {'name': 'ETL', 'color': '#F38181'},
            {'name': 'Excel', 'color': '#217346'},
            {'name': 'CSV', 'color': '#E67E22'},
            {'name': 'JSON', 'color': '#F39C12'},
            {'name': '邮件', 'color': '#3498DB'},
            {'name': 'HTTP', 'color': '#9B59B6'},
            {'name': '数据库', 'color': '#1ABC9C'},
            {'name': '文本处理', 'color': '#E74C3C'},
        ]

        for tag_data in default_tags:
            existing = Tag.query.filter_by(name=tag_data['name']).first()
            if not existing:
                tag = Tag(**tag_data)
                db.session.add(tag)
                print(f"  - 添加标签: {tag_data['name']}")

        db.session.commit()
        print("迁移完成!")

if __name__ == '__main__':
    migrate()
