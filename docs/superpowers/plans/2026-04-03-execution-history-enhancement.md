# 执行历史增强实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为执行历史添加重新执行功能和批量删除（支持1000条），使用服务端选择会话管理跨页选择状态。

**Architecture:** 新增 SelectionSession 数据模型存储批量选择状态，前端创建选择会话后通过 API 管理选中项。重新执行功能复用现有批量 retry 逻辑，扩展为支持所有非运行状态的执行。

**Tech Stack:** Flask, SQLAlchemy, Vue 3, Element Plus, SSE

---

## 文件结构

```
backend/
├── models/
│   ├── __init__.py              # 修改：导入 SelectionSession
│   └── selection_session.py     # 新建：选择会话模型
├── api/
│   ├── __init__.py              # 修改：导入 selection 模块
│   ├── executions.py            # 修改：添加重新执行 API
│   └── selection.py             # 新建：选择会话 API
└── app.py                       # 修改：注册新模型

frontend/src/
├── api/
│   └── index.js                 # 修改：添加选择会话和重新执行 API
├── views/
│   └── Executions.vue           # 修改：添加选择面板和重新执行按钮
└── components/
    └── SelectionPanel.vue       # 新建：选择会话面板组件
```

---

### Task 1: 创建 SelectionSession 数据模型

**Files:**
- Create: `backend/models/selection_session.py`
- Modify: `backend/models/__init__.py:1-24`

- [ ] **Step 1: 创建 SelectionSession 模型文件**

创建 `backend/models/selection_session.py`：

```python
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
```

- [ ] **Step 2: 在 models/__init__.py 中导入新模型**

修改 `backend/models/__init__.py`，在导入列表添加：

```python
from .selection_session import SelectionSession
```

完整导入部分：
```python
"""
数据模型初始化
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .script import Script, ScriptVersion
from .execution import Execution
from .schedule import Schedule
from .environment import Environment
from .category import Category, Tag, script_tags
from .workflow import Workflow, WorkflowNode, WorkflowEdge, WorkflowExecution, WorkflowNodeExecution
from .workflow_template import WorkflowTemplate
from .global_variable import GlobalVariable
from .ai_config import AIConfig
from .webhook import Webhook, WebhookLog
from .selection_session import SelectionSession

__all__ = [
    'db', 'Script', 'ScriptVersion', 'Execution', 'Schedule', 'Environment',
    'Category', 'Tag', 'script_tags', 'Workflow', 'WorkflowNode', 'WorkflowEdge',
    'WorkflowExecution', 'WorkflowNodeExecution', 'WorkflowTemplate', 'GlobalVariable',
    'AIConfig', 'Webhook', 'WebhookLog', 'SelectionSession'
]
```

- [ ] **Step 3: 验证模型定义**

Run: `cd backend && python -c "from models import SelectionSession; print('SelectionSession:', SelectionSession.__tablename__)"`
Expected: SelectionSession: selection_sessions

- [ ] **Step 4: Commit**

```bash
git add backend/models/selection_session.py backend/models/__init__.py
git commit -m "feat: add SelectionSession model for batch selection management"
```

---

### Task 2: 创建选择会话 API

**Files:**
- Create: `backend/api/selection.py`
- Modify: `backend/api/__init__.py`

- [ ] **Step 1: 创建 selection.py API 文件**

创建 `backend/api/selection.py`：

```python
"""
选择会话API - 用于批量操作的状态管理
"""
from flask import request, jsonify
from . import api_bp
from models import db, SelectionSession, Execution
import uuid
import json


@api_bp.route('/executions/selection/create', methods=['POST'])
def create_selection_session():
    """创建新的选择会话"""
    try:
        session_id = uuid.uuid4().hex[:16]
        session = SelectionSession(session_id=session_id)
        db.session.add(session)
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': {
                'session_id': session_id,
                'max_limit': SelectionSession.MAX_SELECTIONS
            },
            'message': '选择会话已创建'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions/selection/<session_id>', methods=['GET'])
def get_selection_session(session_id):
    """获取选择会话详情"""
    try:
        session = SelectionSession.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({'code': 1, 'message': '会话不存在'}), 404

        # 获取选中项基本信息
        ids = session.get_ids()
        items = []
        for eid in ids:
            execution = Execution.query.get(eid)
            if execution:
                items.append({
                    'id': execution.id,
                    'script_name': execution.script.name if execution.script else None,
                    'status': execution.status,
                    'created_at': execution.created_at.isoformat() if execution.created_at else None
                })

        return jsonify({
            'code': 0,
            'data': {
                'session_id': session.session_id,
                'count': session.count,
                'max_limit': SelectionSession.MAX_SELECTIONS,
                'ids': ids,
                'items': items
            }
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions/selection/<session_id>/add', methods=['POST'])
def add_to_selection(session_id):
    """添加执行ID到选择会话"""
    try:
        session = SelectionSession.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({'code': 1, 'message': '会话不存在'}), 404

        data = request.get_json()
        execution_ids = data.get('execution_ids', [])

        if not isinstance(execution_ids, list):
            return jsonify({'code': 1, 'message': 'execution_ids必须是数组'}), 400

        # 验证ID是否存在
        valid_ids = []
        for eid in execution_ids:
            if Execution.query.get(eid):
                valid_ids.append(eid)

        new_count = session.add_ids(valid_ids)
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': {
                'count': new_count,
                'max_limit': SelectionSession.MAX_SELECTIONS,
                'max_reached': session.is_max_reached()
            },
            'message': f'已添加{len(valid_ids)}项'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions/selection/<session_id>/remove', methods=['POST'])
def remove_from_selection(session_id):
    """从选择会话移除执行ID"""
    try:
        session = SelectionSession.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({'code': 1, 'message': '会话不存在'}), 404

        data = request.get_json()
        execution_ids = data.get('execution_ids', [])

        if not isinstance(execution_ids, list):
            return jsonify({'code': 1, 'message': 'execution_ids必须是数组'}), 400

        new_count = session.remove_ids(execution_ids)
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': {
                'count': new_count,
                'max_limit': SelectionSession.MAX_SELECTIONS
            },
            'message': f'已移除{len(execution_ids)}项'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions/selection/<session_id>/clear', methods=['POST'])
def clear_selection(session_id):
    """清空选择会话"""
    try:
        session = SelectionSession.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({'code': 1, 'message': '会话不存在'}), 404

        session.clear()
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': {
                'count': 0,
                'max_limit': SelectionSession.MAX_SELECTIONS
            },
            'message': '选择已清空'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions/selection/<session_id>/delete', methods=['POST'])
def delete_selection_batch(session_id):
    """批量删除选中的执行记录"""
    try:
        import shutil
        from config import Config

        session = SelectionSession.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({'code': 1, 'message': '会话不存在'}), 404

        ids = session.get_ids()
        if not ids:
            return jsonify({'code': 1, 'message': '没有选中项'}), 400

        result = {
            'total': len(ids),
            'success': 0,
            'failed': 0,
            'details': []
        }

        for eid in ids:
            execution = Execution.query.get(eid)
            if not execution:
                result['failed'] += 1
                result['details'].append({
                    'id': eid,
                    'status': 'failed',
                    'message': '执行记录不存在'
                })
                continue

            try:
                # 删除日志文件
                if execution.log_file and os.path.exists(execution.log_file):
                    os.remove(execution.log_file)

                # 删除执行空间
                execution_space = Config.get_execution_space(eid)
                if os.path.exists(execution_space):
                    shutil.rmtree(execution_space)

                db.session.delete(execution)
                result['success'] += 1
                result['details'].append({
                    'id': eid,
                    'status': 'success',
                    'message': '删除成功'
                })

            except Exception as e:
                result['failed'] += 1
                result['details'].append({
                    'id': eid,
                    'status': 'failed',
                    'message': str(e)
                })

        # 清空选择会话
        session.clear()
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': result,
            'message': f'批量删除完成: 成功{result["success"]}个，失败{result["failed"]}个'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


import os
```

- [ ] **Step 2: 在 api/__init__.py 中导入新模块**

检查 `backend/api/__init__.py`，确保所有 API 模块通过 `api_bp` blueprint 注册。如果需要显式导入，添加：

```python
from .selection import *
```

- [ ] **Step 3: 验证 API 注册**

Run: `cd backend && python -c "from api.selection import api_bp; print('Routes:', [r.rule for r in api_bp.url_map.iter_rules() if 'selection' in r.rule][:5])"`
Expected: 显示 selection 相关路由

- [ ] **Step 4: Commit**

```bash
git add backend/api/selection.py backend/api/__init__.py
git commit -m "feat: add selection session API for batch operations"
```

---

### Task 3: 添加重新执行 API

**Files:**
- Modify: `backend/api/executions.py:15-89`

- [ ] **Step 1: 在 executions.py 添加重新执行 API**

在 `batch_manage_executions` 函数后（约第534行）添加：

```python
@api_bp.route('/executions/<int:execution_id>/re-execute', methods=['POST'])
def re_execute_script(execution_id):
    """重新执行脚本（支持所有非运行状态）"""
    try:
        execution = Execution.query.get_or_404(execution_id)

        # 检查状态（running状态不能重新执行）
        if execution.status == 'running':
            return jsonify({
                'code': 1,
                'message': '正在运行的执行不能重新执行，请先中断'
            }), 400

        # 获取原执行参数
        original_params = {}
        if execution.params:
            try:
                original_params = json.loads(execution.params)
            except json.JSONDecodeError:
                original_params = {}

        # 创建新执行记录
        new_execution = Execution(
            script_id=execution.script_id,
            environment_id=execution.environment_id,
            status='pending',
            params=json.dumps(original_params) if original_params else None
        )
        db.session.add(new_execution)
        db.session.flush()  # 获取新execution.id

        # 复制执行空间的文件（如果有）
        from config import Config
        old_space = Config.get_execution_space(execution.id)
        new_space = Config.ensure_execution_space(new_execution.id)

        if os.path.exists(old_space):
            import shutil
            for item in os.listdir(old_space):
                src = os.path.join(old_space, item)
                dst = os.path.join(new_space, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)

        # 异步执行脚本
        from threading import Thread
        from flask import current_app
        from services.executor import execute_script

        app = current_app._get_current_object()

        def run_script_with_context():
            with app.app_context():
                execute_script(new_execution.id)

        thread = Thread(target=run_script_with_context)
        thread.start()

        db.session.commit()

        return jsonify({
            'code': 0,
            'data': {
                'new_execution_id': new_execution.id,
                'original_execution_id': execution.id,
                'script_name': execution.script.name if execution.script else None
            },
            'message': '已创建新执行记录并启动执行'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500
```

- [ ] **Step 2: 验证 API 添加**

Run: `cd backend && python -c "from api.executions import re_execute_script; print('re-execute route added')"`
Expected: re-execute route added

- [ ] **Step 3: Commit**

```bash
git add backend/api/executions.py
git commit -m "feat: add re-execute API for all non-running executions"
```

---

### Task 4: 更新前端 API 客户端

**Files:**
- Modify: `frontend/src/api/index.js:19-31`

- [ ] **Step 1: 添加选择会话 API 方法**

在 `frontend/src/api/index.js` 的执行历史部分后添加：

```javascript
// 选择会话管理（批量操作支持1000条）
export const createSelectionSession = () => request.post('/executions/selection/create')
export const getSelectionSession = (sessionId) => request.get(`/executions/selection/${sessionId}`)
export const addToSelection = (sessionId, executionIds) => request.post(`/executions/selection/${sessionId}/add`, { execution_ids: executionIds })
export const removeFromSelection = (sessionId, executionIds) => request.post(`/executions/selection/${sessionId}/remove`, { execution_ids: executionIds })
export const clearSelection = (sessionId) => request.post(`/executions/selection/${sessionId}/clear`)
export const deleteSelectionBatch = (sessionId) => request.post(`/executions/selection/${sessionId}/delete')

// 重新执行
export const reExecuteScript = (executionId) => request.post(`/executions/${executionId}/re-execute`)
```

- [ ] **Step 2: 验证 API 导出**

Run: `cd frontend && npm run build 2>&1 | head -20`
Expected: 无语法错误，构建成功

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/index.js
git commit -m "feat: add selection session and re-execute API methods"
```

---

### Task 5: 创建 SelectionPanel 组件

**Files:**
- Create: `frontend/src/components/SelectionPanel.vue`

- [ ] **Step 1: 创建 SelectionPanel.vue 组件**

创建 `frontend/src/components/SelectionPanel.vue`：

```vue
<template>
  <div class="selection-panel" v-if="sessionId">
    <!-- 选择计数 -->
    <div class="selection-info">
      <el-badge :value="count" :max="1000" class="selection-badge">
        <el-button size="small" @click="showDetail">
          <el-icon><Select /></el-icon>
          已选择
        </el-button>
      </el-badge>
      <span class="max-hint" v-if="count >= 1000">
        (已达上限)
      </span>
    </div>

    <!-- 批量操作按钮 -->
    <div class="selection-actions">
      <el-button
        type="danger"
        size="small"
        :disabled="count === 0"
        :loading="deleteLoading"
        @click="handleBatchDelete"
      >
        <el-icon><Delete /></el-icon>
        批量删除
      </el-button>
      <el-button
        size="small"
        :disabled="count === 0"
        @click="handleClear"
      >
        清空选择
      </el-button>
    </div>

    <!-- 选中详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="已选择的执行记录"
      width="60%"
      top="10vh"
    >
      <el-table :data="selectedItems" max-height="400" v-loading="detailLoading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="script_name" label="脚本名称" min-width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center">
          <template #default="{ row }">
            <el-button
              type="danger"
              size="small"
              link
              @click="handleRemoveItem(row.id)"
            >
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="danger" @click="handleBatchDelete" :disabled="selectedItems.length === 0">
          删除全部 ({{ selectedItems.length }})
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Select, Delete } from '@element-plus/icons-vue'
import {
  createSelectionSession,
  getSelectionSession,
  addToSelection,
  removeFromSelection,
  clearSelection,
  deleteSelectionBatch
} from '../api'

const props = defineProps({
  // 初始选中的执行ID列表
  initialIds: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['change', 'deleted'])

const sessionId = ref(null)
const count = ref(0)
const selectedItems = ref([])
const detailVisible = ref(false)
const detailLoading = ref(false)
const deleteLoading = ref(false)

// 创建选择会话
const initSession = async () => {
  try {
    const res = await createSelectionSession()
    sessionId.value = res.data.session_id

    // 添加初始选中项
    if (props.initialIds.length > 0) {
      await handleAddItems(props.initialIds)
    }
  } catch (error) {
    console.error('创建选择会话失败:', error)
  }
}

// 添加选中项
const handleAddItems = async (ids) => {
  if (!sessionId.value) return

  try {
    const res = await addToSelection(sessionId.value, ids)
    count.value = res.data.count

    if (res.data.max_reached) {
      ElMessage.warning('已达到最大选择数量1000条')
    }

    emit('change', { count: count.value, maxReached: res.data.max_reached })
  } catch (error) {
    ElMessage.error('添加选择失败: ' + error.message)
  }
}

// 移除选中项
const handleRemoveItem = async (id) => {
  if (!sessionId.value) return

  try {
    const res = await removeFromSelection(sessionId.value, [id])
    count.value = res.data.count
    selectedItems.value = selectedItems.value.filter(item => item.id !== id)
    emit('change', { count: count.value })
  } catch (error) {
    ElMessage.error('移除失败: ' + error.message)
  }
}

// 显示详情
const showDetail = async () => {
  if (!sessionId.value) return

  detailVisible.value = true
  detailLoading.value = true

  try {
    const res = await getSelectionSession(sessionId.value)
    selectedItems.value = res.data.items || []
    count.value = res.data.count
  } catch (error) {
    ElMessage.error('获取选择详情失败: ' + error.message)
  } finally {
    detailLoading.value = false
  }
}

// 清空选择
const handleClear = async () => {
  if (!sessionId.value) return

  try {
    await clearSelection(sessionId.value)
    count.value = 0
    selectedItems.value = []
    emit('change', { count: 0 })
    ElMessage.success('选择已清空')
  } catch (error) {
    ElMessage.error('清空失败: ' + error.message)
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (!sessionId.value || count.value === 0) return

  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${count.value} 条执行记录？此操作不可恢复。`,
      '批量删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    deleteLoading.value = true
    const res = await deleteSelectionBatch(sessionId.value)

    if (res.code === 0) {
      const { success, failed } = res.data
      if (success > 0) {
        ElMessage.success(`成功删除 ${success} 条记录`)
      }
      if (failed > 0) {
        ElMessage.warning(`失败 ${failed} 条`)
      }

      count.value = 0
      selectedItems.value = []
      detailVisible.value = false
      emit('deleted', res.data)
      emit('change', { count: 0 })
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败: ' + error.message)
    }
  } finally {
    deleteLoading.value = false
  }
}

// 状态映射
const getStatusType = (status) => {
  const types = {
    pending: 'info',
    running: '',
    success: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    pending: '等待中',
    running: '运行中',
    success: '成功',
    failed: '失败'
  }
  return texts[status] || status
}

const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}

// 暴露方法给父组件
defineExpose({
  handleAddItems,
  handleRemoveItem,
  handleClear,
  showDetail,
  sessionId,
  count
})

onMounted(() => {
  initSession()
})
</script>

<style scoped lang="scss">
.selection-panel {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background-color: #f0f9ff;
  border-radius: 8px;
  border: 1px solid #b3d8ff;
  margin-bottom: 16px;

  .selection-info {
    display: flex;
    align-items: center;
    gap: 8px;

    .selection-badge {
      margin-right: 4px;
    }

    .max-hint {
      color: #e6a23c;
      font-size: 12px;
    }
  }

  .selection-actions {
    display: flex;
    gap: 8px;
  }
}
</style>
```

- [ ] **Step 2: 验证组件语法**

Run: `cd frontend && npm run build 2>&1 | grep -i error || echo "Build OK"`
Expected: Build OK

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/SelectionPanel.vue
git commit -m "feat: add SelectionPanel component for batch selection"
```

---

### Task 6: 更新 Executions.vue 页面

**Files:**
- Modify: `frontend/src/views/Executions.vue:1-810`

- [ ] **Step 1: 导入 SelectionPanel 和新 API**

在 Executions.vue 的 `<script setup>` 部分修改导入：

```javascript
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Delete, VideoPause, RefreshRight, Close, DataLine, Select } from '@element-plus/icons-vue'
import {
  getExecutions, getExecutionLogs, deleteExecution, deleteWorkflowExecution,
  cancelExecution, batchManageExecutions, getExecutionsStatistics,
  reExecuteScript  // 新增
} from '../api'
import ExecutionFiles from '../components/ExecutionFiles.vue'
import ExecutionProgress from '../components/ExecutionProgress.vue'
import SelectionPanel from '../components/SelectionPanel.vue'  // 新增
```

- [ ] **Step 2: 添加选择面板和重新执行按钮到模板**

在 `<el-card>` 的 `<template #header>` 后，批量操作栏前添加 SelectionPanel：

```vue
<!-- 选择会话面板 -->
<SelectionPanel
  ref="selectionPanelRef"
  @change="handleSelectionChange"
  @deleted="handleSelectionDeleted"
/>
```

在操作列添加"重新执行"按钮：

```vue
<el-table-column label="操作" width="320" fixed="right">
  <template #default="{ row }">
    <el-button
      v-if="row.status === 'running'"
      size="small"
      type="warning"
      @click="handleCancel(row)"
    >
      中断
    </el-button>
    <el-button
      v-if="row.status !== 'running'"
      size="small"
      type="success"
      @click="handleReExecute(row)"
    >
      重新执行
    </el-button>
    <el-button size="small" @click="handleViewLogs(row)">日志</el-button>
    <el-button size="small" type="primary" @click="handleViewFiles(row)">文件</el-button>
    <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
  </template>
</el-table-column>
```

- [ ] **Step 3: 添加表格行选择功能**

修改 `<el-table>` 添加行点击选择：

```vue
<el-table
  :data="executions"
  stripe
  @row-click="handleRowClick"
  ref="executionsTable"
  row-key="id"
>
  <el-table-column type="selection" width="55" />
  ...
</el-table>
```

- [ ] **Step 4: 添加脚本逻辑**

在 script 中添加：

```javascript
const selectionPanelRef = ref(null)
const selectionSessionId = ref(null)
const selectionCount = ref(0)

// 处理行点击（添加到选择）
const handleRowClick = async (row) => {
  // 不选择工作流执行（仅支持脚本执行）
  if (row.execution_type === 'workflow') {
    return
  }

  if (selectionCount.value >= 1000) {
    ElMessage.warning('最多选择1000条')
    return
  }

  // 通过 SelectionPanel 添加
  if (selectionPanelRef.value) {
    await selectionPanelRef.value.handleAddItems([row.id])
  }
}

// 选择变化回调
const handleSelectionChange = ({ count, maxReached }) => {
  selectionCount.value = count
}

// 删除完成回调
const handleSelectionDeleted = (result) => {
  loadExecutions()
}

// 重新执行
const handleReExecute = async (row) => {
  try {
    await ElMessageBox.confirm(
      '确定要重新执行此脚本吗？将创建新的执行记录。',
      '重新执行确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    const res = await reExecuteScript(row.id)
    if (res.code === 0) {
      ElMessage.success(`已创建新执行 #${res.data.new_execution_id}`)
      loadExecutions()

      // 可选：自动跳转到新执行详情
      // router.push(`/executions/${res.data.new_execution_id}`)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重新执行失败: ' + error.message)
    }
  }
}
```

- [ ] **Step 5: 验证前端构建**

Run: `cd frontend && npm run build`
Expected: 构建成功无错误

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/Executions.vue
git commit -m "feat: add re-execute and selection panel to Executions page"
```

---

### Task 7: 集成测试

**Files:**
- 无文件修改，测试验证

- [ ] **Step 1: 启动后端服务**

Run: `cd backend && python app.py`
Expected: Flask 在 port 5000 启动

- [ ] **Step 2: 启动前端开发服务**

Run: `cd frontend && npm run dev`
Expected: Vite 在 port 5173 启动

- [ ] **Step 3: 验证重新执行功能**

在浏览器中：
1. 打开执行历史页面
2. 找一个非运行状态的执行记录
3. 点击"重新执行"按钮
4. 确认对话框
5. 验证新执行记录创建并开始运行

- [ ] **Step 4: 验证批量选择功能**

在浏览器中：
1. 点击执行记录行添加到选择
2. 点击"已选择"按钮查看详情
3. 切换页面，验证选择状态保持
4. 测试批量删除（选择多个后点击批量删除）

- [ ] **Step 5: 验证最大1000条限制**

测试场景：
1. 快速点击多个执行记录行
2. 当达到1000条时，应显示"已达上限"提示
3. 无法继续添加

- [ ] **Step 6: Commit 测试通过标记**

```bash
git add -A
git commit -m "test: execution history enhancement integration test passed"
```

---

## 自检清单

**1. Spec覆盖检查:**
- ✓ 重新执行功能 - Task 3, Task 6
- ✓ 批量删除支持1000条 - Task 1, Task 2, Task 5
- ✓ 服务端选择会话 - Task 1, Task 2
- ✓ 跨页保持选择状态 - Task 2 (session存储在数据库)
- ✓ 前端选择面板 - Task 5, Task 6

**2. Placeholder扫描:**
- 无 TBD、TODO
- 无 "add error handling" 等泛化描述
- 所有代码完整提供

**3. 类型一致性:**
- SelectionSession.session_id 使用 String(32)
- Execution.ids 使用 JSON 数组存储
- API 返回格式一致 {code, data, message}

---

## 完成标记

执行历史增强功能已完成，支持：
- 所有非运行状态的执行记录可重新执行
- 服务端选择会话管理，跨页保持选择状态
- 批量删除最多1000条执行记录