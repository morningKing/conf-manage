# 自动清理与Excel编辑功能设计文档

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现历史任务自动清理（支持白名单）和Excel文件在线编辑（支持多人协作）

**Architecture:** 
- 清理功能：数据库字段扩展 + 清理工具模块 + 系统API + 启动时/手动触发
- Excel编辑：独立编辑页面 + Luckysheet库 + 后端API化 + WebSocket协作

**Tech Stack:** 
- 后端：Flask、openpyxl、Flask-SocketIO（WebSocket）
- 前端：Vue 3、Luckysheet、Socket.IO客户端

---

## 一、自动清理历史任务和执行残留文件

### 1.1 数据库变更

**Schedule表新增字段：**
```python
# backend/models/schedule.py
preserve = db.Column(db.Boolean, default=False, nullable=False)
```

**说明：**
- `preserve=True` 表示该定时任务在白名单中，其执行记录永不被自动清理
- `preserve=False`（默认）表示该任务的执行记录遵循正常清理规则

### 1.2 配置项

**backend/config.py 新增：**
```python
# 清理阈值：保留最近N条执行记录
CLEANUP_THRESHOLD = 500  # 默认保留500条
```

### 1.3 清理规则

**保留条件（不清理）：**
1. Schedule的 `preserve=True` 的所有Execution记录及其执行空间
2. 最近 `CLEANUP_THRESHOLD` 条Execution记录（按created_at降序）

**清理内容：**
1. Execution数据库记录（超出保留条件的）
2. `execution_spaces/execution_{id}/` 目录
3. `workflow_execution_spaces/workflow_execution_{id}/` 目录（关联WorkflowExecution记录）
4. 对应的日志文件（`logs/execution_{id}.log`，如果存在）

**清理顺序：**
1. 查询所有Execution记录，按created_at降序排序
2. 识别白名单Schedule对应的Execution ID集合
3. 取前CLEANUP_THRESHOLD条 + 白名单Execution作为保留集合
4. 其余Execution执行清理（删除数据库记录 + 删除文件系统目录）

### 1.4 API设计

**新建 backend/api/system.py：**

| API | 方法 | 说明 |
|-----|------|------|
| `/api/system/cleanup` | POST | 执行清理操作 |
| `/api/system/cleanup/stats` | GET | 获取清理统计信息 |
| `/api/system/cleanup/config` | GET/PUT | 获取/修改清理配置 |

**POST /api/system/cleanup 响应：**
```json
{
  "code": 0,
  "data": {
    "deleted_executions": 120,
    "deleted_execution_spaces": 120,
    "deleted_workflow_spaces": 5,
    "freed_space_mb": 45.2
  },
  "message": "清理完成"
}
```

**GET /api/system/cleanup/stats 响应：**
```json
{
  "code": 0,
  "data": {
    "total_executions": 600,
    "whitelisted_executions": 50,
    "to_cleanup": 50,
    "execution_spaces_size_mb": 120,
    "workflow_spaces_size_mb": 30,
    "threshold": 500
  }
}
```

### 1.5 清理触发机制

**触发方式：**
1. **启动时清理**：应用启动时检查并执行一次清理（如果需要）
2. **手动触发**：提供API接口，用户可在系统设置页面手动触发

**实现位置：**
- `backend/utils/cleanup.py`：清理逻辑模块
- `backend/app.py`：启动时调用 `run_cleanup_if_needed()`

### 1.6 前端UI

**定时任务列表页面（Schedules.vue）：**
- 每行添加"保护"开关（星标图标，点击切换preserve状态）
- 批量操作添加"设置白名单"按钮
- 表格列添加"保护状态"列

**系统设置页面（Settings.vue或新建）：**
- 显示清理统计信息卡片
- "立即清理"按钮（点击调用清理API）
- 可配置清理阈值（输入框 + 保存按钮）

---

## 二、Excel编辑功能

### 2.1 前端架构

**新建页面 frontend/src/views/ExcelEditor.vue：**

**页面布局：**
```
+--------------------------------------------------+
|  [保存] [撤销] [重做] | [新增Sheet] [删除Sheet]  | 协作者: 3人
+--------------------------------------------------+
|                                                  |
|              Luckysheet 编辑区域                  |
|                                                  |
+--------------------------------------------------+
| Sheet1 | Sheet2 | Sheet3 |        | 状态: 已保存 |
+--------------------------------------------------+
```

**路由配置：**
```javascript
// frontend/src/router/index.js
{
  path: '/excel-editor',
  name: 'ExcelEditor',
  component: () => import('../views/ExcelEditor.vue'),
  meta: { requiresAuth: true }
}
```

**访问方式：**
- Files.vue点击Excel文件 → `window.open('/excel-editor?file_id=123', '_blank')`

### 2.2 Luckysheet集成

**安装依赖：**
```bash
npm install luckysheet
```

**初始化配置：**
```javascript
// ExcelEditor.vue
import { createWorkbook } from 'luckysheet'

luckysheet.create({
  container: 'luckysheet',
  showinfobar: false,
  showsheetbar: true,
  showstatisticbar: true,
  enableAddRow: true,
  enableAddBack: true,
  // 自定义钩子
  hook: {
    cellUpdated: (r, c, oldValue, newValue) => {
      // 通过WebSocket广播编辑操作
      socket.emit('edit', { row: r, col: c, value: newValue })
    }
  }
})
```

### 2.3 后端API设计

**新建 backend/api/excel.py：**

| API | 方法 | 说明 |
|-----|------|------|
| `/api/excel/info` | GET | 获取Excel文件信息 |
| `/api/excel/sheet` | GET | 分页获取sheet数据 |
| `/api/excel/save` | POST | 保存Excel文件 |
| `/api/excel/sheet/add` | POST | 新增sheet |
| `/api/excel/sheet/delete` | DELETE | 删除sheet |
| `/api/excel/sheet/rename` | PUT | 重命名sheet |

**GET /api/excel/info?file_id=123 响应：**
```json
{
  "code": 0,
  "data": {
    "file_id": 123,
    "file_name": "data.xlsx",
    "file_size_kb": 450,
    "sheets": [
      { "name": "Sheet1", "rows": 5000, "cols": 26 },
      { "name": "Sheet2", "rows": 100, "cols": 10 }
    ]
  }
}
```

**GET /api/excel/sheet?file_id=123&sheet=Sheet1&offset=0&limit=100 响应：**
```json
{
  "code": 0,
  "data": {
    "sheet_name": "Sheet1",
    "total_rows": 5000,
    "offset": 0,
    "limit": 100,
    "rows": [
      ["A1", "B1", "C1", ...],
      ["A2", "B2", "C2", ...],
      ...
    ]
  }
}
```

**POST /api/excel/save 请求体：**
```json
{
  "file_id": 123,
  "sheets": [
    {
      "name": "Sheet1",
      "data": [...],  // 或增量更新：{ "changes": [{row: 5, col: 3, value: "xxx"}] }
    }
  ]
}
```

### 2.4 WebSocket协作

**技术选型：Flask-SocketIO**

**安装：**
```bash
pip install flask-socketio
```

**WebSocket端点：`/api/excel/ws`**

**消息格式：**

**客户端发送编辑操作：**
```json
{
  "type": "edit",
  "file_id": 123,
  "sheet_name": "Sheet1",
  "operation": {
    "op": "cell_update",
    "row": 5,
    "col": 3,
    "value": "新值"
  },
  "user_id": "user_abc",
  "timestamp": 1700000000000
}
```

**服务端广播：**
```json
{
  "type": "sync",
  "operation": {
    "op": "cell_update",
    "row": 5,
    "col": 3,
    "value": "新值"
  },
  "user_id": "user_abc",
  "user_name": "张三",
  "user_color": "#FF5733"
}
```

**其他消息类型：**
- `join`: 用户加入编辑房间
- `leave`: 用户离开编辑房间
- `cursor_move`: 用户移动光标位置（显示其他用户正在编辑哪里）
- `save_complete`: 服务端通知保存完成

**协作功能实现：**
1. 用户进入ExcelEditor时建立WebSocket连接
2. 发送 `join` 消息加入房间（房间名 = `excel_{file_id}`）
3. 服务端维护房间用户列表，广播 `user_joined` 给其他用户
4. 每个编辑操作实时广播给房间内其他用户
5. 前端显示在线用户列表，每个用户用不同颜色标识
6. Luckysheet渲染其他用户的编辑内容

### 2.5 性能优化策略

**后端优化：**
1. 使用openpyxl `read_only=True` 模式读取（不加载整个文件到内存）
2. 使用openpyxl `write_only=True` 模式写入（流式写入）
3. 分页返回sheet数据（每次最多100行×50列）
4. 大文件（>10MB）返回错误提示，建议下载后本地编辑

**前端优化：**
1. Luckysheet内置虚拟滚动，只渲染可视区域单元格
2. 首屏只加载前100行数据
3. 滚动到底部时动态请求下一页数据
4. 增量保存：只提交修改的单元格，不提交整个sheet
5. 本地缓存已加载的数据，避免重复请求

**增量保存协议：**
```json
{
  "file_id": 123,
  "save_type": "incremental",  // 或 "full"
  "changes": [
    { "sheet": "Sheet1", "row": 5, "col": 3, "value": "xxx" },
    { "sheet": "Sheet1", "row": 10, "col": 1, "value": "yyy" }
  ]
}
```

---

## 三、文件结构变更

### 3.1 新增文件

```
backend/
  utils/cleanup.py           # 清理逻辑模块
  api/system.py              # 系统管理API（清理接口）
  api/excel.py               # Excel操作API
  websocket/                 # WebSocket模块目录
    __init__.py
    excel_ws.py              # Excel协作WebSocket处理

frontend/
  src/views/ExcelEditor.vue  # Excel编辑页面
  src/utils/excel-socket.js  # WebSocket客户端封装
```

### 3.2 修改文件

```
backend/
  models/schedule.py         # 添加preserve字段
  config.py                  # 添加CLEANUP_THRESHOLD配置
  app.py                     # 启动时清理 + 注册SocketIO

frontend/
  src/router/index.js        # 添加ExcelEditor路由
  src/views/Schedules.vue    # 白名单开关UI
  src/views/Files.vue        # Excel文件点击跳转逻辑
  src/api/index.js           # 添加Excel相关API调用
```

---

## 四、实现顺序

建议按以下顺序实现：

1. **Phase 1: 清理功能基础**
   - Schedule表添加preserve字段
   - 配置项添加
   - 清理工具模块实现
   - 系统API实现
   - 启动时清理集成

2. **Phase 2: 清理功能前端**
   - Schedules.vue白名单开关
   - 系统设置页面清理统计和触发按钮

3. **Phase 3: Excel编辑基础**
   - 后端Excel API实现（不含WebSocket）
   - 前端ExcelEditor页面（Luckysheet集成）
   - Files.vue跳转逻辑
   - 基础保存功能

4. **Phase 4: Excel协作功能**
   - Flask-SocketIO集成
   - WebSocket协作实现
   - 前端WebSocket客户端
   - 协作者显示和同步