"""
脚本分类和标签模型
"""
from datetime import datetime
from . import db


class Category(db.Model):
    """脚本分类表"""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(20), default='#409EFF')  # 分类颜色
    icon = db.Column(db.String(50))  # 图标名称
    sort_order = db.Column(db.Integer, default=0)  # 排序顺序
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Tag(db.Model):
    """脚本标签表"""
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(20), default='#67C23A')  # 标签颜色
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# 脚本与标签的多对多关系表
script_tags = db.Table('script_tags',
    db.Column('script_id', db.Integer, db.ForeignKey('scripts.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)
