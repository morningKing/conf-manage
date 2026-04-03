"""
选择会话模型 - 用于批量操作的状态管理
"""
from datetime import datetime
from . import db
import json


class SelectionSession(db.Model):
    """选择会话表"""
    __tablename__ = 'selection_sessions'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(32), unique=True, nullable=False)  # UUID
    execution_ids = db.Column(db.Text, default='[]')  # JSON数组存储选中ID
    count = db.Column(db.Integer, default=0)  # 选中数量
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 最大选择数量
    MAX_SELECTIONS = 1000

    def get_ids(self):
        """获取选中的执行ID列表"""
        return json.loads(self.execution_ids) if self.execution_ids else []

    def set_ids(self, ids):
        """设置选中的执行ID列表"""
        # 限制最大数量
        ids = list(set(ids))[:self.MAX_SELECTIONS]
        self.execution_ids = json.dumps(ids)
        self.count = len(ids)

    def add_ids(self, ids):
        """添加执行ID到选择列表"""
        current_ids = self.get_ids()
        new_ids = list(set(current_ids + ids))[:self.MAX_SELECTIONS]
        self.set_ids(new_ids)
        return len(new_ids)

    def remove_ids(self, ids):
        """从选择列表移除执行ID"""
        current_ids = self.get_ids()
        new_ids = [id for id in current_ids if id not in ids]
        self.set_ids(new_ids)
        return len(new_ids)

    def clear(self):
        """清空选择列表"""
        self.execution_ids = '[]'
        self.count = 0

    def is_max_reached(self):
        """检查是否达到最大选择数量"""
        return self.count >= self.MAX_SELECTIONS

    def to_dict(self):
        """转换为字典"""
        return {
            'session_id': self.session_id,
            'count': self.count,
            'max_limit': self.MAX_SELECTIONS,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }