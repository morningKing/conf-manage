"""
文件夹模型（替代分类）
"""
from datetime import datetime
from . import db


class Folder(db.Model):
    """文件夹表"""
    __tablename__ = 'folders'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent = db.relationship('Folder', remote_side=[id], backref=db.backref('children', lazy='dynamic'))

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_tree_dict(self):
        """转换为树形字典（含子文件夹）"""
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'sort_order': self.sort_order,
            'children': [child.to_tree_dict() for child in self.children.order_by(Folder.sort_order, Folder.name).all()],
            'script_count': len(self.scripts) if hasattr(self, 'scripts') else 0
        }
