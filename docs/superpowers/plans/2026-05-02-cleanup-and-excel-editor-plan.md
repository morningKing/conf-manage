# 自动清理与Excel编辑功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现历史任务自动清理（支持白名单）和Excel文件在线编辑（支持多人协作）

**Architecture:** 
- 清理功能：数据库字段扩展 + 清理工具模块 + 系统API + 启动时/手动触发
- Excel编辑：独立编辑页面 + Luckysheet库 + 后端API化 + WebSocket协作

**Tech Stack:** 
- 后端：Flask、openpyxl、Flask-SocketIO（WebSocket）
- 前端：Vue 3、Luckysheet、Socket.IO客户端

---

## Phase 1: 清理功能后端

### Task 1: Schedule模型添加preserve字段

**Files:**
- Modify: `backend/models/schedule.py`

- [ ] **Step 1: 添加preserve字段到Schedule模型**

```python
# backend/models/schedule.py
# 在现有字段后添加：

preserve = db.Column(db.Boolean, default=False, nullable=False)  # 白名单标记，True表示永不清理
```

- [ ] **Step 2: 更新to_dict方法包含preserve字段**

```python
# backend/models/schedule.py to_dict方法中添加：
def to_dict(self):
    """转换为字典"""
    return {
        'id': self.id,
        'script_id': self.script_id,
        'script_name': self.script.name if self.script else None,
        'name': self.name,
        'description': self.description,
        'cron': self.cron,
        'params': self.params,
        'enabled': self.enabled,
        'preserve': self.preserve,  # 新增
        'last_run': self.last_run.isoformat() if self.last_run else None,
        'next_run': self.next_run.isoformat() if self.next_run else None,
        'created_at': self.created_at.isoformat() if self.created_at else None,
        'updated_at': self.updated_at.isoformat() if self.updated_at else None
    }
```

- [ ] **Step 3: 提交变更**

```bash
git add backend/models/schedule.py
git commit -m "feat: add preserve field to Schedule model for cleanup whitelist"
```

---

### Task 2: 配置文件添加清理阈值

**Files:**
- Modify: `backend/config.py`

- [ ] **Step 1: 添加清理阈值配置**

```python
# backend/config.py
# 在 Config 类中添加（约第80行后）：

# 清理阈值：保留最近N条执行记录
CLEANUP_THRESHOLD = 500
```

- [ ] **Step 2: 提交变更**

```bash
git add backend/config.py
git commit -m "feat: add CLEANUP_THRESHOLD configuration"
```

---

### Task 3: 创建清理工具模块

**Files:**
- Create: `backend/utils/cleanup.py`

- [ ] **Step 1: 创建清理模块基础结构**

```python
# backend/utils/cleanup.py
"""
历史数据清理工具模块
"""
import os
import shutil
from datetime import datetime
from models import db, Execution, Schedule, WorkflowExecution
from config import Config


def get_cleanup_stats():
    """
    获取清理统计信息
    
    Returns:
        dict: 统计信息
    """
    # 总执行记录数
    total_executions = Execution.query.count()
    
    # 白名单Schedule的ID集合
    whitelisted_schedule_ids = set(
        s.id for s in Schedule.query.filter_by(preserve=True).all()
    )
    
    # 白名单Execution数量
    whitelisted_executions = Execution.query.filter(
        Execution.script_id.in_(
            Schedule.query.filter_by(preserve=True).with_entities(Schedule.script_id).all()
        )
    ).count()
    
    # 计算需要清理的数量
    threshold = Config.CLEANUP_THRESHOLD
    to_cleanup = max(0, total_executions - threshold - whitelisted_executions)
    
    # 计算执行空间大小
    execution_spaces_size = get_directory_size(Config.EXECUTION_SPACES_DIR)
    workflow_spaces_size = get_directory_size(Config.WORKFLOW_EXECUTION_SPACES_DIR)
    
    return {
        'total_executions': total_executions,
        'whitelisted_executions': whitelisted_executions,
        'to_cleanup': to_cleanup,
        'execution_spaces_size_mb': execution_spaces_size / (1024 * 1024),
        'workflow_spaces_size_mb': workflow_spaces_size / (1024 * 1024),
        'threshold': threshold
    }


def get_directory_size(path):
    """
    计算目录大小
    
    Args:
        path: 目录路径
    
    Returns:
        float: 大小（字节）
    """
    if not os.path.exists(path):
        return 0
    
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except OSError:
                pass
    
    return total_size


def run_cleanup():
    """
    执行清理操作
    
    Returns:
        dict: 清理结果
    """
    threshold = Config.CLEANUP_THRESHOLD
    
    # 1. 获取白名单Schedule的script_id集合
    whitelisted_script_ids = set(
        s.script_id for s in Schedule.query.filter_by(preserve=True).all()
    )
    
    # 2. 获取所有Execution，按created_at降序
    all_executions = Execution.query.order_by(Execution.created_at.desc()).all()
    
    # 3. 确定保留的Execution ID集合
    preserve_ids = set()
    
    # 首先添加白名单Execution
    for exec in all_executions:
        if exec.script_id in whitelisted_script_ids:
            preserve_ids.add(exec.id)
    
    # 然后添加最近的N条（如果不在白名单中）
    non_whitelisted_execs = [e for e in all_executions if e.script_id not in whitelisted_script_ids]
    for exec in non_whitelisted_execs[:threshold]:
        preserve_ids.add(exec.id)
    
    # 4. 清理不在保留集合中的Execution
    to_delete = [e for e in all_executions if e.id not in preserve_ids]
    
    deleted_executions = 0
    deleted_execution_spaces = 0
    deleted_workflow_spaces = 0
    freed_space = 0
    
    for exec in to_delete:
        # 删除执行空间
        space_path = Config.get_execution_space(exec.id)
        if os.path.exists(space_path):
            space_size = get_directory_size(space_path)
            freed_space += space_size
            shutil.rmtree(space_path)
            deleted_execution_spaces += 1
        
        # 删除日志文件
        log_path = os.path.join(Config.LOGS_DIR, f'execution_{exec.id}.log')
        if os.path.exists(log_path):
            freed_space += os.path.getsize(log_path)
            os.remove(log_path)
        
        # 删除数据库记录
        db.session.delete(exec)
        deleted_executions += 1
    
    # 5. 清理WorkflowExecution（不在保留Execution关联的）
    # WorkflowNodeExecution关联Execution，如果Execution被删除，对应的WorkflowExecution也应清理
    workflow_executions = WorkflowExecution.query.all()
    for wf_exec in workflow_executions:
        # 检查该WorkflowExecution的所有node_executions关联的Execution是否都被删除
        node_execs = wf_exec.node_executions.all()
        if all(ne.execution_id not in preserve_ids for ne in node_execs if ne.execution_id):
            # 删除工作流执行空间
            wf_space_path = Config.get_workflow_execution_space(wf_exec.id)
            if os.path.exists(wf_space_path):
                space_size = get_directory_size(wf_space_path)
                freed_space += space_size
                shutil.rmtree(wf_space_path)
                deleted_workflow_spaces += 1
            
            # 删除数据库记录
            db.session.delete(wf_exec)
    
    # 提交数据库变更
    db.session.commit()
    
    return {
        'deleted_executions': deleted_executions,
        'deleted_execution_spaces': deleted_execution_spaces,
        'deleted_workflow_spaces': deleted_workflow_spaces,
        'freed_space_mb': freed_space / (1024 * 1024)
    }


def run_cleanup_if_needed():
    """
    启动时检查并执行清理（如果需要）
    """
    stats = get_cleanup_stats()
    
    # 如果需要清理的数量大于阈值的一半，执行清理
    if stats['to_cleanup'] > Config.CLEANUP_THRESHOLD / 2:
        print(f"[Cleanup] 检测到需要清理 {stats['to_cleanup']} 条记录，开始清理...")
        result = run_cleanup()
        print(f"[Cleanup] 清理完成: 删除 {result['deleted_executions']} 条执行记录, "
              f"释放 {result['freed_space_mb']:.2f} MB 空间")
    else:
        print(f"[Cleanup] 当前无需清理，总记录 {stats['total_executions']} 条")
```

- [ ] **Step 2: 提交变更**

```bash
git add backend/utils/cleanup.py
git commit -m "feat: create cleanup utility module for history data management"
```

---

### Task 4: 创建系统管理API

**Files:**
- Create: `backend/api/system.py`
- Modify: `backend/api/__init__.py`

- [ ] **Step 1: 创建system.py API文件**

```python
# backend/api/system.py
"""
系统管理API
"""
from flask import jsonify, request
from api import api_bp
from utils.cleanup import get_cleanup_stats, run_cleanup
from config import Config


@api_bp.route('/system/cleanup/stats', methods=['GET'])
def get_cleanup_stats_api():
    """获取清理统计信息"""
    try:
        stats = get_cleanup_stats()
        return jsonify({
            'code': 0,
            'data': stats
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/system/cleanup', methods=['POST'])
def execute_cleanup():
    """执行清理操作"""
    try:
        result = run_cleanup()
        return jsonify({
            'code': 0,
            'data': result,
            'message': '清理完成'
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/system/cleanup/config', methods=['GET'])
def get_cleanup_config():
    """获取清理配置"""
    try:
        return jsonify({
            'code': 0,
            'data': {
                'threshold': Config.CLEANUP_THRESHOLD
            }
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/system/cleanup/config', methods=['PUT'])
def update_cleanup_config():
    """更新清理配置（运行时配置，不写入文件）"""
    try:
        data = request.get_json()
        threshold = data.get('threshold', 500)
        
        # 验证阈值范围
        if threshold < 50 or threshold > 10000:
            return jsonify({'code': 1, 'message': '阈值范围应为50-10000'}), 400
        
        # 更新运行时配置
        Config.CLEANUP_THRESHOLD = threshold
        
        return jsonify({
            'code': 0,
            'data': {
                'threshold': Config.CLEANUP_THRESHOLD
            },
            'message': '配置已更新'
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500
```

- [ ] **Step 2: 在__init__.py中导入system模块**

```python
# backend/api/__init__.py
# 在导入列表中添加 system：

from . import scripts, executions, schedules, files, environments, folders, workflows, workflow_templates, global_variables, ai_configs, ai_scripts, webhooks, webhook_trigger, backup, selection, upload, system
```

- [ ] **Step 3: 提交变更**

```bash
git add backend/api/system.py backend/api/__init__.py
git commit -m "feat: create system API for cleanup management"
```

---

### Task 5: Schedule API添加preserve字段支持

**Files:**
- Modify: `backend/api/schedules.py`

- [ ] **Step 1: 在create_schedule中添加preserve支持**

找到create_schedule函数，在数据提取部分添加：

```python
# backend/api/schedules.py create_schedule函数中
# 在 data = { ... } 字典中添加：

data = {
    'script_id': script_id,
    'name': name,
    'description': description,
    'cron': cron,
    'params': params,
    'enabled': enabled,
    'preserve': data.get('preserve', False)  # 新增
}
```

- [ ] **Step 2: 在update_schedule中添加preserve支持**

找到update_schedule函数，在更新字段部分添加：

```python
# backend/api/schedules.py update_schedule函数中
# 在 if name: schedule.name = name 等字段更新后添加：

if 'preserve' in data:
    schedule.preserve = data.get('preserve')
```

- [ ] **Step 3: 添加toggle_preserve API**

```python
# backend/api/schedules.py 末尾添加：

@api_bp.route('/schedules/<int:id>/preserve', methods=['POST'])
def toggle_schedule_preserve(id):
    """切换定时任务的白名单状态"""
    try:
        schedule = Schedule.query.get(id)
        if not schedule:
            return jsonify({'code': 1, 'message': '定时任务不存在'}), 404
        
        schedule.preserve = not schedule.preserve
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': schedule.to_dict(),
            'message': f'已{"加入" if schedule.preserve else "移出"}白名单'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/schedules/batch/preserve', methods=['POST'])
def batch_toggle_preserve():
    """批量设置白名单状态"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        preserve = data.get('preserve', True)
        
        if not ids:
            return jsonify({'code': 1, 'message': '请选择定时任务'}), 400
        
        schedules = Schedule.query.filter(Schedule.id.in_(ids)).all()
        for schedule in schedules:
            schedule.preserve = preserve
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'message': f'已批量{"加入" if preserve else "移出"}白名单',
            'data': {'count': len(schedules)}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500
```

- [ ] **Step 4: 提交变更**

```bash
git add backend/api/schedules.py
git commit -m "feat: add preserve field support to Schedule API"
```

---

### Task 6: 应用启动时集成清理

**Files:**
- Modify: `backend/app.py`

- [ ] **Step 1: 导入清理模块并添加启动清理**

```python
# backend/app.py
# 在文件顶部导入部分添加：

from utils.cleanup import run_cleanup_if_needed

# 在 create_app 函数中，db.create_all() 之后添加：

# 创建数据库表
with app.app_context():
    db.create_all()
    # 设置调度器的应用实例
    scheduler_manager.set_app(app)
    # 重新加载定时任务
    scheduler_manager.reload_schedules()
    # 执行清理检查（新增）
    run_cleanup_if_needed()
```

- [ ] **Step 2: 提交变更**

```bash
git add backend/app.py
git commit -m "feat: integrate cleanup check on application startup"
```

---

## Phase 2: 清理功能前端

### Task 7: 前端API添加清理相关方法

**Files:**
- Modify: `frontend/src/api/index.js`

- [ ] **Step 1: 添加清理和preserve相关API方法**

```javascript
// frontend/src/api/index.js
// 在文件末尾添加：

// 系统清理管理
export const getCleanupStats = () => request.get('/system/cleanup/stats')
export const executeCleanup = () => request.post('/system/cleanup')
export const getCleanupConfig = () => request.get('/system/cleanup/config')
export const updateCleanupConfig = (data) => request.put('/system/cleanup/config', data)

// 定时任务白名单
export const toggleSchedulePreserve = (id) => request.post(`/schedules/${id}/preserve`)
export const batchToggleSchedulePreserve = (data) => request.post('/schedules/batch/preserve', data)
```

- [ ] **Step 2: 提交变更**

```bash
git add frontend/src/api/index.js
git commit -m "feat: add cleanup and preserve API methods"
```

---

### Task 8: Schedules.vue添加白名单开关

**Files:**
- Modify: `frontend/src/views/Schedules.vue`

- [ ] **Step 1: 在表格中添加保护状态列**

```vue
<!-- frontend/src/views/Schedules.vue -->
<!-- 在 <el-table> 中，enabled列后添加preserve列 -->

<el-table-column prop="preserve" label="保护" width="80">
  <template #default="{ row }">
    <el-tooltip :content="row.preserve ? '已加入白名单，不会被清理' : '未保护'" placement="top">
      <el-icon 
        :style="{ color: row.preserve ? '#E6A23C' : '#C0C4CC', cursor: 'pointer' }" 
        @click="handleTogglePreserve(row)"
      >
        <Star v-if="row.preserve" />
        <StarFilled v-if="row.preserve" />
      </el-icon>
    </el-tooltip>
  </template>
</el-table-column>
```

- [ ] **Step 2: 导入Star图标和API**

```javascript
// frontend/src/views/Schedules.vue script部分
// 在 import 中添加：

import { Plus, Star, StarFilled } from '@element-plus/icons-vue'
import { toggleSchedulePreserve, batchToggleSchedulePreserve } from '../api'

// 或如果已有图标导入，添加 Star, StarFilled
```

- [ ] **Step 3: 添加切换白名单方法**

```javascript
// frontend/src/views/Schedules.vue script部分添加方法：

const handleTogglePreserve = async (row) => {
  try {
    const res = await toggleSchedulePreserve(row.id)
    if (res.code === 0) {
      row.preserve = res.data.preserve
      ElMessage.success(res.message)
    } else {
      ElMessage.error(res.message)
    }
  } catch (e) {
    ElMessage.error('操作失败')
  }
}
```

- [ ] **Step 4: 提交变更**

```bash
git add frontend/src/views/Schedules.vue
git commit -m "feat: add preserve toggle to Schedules table"
```

---

### Task 9: 创建清理管理页面或集成到现有设置

**Files:**
- Modify: `frontend/src/views/AISettings.vue`（或新建Settings.vue）

- [ ] **Step 1: 在AISettings.vue添加清理管理卡片**

找到AISettings.vue，在现有内容后添加清理管理section：

```vue
<!-- frontend/src/views/AISettings.vue -->
<!-- 在模板末尾或合适位置添加 -->

<div class="glass-card cleanup-section" style="margin-top: 20px">
  <div class="glass-card-header">
    <span class="glass-card-title">清理管理</span>
  </div>
  <div class="glass-card-body">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-statistic title="总执行记录" :value="cleanupStats.total_executions" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="白名单记录" :value="cleanupStats.whitelisted_executions" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="待清理" :value="cleanupStats.to_cleanup" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="执行空间(MB)" :value="cleanupStats.execution_spaces_size_mb" :precision="2" />
      </el-col>
    </el-row>
    
    <div style="margin-top: 20px; display: flex; gap: 10px; align-items: center">
      <el-input-number 
        v-model="cleanupThreshold" 
        :min="50" 
        :max="10000" 
        :step="100"
        style="width: 150px"
      />
      <span style="color: var(--text-muted)">保留最近N条记录</span>
      <GlassButton label="保存配置" type="secondary" @click="handleSaveCleanupConfig" />
      <GlassButton label="立即清理" type="warning" @click="handleExecuteCleanup" :loading="cleanupLoading" />
    </div>
  </div>
</div>
```

- [ ] **Step 2: 添加清理相关状态和方法**

```javascript
// frontend/src/views/AISettings.vue script部分添加：

import { getCleanupStats, executeCleanup, getCleanupConfig, updateCleanupConfig } from '../api'

// 添加状态
const cleanupStats = ref({
  total_executions: 0,
  whitelisted_executions: 0,
  to_cleanup: 0,
  execution_spaces_size_mb: 0,
  workflow_spaces_size_mb: 0,
  threshold: 500
})
const cleanupThreshold = ref(500)
const cleanupLoading = ref(false)

// 加载清理统计
const loadCleanupStats = async () => {
  try {
    const res = await getCleanupStats()
    if (res.code === 0) {
      cleanupStats.value = res.data
    }
  } catch (e) {
    console.error('加载清理统计失败', e)
  }
}

// 保存清理配置
const handleSaveCleanupConfig = async () => {
  try {
    const res = await updateCleanupConfig({ threshold: cleanupThreshold.value })
    if (res.code === 0) {
      ElMessage.success('配置已保存')
      cleanupStats.value.threshold = cleanupThreshold.value
    } else {
      ElMessage.error(res.message)
    }
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

// 执行清理
const handleExecuteCleanup = async () => {
  try {
    cleanupLoading.value = true
    const res = await executeCleanup()
    if (res.code === 0) {
      ElMessage.success(`清理完成，释放 ${res.data.freed_space_mb.toFixed(2)} MB`)
      loadCleanupStats()
    } else {
      ElMessage.error(res.message)
    }
  } catch (e) {
    ElMessage.error('清理失败')
  } finally {
    cleanupLoading.value = false
  }
}

// 在onMounted中调用
onMounted(() => {
  loadCleanupStats()
  getCleanupConfig().then(res => {
    if (res.code === 0) {
      cleanupThreshold.value = res.data.threshold
    }
  })
})
```

- [ ] **Step 3: 提交变更**

```bash
git add frontend/src/views/AISettings.vue
git commit -m "feat: add cleanup management section to settings page"
```

---

## Phase 3: Excel编辑后端API

### Task 10: 创建Excel操作API

**Files:**
- Create: `backend/api/excel.py`
- Modify: `backend/api/__init__.py`

- [ ] **Step 1: 创建excel.py API文件**

```python
# backend/api/excel.py
"""
Excel文件操作API
"""
import os
import json
import openpyxl
from openpyxl.utils import get_column_letter
from flask import jsonify, request, send_file
from api import api_bp
from config import Config
import tempfile
import shutil


# 文件大小限制（10MB）
MAX_EXCEL_SIZE = 10 * 1024 * 1024


def get_excel_path(file_id):
    """
    根据file_id获取Excel文件路径
    file_id可以是：
    - uploads目录下的相对路径
    - execution空间的文件路径
    """
    # 首先尝试uploads目录
    uploads_dir = os.path.join(Config.DATA_DIR, 'uploads')
    path = request.args.get('path', '') or request.json.get('path', '')
    
    if path:
        # 直接使用提供的路径
        file_path = os.path.join(uploads_dir, path)
        if os.path.exists(file_path):
            return file_path
    
    # 尝试execution空间
    exec_id = request.args.get('execution_id') or request.json.get('execution_id')
    if exec_id:
        exec_space = Config.get_execution_space(exec_id)
        file_path = os.path.join(exec_space, path)
        if os.path.exists(file_path):
            return file_path
    
    return None


@api_bp.route('/excel/info', methods=['GET'])
def get_excel_info():
    """获取Excel文件信息"""
    try:
        file_path = get_excel_path(None)
        if not file_path:
            return jsonify({'code': 1, 'message': '文件不存在'}), 404
        
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size > MAX_EXCEL_SIZE:
            return jsonify({
                'code': 1, 
                'message': f'文件过大({file_size/1024/1024:.2f}MB)，超过10MB限制，建议下载后本地编辑'
            }), 400
        
        # 检查扩展名
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ['.xlsx', '.xls']:
            return jsonify({'code': 1, 'message': '不是Excel文件'}), 400
        
        # 使用read_only模式读取
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        
        sheets_info = []
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            sheets_info.append({
                'name': sheet_name,
                'rows': sheet.max_row,
                'cols': sheet.max_column
            })
        
        wb.close()
        
        return jsonify({
            'code': 0,
            'data': {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_size_kb': file_size / 1024,
                'sheets': sheets_info
            }
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/excel/sheet', methods=['GET'])
def get_excel_sheet():
    """分页获取sheet数据"""
    try:
        file_path = get_excel_path(None)
        if not file_path:
            return jsonify({'code': 1, 'message': '文件不存在'}), 404
        
        sheet_name = request.args.get('sheet', 'Sheet1')
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 100))
        
        # 限制每次最多获取100行
        limit = min(limit, 100)
        
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        
        if sheet_name not in wb.sheetnames:
            wb.close()
            return jsonify({'code': 1, 'message': f'Sheet "{sheet_name}" 不存在'}), 404
        
        sheet = wb[sheet_name]
        
        rows = []
        # 计算实际读取范围
        start_row = offset + 1  # openpyxl行号从1开始
        end_row = min(offset + limit, sheet.max_row)
        max_cols = min(sheet.max_column, 50)  # 限制列数
        
        for row_idx in range(start_row, end_row + 1):
            row_data = []
            for col_idx in range(1, max_cols + 1):
                cell = sheet.cell(row=row_idx, column=col_idx)
                value = cell.value
                # 转换None为空字符串
                row_data.append(str(value) if value is not None else '')
            rows.append(row_data)
        
        wb.close()
        
        return jsonify({
            'code': 0,
            'data': {
                'sheet_name': sheet_name,
                'total_rows': sheet.max_row,
                'total_cols': sheet.max_column,
                'offset': offset,
                'limit': limit,
                'rows': rows
            }
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/excel/save', methods=['POST'])
def save_excel():
    """保存Excel文件"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        save_type = data.get('save_type', 'incremental')  # incremental or full
        changes = data.get('changes', [])
        sheets_data = data.get('sheets', [])
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'code': 1, 'message': '文件路径无效'}), 400
        
        if save_type == 'incremental':
            # 增量保存：只更新修改的单元格
            wb = openpyxl.load_workbook(file_path)
            
            for change in changes:
                sheet_name = change.get('sheet', 'Sheet1')
                if sheet_name not in wb.sheetnames:
                    continue
                
                sheet = wb[sheet_name]
                row = change.get('row', 0)
                col = change.get('col', 0)
                value = change.get('value', '')
                
                if row > 0 and col > 0:
                    sheet.cell(row=row, column=col, value=value)
            
            wb.save(file_path)
            wb.close()
        
        else:
            # 全量保存：替换整个sheet数据
            wb = openpyxl.load_workbook(file_path)
            
            for sheet_data in sheets_data:
                sheet_name = sheet_data.get('name')
                if sheet_name not in wb.sheetnames:
                    continue
                
                sheet = wb[sheet_name]
                rows = sheet_data.get('data', [])
                
                # 清除现有数据
                for row in sheet.iter_rows():
                    for cell in row:
                        cell.value = None
                
                # 写入新数据
                for row_idx, row_data in enumerate(rows, start=1):
                    for col_idx, value in enumerate(row_data, start=1):
                        sheet.cell(row=row_idx, column=col_idx, value=value)
            
            wb.save(file_path)
            wb.close()
        
        return jsonify({
            'code': 0,
            'message': '保存成功'
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/excel/sheet/add', methods=['POST'])
def add_excel_sheet():
    """新增sheet"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        sheet_name = data.get('sheet_name', 'NewSheet')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'code': 1, 'message': '文件路径无效'}), 400
        
        wb = openpyxl.load_workbook(file_path)
        
        # 检查sheet名称是否已存在
        if sheet_name in wb.sheetnames:
            wb.close()
            return jsonify({'code': 1, 'message': 'Sheet名称已存在'}), 400
        
        wb.create_sheet(sheet_name)
        wb.save(file_path)
        wb.close()
        
        return jsonify({
            'code': 0,
            'message': 'Sheet创建成功'
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/excel/sheet/delete', methods=['DELETE'])
def delete_excel_sheet():
    """删除sheet"""
    try:
        file_path = request.args.get('file_path')
        sheet_name = request.args.get('sheet_name')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'code': 1, 'message': '文件路径无效'}), 400
        
        wb = openpyxl.load_workbook(file_path)
        
        if sheet_name not in wb.sheetnames:
            wb.close()
            return jsonify({'code': 1, 'message': 'Sheet不存在'}), 404
        
        if len(wb.sheetnames) == 1:
            wb.close()
            return jsonify({'code': 1, 'message': '至少保留一个Sheet'}), 400
        
        wb.remove(wb[sheet_name])
        wb.save(file_path)
        wb.close()
        
        return jsonify({
            'code': 0,
            'message': 'Sheet删除成功'
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/excel/sheet/rename', methods=['PUT'])
def rename_excel_sheet():
    """重命名sheet"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        old_name = data.get('old_name')
        new_name = data.get('new_name')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'code': 1, 'message': '文件路径无效'}), 400
        
        wb = openpyxl.load_workbook(file_path)
        
        if old_name not in wb.sheetnames:
            wb.close()
            return jsonify({'code': 1, 'message': '原Sheet不存在'}), 404
        
        if new_name in wb.sheetnames:
            wb.close()
            return jsonify({'code': 1, 'message': '新Sheet名称已存在'}), 400
        
        wb[old_name].title = new_name
        wb.save(file_path)
        wb.close()
        
        return jsonify({
            'code': 0,
            'message': 'Sheet重命名成功'
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500
```

- [ ] **Step 2: 在__init__.py中导入excel模块**

```python
# backend/api/__init__.py
# 在导入列表中添加 excel：

from . import scripts, executions, schedules, files, environments, folders, workflows, workflow_templates, global_variables, ai_configs, ai_scripts, webhooks, webhook_trigger, backup, selection, upload, system, excel
```

- [ ] **Step 3: 提交变更**

```bash
git add backend/api/excel.py backend/api/__init__.py
git commit -m "feat: create Excel operation API for file editing"
```

---

## Phase 4: Excel编辑前端

### Task 11: 安装Luckysheet依赖

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: 安装Luckysheet**

```bash
cd E:/wsl/check/conf-manage/frontend
npm install luckysheet
```

- [ ] **Step 2: 确认安装成功**

检查package.json中是否包含luckysheet依赖。

---

### Task 12: 创建ExcelEditor页面

**Files:**
- Create: `frontend/src/views/ExcelEditor.vue`
- Modify: `frontend/src/router/index.js`

- [ ] **Step 1: 创建ExcelEditor.vue基础结构**

```vue
<!-- frontend/src/views/ExcelEditor.vue -->
<template>
  <div class="excel-editor-page">
    <!-- 顶部工具栏 -->
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <GlassButton label="保存" type="primary" @click="handleSave" :loading="saving" />
        <GlassButton label="撤销" type="secondary" @click="handleUndo" />
        <GlassButton label="重做" type="secondary" @click="handleRedo" />
      </div>
      <div class="toolbar-center">
        <span class="file-name">{{ fileName }}</span>
      </div>
      <div class="toolbar-right">
        <GlassButton label="新增Sheet" type="secondary" @click="handleAddSheet" />
        <GlassButton label="删除Sheet" type="danger" @click="handleDeleteSheet" />
        <div class="collaborators">
          <span class="collaborator-label">协作者:</span>
          <span class="collaborator-count">{{ collaborators.length }}</span>
        </div>
      </div>
    </div>

    <!-- Luckysheet容器 -->
    <div class="editor-container">
      <div id="luckysheet" style="width: 100%; height: 100%"></div>
    </div>

    <!-- 底部状态栏 -->
    <div class="editor-statusbar">
      <div class="statusbar-left">
        <span v-for="sheet in sheets" 
              :key="sheet.name"
              class="sheet-tab"
              :class="{ active: currentSheet === sheet.name }"
              @click="switchSheet(sheet.name)"
        >
          {{ sheet.name }}
        </span>
      </div>
      <div class="statusbar-right">
        <span class="save-status">{{ saveStatus }}</span>
      </div>
    </div>

    <!-- 新增Sheet对话框 -->
    <el-dialog v-model="addSheetDialogVisible" title="新增Sheet" width="300px">
      <el-input v-model="newSheetName" placeholder="请输入Sheet名称" />
      <template #footer>
        <GlassButton label="取消" type="secondary" @click="addSheetDialogVisible = false" />
        <GlassButton label="确认" type="primary" @click="confirmAddSheet" />
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import GlassButton from '../components/GlassButton.vue'
import { getExcelInfo, getExcelSheet, saveExcel, addExcelSheet, deleteExcelSheet, renameExcelSheet } from '../api'
import luckysheet from 'luckysheet'
import 'luckysheet/dist/plugins/css/pluginsCss.css'
import 'luckysheet/dist/plugins/plugins.css'
import 'luckysheet/dist/css/luckysheet.css'
import 'luckysheet/dist/plugins/font/font.css'

const route = useRoute()

// 状态
const fileName = ref('')
const filePath = ref('')
const sheets = ref([])
const currentSheet = ref('')
const saving = ref(false)
const saveStatus = ref('已保存')
const collaborators = ref([])
const addSheetDialogVisible = ref(false)
const newSheetName = ref('')

// Luckysheet实例引用
let luckysheetInstance = null
// 本地数据缓存
const sheetDataCache = {}
// 修改记录
const pendingChanges = []

// 初始化Luckysheet
const initLuckysheet = async () => {
  // 获取文件信息
  const infoRes = await getExcelInfo({ path: route.query.path, execution_id: route.query.execution_id })
  if (infoRes.code !== 0) {
    ElMessage.error(infoRes.message || '无法加载文件信息')
    return
  }
  
  fileName.value = infoRes.data.file_name
  filePath.value = infoRes.data.file_path
  sheets.value = infoRes.data.sheets
  
  // 加载第一个sheet数据
  const firstSheet = sheets.value[0]?.name || 'Sheet1'
  const sheetRes = await getExcelSheet({
    path: route.query.path,
    execution_id: route.query.execution_id,
    sheet: firstSheet,
    offset: 0,
    limit: 100
  })
  
  if (sheetRes.code === 0) {
    currentSheet.value = firstSheet
    sheetDataCache[firstSheet] = sheetRes.data.rows
    
    // 转换为Luckysheet格式
    const sheetData = convertToLuckysheetFormat(sheetRes.data.rows, firstSheet)
    
    luckysheet.create({
      container: 'luckysheet',
      showinfobar: false,
      showsheetbar: false,  // 使用自定义sheet栏
      showstatisticbar: true,
      enableAddRow: true,
      enableAddBack: true,
      data: [sheetData],
      hook: {
        cellEditBefore: (r, c) => {
          // 记录编辑前的值
        },
        cellUpdated: (r, c, oldValue, newValue, isRefresh) => {
          if (!isRefresh) {
            // 记录修改
            pendingChanges.push({
              sheet: currentSheet.value,
              row: r + 1,  // Luckysheet从0开始，Excel从1开始
              col: c + 1,
              value: newValue
            })
            saveStatus.value = '未保存'
            
            // TODO: 通过WebSocket广播
          }
        }
      }
    })
  }
}

// 转换数据格式
const convertToLuckysheetFormat = (rows, sheetName) => {
  const celldata = []
  
  rows.forEach((row, rowIdx) => {
    row.forEach((value, colIdx) => {
      if (value !== '') {
        celldata.push({
          r: rowIdx,
          c: colIdx,
          v: { v: value, m: value }
        })
      }
    })
  })
  
  return {
    name: sheetName,
    celldata: celldata,
    row: Math.max(rows.length, 100),
    column: Math.max(rows[0]?.length || 26, 26)
  }
}

// 切换Sheet
const switchSheet = async (sheetName) => {
  if (sheetName === currentSheet.value) return
  
  // 检查是否已缓存
  if (!sheetDataCache[sheetName]) {
    const res = await getExcelSheet({
      path: route.query.path,
      execution_id: route.query.execution_id,
      sheet: sheetName,
      offset: 0,
      limit: 100
    })
    
    if (res.code === 0) {
      sheetDataCache[sheetName] = res.data.rows
    } else {
      ElMessage.error('加载Sheet失败')
      return
    }
  }
  
  currentSheet.value = sheetName
  
  // 更新Luckysheet显示
  const sheetData = convertToLuckysheetFormat(sheetDataCache[sheetName], sheetName)
  luckysheet.setSheetData({ sheetData })
}

// 保存
const handleSave = async () => {
  if (pendingChanges.length === 0) {
    ElMessage.info('无修改需要保存')
    return
  }
  
  saving.value = true
  try {
    const res = await saveExcel({
      file_path: filePath.value,
      save_type: 'incremental',
      changes: pendingChanges
    })
    
    if (res.code === 0) {
      ElMessage.success('保存成功')
      pendingChanges.length = 0
      saveStatus.value = '已保存'
    } else {
      ElMessage.error(res.message || '保存失败')
    }
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 撤销
const handleUndo = () => {
  luckysheet.undo()
}

// 重做
const handleRedo = () => {
  luckysheet.redo()
}

// 新增Sheet
const handleAddSheet = () => {
  newSheetName.value = ''
  addSheetDialogVisible.value = true
}

const confirmAddSheet = async () => {
  if (!newSheetName.value.trim()) {
    ElMessage.warning('请输入Sheet名称')
    return
  }
  
  try {
    const res = await addExcelSheet({
      file_path: filePath.value,
      sheet_name: newSheetName.value.trim()
    })
    
    if (res.code === 0) {
      sheets.value.push({ name: newSheetName.value.trim(), rows: 100, cols: 26 })
      sheetDataCache[newSheetName.value.trim()] = []
      addSheetDialogVisible.value = false
      ElMessage.success('Sheet创建成功')
    } else {
      ElMessage.error(res.message)
    }
  } catch (e) {
    ElMessage.error('创建失败')
  }
}

// 删除Sheet
const handleDeleteSheet = async () => {
  if (sheets.value.length <= 1) {
    ElMessage.warning('至少保留一个Sheet')
    return
  }
  
  try {
    const res = await deleteExcelSheet({
      file_path: filePath.value,
      sheet_name: currentSheet.value
    })
    
    if (res.code === 0) {
      // 移除本地数据
      const idx = sheets.value.findIndex(s => s.name === currentSheet.value)
      if (idx !== -1) {
        sheets.value.splice(idx, 1)
        delete sheetDataCache[currentSheet.value]
      }
      // 切换到第一个sheet
      switchSheet(sheets.value[0].name)
      ElMessage.success('Sheet删除成功')
    } else {
      ElMessage.error(res.message)
    }
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  initLuckysheet()
})

onUnmounted(() => {
  // 清理Luckysheet
  luckysheet.destroy()
})
</script>

<style scoped>
.excel-editor-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-primary);
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-secondary);
}

.toolbar-left, .toolbar-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

.toolbar-center {
  flex: 1;
  text-align: center;
}

.file-name {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
}

.collaborators {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-left: 15px;
  color: var(--text-secondary);
}

.collaborator-count {
  font-weight: 500;
  color: var(--accent-primary);
}

.editor-container {
  flex: 1;
  overflow: hidden;
}

.editor-statusbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 15px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-secondary);
}

.statusbar-left {
  display: flex;
  gap: 10px;
}

.sheet-tab {
  padding: 5px 15px;
  border-radius: 4px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.sheet-tab:hover {
  background: var(--glass-active);
}

.sheet-tab.active {
  background: var(--accent-primary);
  color: white;
}

.save-status {
  color: var(--text-muted);
  font-size: 12px;
}
</style>
```

- [ ] **Step 2: 添加路由**

```javascript
// frontend/src/router/index.js
// 在routes数组中添加：

{
  path: '/excel-editor',
  name: 'ExcelEditor',
  component: () => import('../views/ExcelEditor.vue'),
  meta: { requiresAuth: true }
}
```

- [ ] **Step 3: 提交变更**

```bash
git add frontend/src/views/ExcelEditor.vue frontend/src/router/index.js frontend/package.json frontend/package-lock.json
git commit -m "feat: create ExcelEditor page with Luckysheet integration"
```

---

### Task 13: Files.vue点击Excel跳转编辑器

**Files:**
- Modify: `frontend/src/views/Files.vue`

- [ ] **Step 1: 修改Excel文件点击逻辑**

找到Files.vue中处理文件点击或预览的部分，修改Excel文件的处理：

```javascript
// frontend/src/views/Files.vue
// 找到 handlePreview 或类似的文件点击方法

// 如果是Excel文件，跳转到编辑器页面
const handleFileClick = (file) => {
  const ext = file.name.split('.').pop().toLowerCase()
  if (ext === 'xlsx' || ext === 'xls') {
    // 新标签页打开Excel编辑器
    const url = `/excel-editor?path=${encodeURIComponent(file.path)}`
    window.open(url, '_blank')
  } else {
    // 其他文件使用原有预览逻辑
    handlePreview(file)
  }
}

// 或者修改现有预览逻辑：
const handlePreview = (file) => {
  const ext = file.name.split('.').pop().toLowerCase()
  if (ext === 'xlsx' || ext === 'xls') {
    // Excel文件跳转编辑器
    const url = `/excel-editor?path=${encodeURIComponent(file.path)}`
    window.open(url, '_blank')
    return
  }
  // 其他文件继续原有逻辑...
}
```

- [ ] **Step 2: 提交变更**

```bash
git add frontend/src/views/Files.vue
git commit -m "feat: redirect Excel files to ExcelEditor on click"
```

---

## Phase 5: WebSocket协作功能

### Task 14: 后端WebSocket集成

**Files:**
- Create: `backend/websocket/__init__.py`
- Create: `backend/websocket/excel_ws.py`
- Modify: `backend/app.py`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 安装Flask-SocketIO**

```bash
cd E:/wsl/check/conf-manage/backend
pip install flask-socketio python-engineio python-socketio
```

或更新requirements.txt：

```text
# backend/requirements.txt 添加：
flask-socketio>=5.3.0
python-engineio>=4.3.0
python-socketio>=5.5.0
```

- [ ] **Step 2: 创建websocket模块**

```python
# backend/websocket/__init__.py
"""
WebSocket模块初始化
"""
from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*")

__all__ = ['socketio']
```

```python
# backend/websocket/excel_ws.py
"""
Excel协作WebSocket处理
"""
import random
from flask import request
from flask_socketio import emit, join_room, leave_room
from websocket import socketio

# 房间用户管理
room_users = {}  # {room_id: {user_id: {name, color}}}

# 用户颜色列表
USER_COLORS = [
    '#FF5733', '#33FF57', '#3357FF', '#FF33F5', 
    '#F5FF33', '#33FFF5', '#FF8C33', '#8C33FF'
]


@socketio.on('connect', namespace='/excel')
def handle_connect():
    """连接建立"""
    print(f"[ExcelWS] Client connected: {request.sid}")


@socketio.on('disconnect', namespace='/excel')
def handle_disconnect():
    """连接断开"""
    # 从所有房间移除用户
    for room_id, users in room_users.items():
        if request.sid in users:
            user_info = users.pop(request.sid)
            emit('user_left', {
                'user_id': request.sid,
                'user_name': user_info['name']
            }, room=room_id)
    
    print(f"[ExcelWS] Client disconnected: {request.sid}")


@socketio.on('join', namespace='/excel')
def handle_join(data):
    """加入编辑房间"""
    file_id = data.get('file_id')
    user_name = data.get('user_name', '匿名用户')
    
    room_id = f"excel_{file_id}"
    join_room(room_id)
    
    # 分配颜色
    color = USER_COLORS[random.randint(0, len(USER_COLORS) - 1)]
    
    # 记录用户
    if room_id not in room_users:
        room_users[room_id] = {}
    
    room_users[room_id][request.sid] = {
        'name': user_name,
        'color': color
    }
    
    # 通知用户加入成功
    emit('joined', {
        'room_id': room_id,
        'user_id': request.sid,
        'user_name': user_name,
        'user_color': color,
        'users': list(room_users[room_id].values())
    })
    
    # 通知其他用户
    emit('user_joined', {
        'user_id': request.sid,
        'user_name': user_name,
        'user_color': color
    }, room=room_id, include_self=False)
    
    print(f"[ExcelWS] User {user_name} joined room {room_id}")


@socketio.on('leave', namespace='/excel')
def handle_leave(data):
    """离开编辑房间"""
    file_id = data.get('file_id')
    room_id = f"excel_{file_id}"
    
    if room_id in room_users and request.sid in room_users[room_id]:
        user_info = room_users[room_id].pop(request.sid)
        leave_room(room_id)
        
        emit('user_left', {
            'user_id': request.sid,
            'user_name': user_info['name']
        }, room=room_id)
    
    print(f"[ExcelWS] User left room {room_id}")


@socketio.on('edit', namespace='/excel')
def handle_edit(data):
    """处理编辑操作并广播"""
    file_id = data.get('file_id')
    sheet_name = data.get('sheet_name')
    operation = data.get('operation')
    
    room_id = f"excel_{file_id}"
    
    # 获取用户信息
    user_info = room_users.get(room_id, {}).get(request.sid, {})
    
    # 广播给房间内其他用户
    emit('sync', {
        'operation': operation,
        'sheet_name': sheet_name,
        'user_id': request.sid,
        'user_name': user_info.get('name', '匿名'),
        'user_color': user_info.get('color', '#FF5733')
    }, room=room_id, include_self=False)


@socketio.on('cursor_move', namespace='/excel')
def handle_cursor_move(data):
    """处理光标移动"""
    file_id = data.get('file_id')
    sheet_name = data.get('sheet_name')
    row = data.get('row')
    col = data.get('col')
    
    room_id = f"excel_{file_id}"
    user_info = room_users.get(room_id, {}).get(request.sid, {})
    
    emit('cursor_update', {
        'sheet_name': sheet_name,
        'row': row,
        'col': col,
        'user_id': request.sid,
        'user_name': user_info.get('name', '匿名'),
        'user_color': user_info.get('color', '#FF5733')
    }, room=room_id, include_self=False)


@socketio.on('save_complete', namespace='/excel')
def handle_save_complete(data):
    """通知保存完成"""
    file_id = data.get('file_id')
    room_id = f"excel_{file_id}"
    
    emit('saved', {
        'file_id': file_id,
        'message': '文件已保存'
    }, room=room_id)
```

- [ ] **Step 3: 修改app.py集成SocketIO**

```python
# backend/app.py
# 在导入部分添加：

from websocket import socketio

# 在 create_app 函数末尾，return之前添加：

# 初始化SocketIO
socketio.init_app(app)

# 修改启动方式（文件末尾）：
if __name__ == '__main__':
    app = create_app()
    print('=' * 60)
    print('脚本工具管理系统后端服务')
    print('=' * 60)
    print(f'服务地址: http://localhost:5001')
    print(f'API地址: http://localhost:5001/api')
    print(f'健康检查: http://localhost:5001/health')
    print(f'WebSocket: ws://localhost:5001/excel')
    print('=' * 60)
    # 使用socketio.run代替app.run
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)
```

- [ ] **Step 4: 提交变更**

```bash
git add backend/websocket/__init__.py backend/websocket/excel_ws.py backend/app.py backend/requirements.txt
git commit -m "feat: integrate Flask-SocketIO for Excel collaboration"
```

---

### Task 15: 前端WebSocket客户端

**Files:**
- Create: `frontend/src/utils/excel-socket.js`
- Modify: `frontend/src/views/ExcelEditor.vue`
- Modify: `frontend/package.json`

- [ ] **Step 1: 安装Socket.IO客户端**

```bash
cd E:/wsl/check/conf-manage/frontend
npm install socket.io-client
```

- [ ] **Step 2: 创建WebSocket客户端封装**

```javascript
// frontend/src/utils/excel-socket.js
/**
 * Excel协作WebSocket客户端
 */
import { io } from 'socket.io-client'

class ExcelSocket {
  constructor() {
    this.socket = null
    this.roomId = null
    this.userId = null
    this.callbacks = {}
  }

  /**
   * 连接到服务器
   * @param {string} fileId - 文件ID
   * @param {string} userName - 用户名
   */
  connect(fileId, userName) {
    if (this.socket) {
      this.disconnect()
    }

    this.socket = io('http://localhost:5001/excel', {
      transports: ['websocket', 'polling']
    })

    this.socket.on('connect', () => {
      console.log('[ExcelSocket] Connected')
      this.userId = this.socket.id
      this.joinRoom(fileId, userName)
    })

    this.socket.on('joined', (data) => {
      console.log('[ExcelSocket] Joined room:', data.room_id)
      this.roomId = data.room_id
      this.trigger('joined', data)
    })

    this.socket.on('user_joined', (data) => {
      console.log('[ExcelSocket] User joined:', data.user_name)
      this.trigger('user_joined', data)
    })

    this.socket.on('user_left', (data) => {
      console.log('[ExcelSocket] User left:', data.user_name)
      this.trigger('user_left', data)
    })

    this.socket.on('sync', (data) => {
      this.trigger('sync', data)
    })

    this.socket.on('cursor_update', (data) => {
      this.trigger('cursor_update', data)
    })

    this.socket.on('saved', (data) => {
      this.trigger('saved', data)
    })

    this.socket.on('disconnect', () => {
      console.log('[ExcelSocket] Disconnected')
      this.trigger('disconnect')
    })

    this.socket.on('connect_error', (error) => {
      console.error('[ExcelSocket] Connection error:', error)
      this.trigger('error', error)
    })
  }

  /**
   * 加入房间
   */
  joinRoom(fileId, userName) {
    this.socket.emit('join', {
      file_id: fileId,
      user_name: userName
    })
  }

  /**
   * 离开房间
   */
  leaveRoom(fileId) {
    this.socket.emit('leave', {
      file_id: fileId
    })
  }

  /**
   * 发送编辑操作
   */
  sendEdit(fileId, sheetName, operation) {
    this.socket.emit('edit', {
      file_id: fileId,
      sheet_name: sheetName,
      operation: operation
    })
  }

  /**
   * 发送光标位置
   */
  sendCursor(fileId, sheetName, row, col) {
    this.socket.emit('cursor_move', {
      file_id: fileId,
      sheet_name: sheetName,
      row: row,
      col: col
    })
  }

  /**
   * 通知保存完成
   */
  notifySaved(fileId) {
    this.socket.emit('save_complete', {
      file_id: fileId
    })
  }

  /**
   * 断开连接
   */
  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }

  /**
   * 注册回调
   */
  on(event, callback) {
    this.callbacks[event] = callback
  }

  /**
   * 触发回调
   */
  trigger(event, data) {
    if (this.callbacks[event]) {
      this.callbacks[event](data)
    }
  }
}

export default new ExcelSocket()
```

- [ ] **Step 3: 在ExcelEditor中集成WebSocket**

```javascript
// frontend/src/views/ExcelEditor.vue
// 在script setup部分添加：

import excelSocket from '../utils/excel-socket'

// 协作者状态扩展
const collaborators = ref([])
const myUserInfo = ref({ name: '', color: '' })
const cursorPositions = ref({})  // {userId: {row, col, color}}

// 连接WebSocket
const connectWebSocket = () => {
  // 获取用户名（可以从localStorage或登录信息获取）
  const userName = localStorage.getItem('user_name') || '用户' + Math.floor(Math.random() * 1000)
  
  excelSocket.connect(route.query.file_id || route.query.path, userName)
  
  excelSocket.on('joined', (data) => {
    myUserInfo.value = {
      name: data.user_name,
      color: data.user_color
    }
    collaborators.value = data.users
  })
  
  excelSocket.on('user_joined', (data) => {
    collaborators.value.push({
      name: data.user_name,
      color: data.user_color
    })
    ElMessage.info(`${data.user_name} 加入了编辑`)
  })
  
  excelSocket.on('user_left', (data) => {
    const idx = collaborators.value.findIndex(u => u.name === data.user_name)
    if (idx !== -1) {
      collaborators.value.splice(idx, 1)
    }
    delete cursorPositions.value[data.user_id]
    ElMessage.info(`${data.user_name} 离开了编辑`)
  })
  
  excelSocket.on('sync', (data) => {
    // 应用其他用户的编辑
    const { operation, user_color } = data
    if (operation.op === 'cell_update') {
      // 更新Luckysheet单元格
      luckysheet.setCellValue(operation.row - 1, operation.col - 1, operation.value)
      // 高亮显示（可选）
      luckysheet.setRangeStyle(operation.row - 1, operation.col - 1, operation.row - 1, operation.col - 1, {
        'bg': user_color + '20'  // 添加透明度
      })
    }
  })
  
  excelSocket.on('cursor_update', (data) => {
    cursorPositions.value[data.user_id] = {
      row: data.row,
      col: data.col,
      color: data.user_color,
      name: data.user_name
    }
  })
  
  excelSocket.on('saved', () => {
    saveStatus.value = '已保存'
  })
}

// 修改handleSave，保存后通知其他用户
const handleSave = async () => {
  // ... 原有保存逻辑 ...
  if (res.code === 0) {
    // 通知其他用户
    excelSocket.notifySaved(route.query.file_id || route.query.path)
  }
}

// 修改Luckysheet hook，发送编辑操作
const initLuckysheet = async () => {
  // ... 原有初始化逻辑 ...
  
  luckysheet.create({
    // ...
    hook: {
      cellUpdated: (r, c, oldValue, newValue, isRefresh) => {
        if (!isRefresh) {
          pendingChanges.push({
            sheet: currentSheet.value,
            row: r + 1,
            col: c + 1,
            value: newValue
          })
          saveStatus.value = '未保存'
          
          // 发送编辑操作
          excelSocket.sendEdit(
            route.query.file_id || route.query.path,
            currentSheet.value,
            { op: 'cell_update', row: r + 1, col: c + 1, value: newValue }
          )
        }
      },
      rangeSelect: (range) => {
        // 发送光标位置
        if (range.length > 0) {
          excelSocket.sendCursor(
            route.query.file_id || route.query.path,
            currentSheet.value,
            range[0].row[0],
            range[0].column[0]
          )
        }
      }
    }
  })
}

// 在onMounted中连接WebSocket
onMounted(() => {
  initLuckysheet()
  connectWebSocket()
})

// 在onUnmounted中断开连接
onUnmounted(() => {
  luckysheet.destroy()
  excelSocket.disconnect()
})
```

- [ ] **Step 4: 提交变更**

```bash
git add frontend/src/utils/excel-socket.js frontend/src/views/ExcelEditor.vue frontend/package.json frontend/package-lock.json
git commit -m "feat: integrate WebSocket client for real-time Excel collaboration"
```

---

## 完成检查

- [ ] **Step 1: 运行后端验证**

```bash
cd E:/wsl/check/conf-manage/backend
python app.py
```

检查：
- 应用启动时清理日志输出
- `/api/system/cleanup/stats` API可访问
- `/api/schedules` 返回preserve字段
- `/api/excel/info` API可访问
- WebSocket `/excel` namespace正常

- [ ] **Step 2: 运行前端验证**

```bash
cd E:/wsl/check/conf-manage/frontend
npm run dev
```

检查：
- Schedules.vue显示保护列，可切换白名单
- AISettings.vue显示清理统计和按钮
- 点击Excel文件跳转到ExcelEditor页面
- ExcelEditor加载Luckysheet正常
- WebSocket连接成功

- [ ] **Step 3: 最终提交**

```bash
git status
git log --oneline -10
```

---

## 总结

**实现内容：**
1. ✅ Schedule模型添加preserve字段（白名单）
2. ✅ 清理工具模块（cleanup.py）
3. ✅ 系统管理API（system.py）
4. ✅ 启动时自动清理
5. ✅ 前端白名单开关UI
6. ✅ 清理统计管理页面
7. ✅ Excel操作API（excel.py）
8. ✅ ExcelEditor页面（Luckysheet）
9. ✅ WebSocket协作功能

**预计工作量：** 15个任务，约2-3小时