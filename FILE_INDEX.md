# 项目文件索引

## 后端文件索引

### 核心应用文件

**文件：** `/backend/app.py` (72行)
- Flask应用入口
- 初始化数据库、CORS、蓝图
- 健康检查端点
- 错误处理

**文件：** `/backend/config.py` (87行)
- 路径配置：SCRIPTS_DIR, WORKSPACES_DIR, EXECUTION_SPACES_DIR, LOGS_DIR, DATA_DIR
- 支持的脚本类型：python, javascript
- 执行器路径：PYTHON_EXECUTABLE, NODE_EXECUTABLE
- 超时配置：EXECUTION_TIMEOUT = 300秒
- 上传配置：MAX_CONTENT_LENGTH = 16MB
- CORS配置：CORS_ORIGINS
- 工作目录管理方法

### 数据模型文件

**文件：** `/backend/models/__init__.py` (18行)
- SQLAlchemy数据库初始化

**文件：** `/backend/models/script.py` (65行)
- Script 模型：脚本表（id, name, type, code, dependencies, version, created_at, updated_at）
- ScriptVersion 模型：版本表（id, script_id, version, code, dependencies, description, created_at）
- to_dict() 方法用于JSON序列化

**文件：** `/backend/models/execution.py` (38行)
- Execution 模型：执行记录表（id, script_id, status, params, output, error, log_file, start_time, end_time, created_at）
- 状态枚举：pending, running, success, failed

**文件：** `/backend/models/schedule.py` (40行)
- Schedule 模型：定时任务表（id, script_id, name, cron, params, enabled, last_run, next_run, created_at, updated_at）

### API路由文件

**文件：** `/backend/api/__init__.py` (216行)
- API蓝图定义
- 没有具体内容示例提供，但应包含蓝图初始化

**文件：** `/backend/api/scripts.py` (239行)
- GET /scripts - 获取脚本列表
- GET /scripts/<id> - 获取脚本详情
- POST /scripts - 创建脚本（验证名称唯一性，创建ScriptVersion）
- PUT /scripts/<id> - 更新脚本（检测代码变化，自动创建新版本）
- DELETE /scripts/<id> - 删除脚本及其工作目录
- GET /scripts/<id>/versions - 获取版本列表
- GET /scripts/<id>/versions/<version_id> - 获取指定版本
- POST /scripts/<id>/rollback/<version_num> - 版本回滚

**文件：** `/backend/api/executions.py` (384行)
- POST /scripts/<id>/execute - 执行脚本（支持文件上传）
- GET /executions - 获取执行历史（分页）
- GET /executions/<id> - 获取执行详情
- GET /executions/<id>/logs - 获取执行日志
- GET /executions/<id>/logs/stream - 实时日志流（SSE）
- DELETE /executions/<id> - 删除执行记录
- GET /executions/<id>/files - 获取执行空间的文件列表
- GET /executions/<id>/files/<path> - 获取执行空间的文件内容（预览/下载）
- 辅助函数：is_text_file() 判断文本文件

**文件：** `/backend/api/schedules.py` (超过100行)
- GET /schedules - 获取任务列表
- GET /schedules/<id> - 获取任务详情
- POST /schedules - 创建任务
- PUT /schedules/<id> - 更新任务
- DELETE /schedules/<id> - 删除任务
- POST /schedules/<id>/toggle - 启用/禁用任务
- （还有其他操作）

**文件：** `/backend/api/files.py` (100+行)
- GET /files - 获取文件列表
- POST /files/upload - 上传文件
- GET /files/download - 下载文件
- DELETE /files/delete - 删除文件
- 路径安全检查（防止目录遍历攻击）

### 服务层文件

**文件：** `/backend/services/__init__.py` (156行)
- 可能包含服务初始化

**文件：** `/backend/services/executor.py` (197行)
- execute_script(execution_id) - 脚本执行引擎
  - 状态管理：pending → running → success/failed
  - 参数解析和文件处理
  - 执行空间管理
  - 依赖安装
  - 子进程执行（Python/JavaScript）
  - 日志写入
  - 超时控制
- install_dependencies_python() - Python依赖安装
- install_dependencies_node() - Node.js依赖安装

**文件：** `/backend/services/scheduler.py` (超过100行)
- APScheduler集成
- 定时任务管理
- Cron表达式解析

---

## 前端文件索引

### 入口文件

**文件：** `/frontend/src/main.js` (446字)
- Vue应用初始化
- 插件注册（Element Plus等）
- 路由挂载
- 应用挂载到DOM

**文件：** `/frontend/src/App.vue` (1784字)
- 根组件
- 导航栏/菜单
- 路由视图占位符
- 全局样式

### 路由配置

**文件：** `/frontend/src/router/index.js`
- 路由定义
- 路由：/, /executions, /schedules, /files

### API服务层

**文件：** `/frontend/src/api/request.js` (686字)
- Axios实例配置
- 请求拦截器（添加API前缀）
- 响应拦截器

**文件：** `/frontend/src/api/index.js` (39行，2162字)
- 脚本管理API：getScripts, createScript, updateScript, deleteScript, getScriptVersions, rollbackScript, executeScript, executeScriptWithFiles
- 执行历史API：getExecutions, getExecution, getExecutionLogs, deleteExecution
- 定时任务API：getSchedules, createSchedule, updateSchedule, deleteSchedule, toggleSchedule, runScheduleNow
- 文件管理API：getFiles, uploadFile, downloadFile, deleteFile, createFolder

### 视图组件（页面）

**文件：** `/frontend/src/views/Scripts.vue` (525行，13886字)
- 脚本列表表格
- 创建/编辑对话框
  - 脚本名称输入
  - 脚本类型选择（Python/JavaScript）
  - 描述文本区
  - 依赖配置文本区
  - 代码编辑器（CodeEditor组件）
- 执行对话框
  - 文件上传（FileUpload组件）
  - 参数输入（JSON格式）
- 实时日志对话框
  - SSE连接获取日志
  - 实时显示和自动滚动
  - 执行状态显示
- 版本历史对话框
  - 版本列表
  - 版本查看和代码预览
  - 版本回滚功能

**文件：** `/frontend/src/views/Executions.vue` (7080字)
- 执行历史列表（分页）
- 日志查看对话框
- 执行文件查看（ExecutionFiles组件）
- 执行删除功能

**文件：** `/frontend/src/views/Schedules.vue` (6597字)
- 定时任务列表
- 任务创建/编辑对话框
- Cron表达式输入
- 任务启用/禁用
- 立即运行功能

**文件：** `/frontend/src/views/Files.vue` (12544字，6470字示例)
- 文件列表浏览
- 文件上传
- 文件夹创建
- 文件删除
- 面包屑导航

### 组件（可复用组件）

**文件：** `/frontend/src/components/CodeEditor.vue` (249行，5071字)
- CodeMirror集成
- 语言支持：Python, JavaScript
- 主题：light, dark
- 只读模式
- Props：modelValue, language, readonly, height, theme
- 暴露方法：focus(), getValue(), setValue()
- 样式自定义

**文件：** `/frontend/src/components/FileUpload.vue` (218行，4407字)
- 拖拽和点击上传
- 多文件支持
- 文件列表显示
- 文件删除
- 文件大小格式化
- Props：modelValue
- 事件：update:modelValue

**文件：** `/frontend/src/components/ExecutionFiles.vue` (6470字)
- 执行空间文件列表
- 文本文件预览
- 文件下载
- 文件删除
- 递归显示子文件夹

### 构建配置

**文件：** `/frontend/package.json`
- 依赖：vue, vue-router, axios, element-plus, @codemirror/*
- 脚本：npm run dev, npm run build

---

## 数据库文件

**位置：** `/data/database.db`
- SQLite数据库文件
- 包含表：scripts, script_versions, executions, schedules

---

## 日志和运行时文件

**目录：** `/logs/`
- execution_1.log
- execution_2.log
- ...
- 存储每次脚本执行的完整输出

**目录：** `/execution_spaces/`
- execution_1/
  - script_1.py (临时脚本文件)
  - input.csv (上传的文件)
  - output.txt (脚本生成的文件)
- execution_2/
- ...

**目录：** `/data/uploads/`
- 通过文件管理API上传的文件

---

## 配置和启动文件

**文件：** `/requirements.txt`
- Python依赖列表

**文件：** `/start-backend.sh` (694字)
- 启动后端脚本（Linux/Mac）

**文件：** `/start-backend.bat` (703字)
- 启动后端脚本（Windows）

**文件：** `/start-frontend.sh` (679字)
- 启动前端脚本（Linux/Mac）

**文件：** `/start-frontend.bat` (696字)
- 启动前端脚本（Windows）

---

## 文档文件

**文件：** `/README.md`
- 项目简介
- 技术栈
- 核心功能
- 目录结构
- 快速开始
- API文档
- 数据库模型

**文件：** `/USAGE.md` (5700字)
- 使用指南

**文件：** `/CODE_EDITOR_GUIDE.md` (5289字)
- 代码编辑器使用指南

**文件：** `/FILE_UPLOAD_GUIDE.md` (6168字)
- 文件上传指南

**文件：** `/WORKSPACE_GUIDE.md` (9874字)
- 工作空间指南

**文件：** `/PROJECT_ANALYSIS.md` (本次生成)
- 详细代码结构分析

**文件：** `/QUICK_REFERENCE.md` (本次生成)
- 快速参考指南

---

## 文件关系图

```
前端页面 (Views)
├── Scripts.vue
│   └── 依赖组件
│       ├── CodeEditor.vue
│       ├── FileUpload.vue
│       └── ExecutionFiles.vue
├── Executions.vue
│   └── 依赖组件
│       └── ExecutionFiles.vue
├── Schedules.vue
└── Files.vue

前端API (api/index.js)
└── 依赖服务
    └── request.js (Axios)
        ↓
        后端 API 端点

后端路由 (api/)
├── scripts.py
├── executions.py
├── schedules.py
└── files.py
    ↓
    (使用) 数据模型 (models/)
    ├── script.py
    ├── execution.py
    └── schedule.py
    ↓
    (调用) 服务层 (services/)
    ├── executor.py
    └── scheduler.py
    ↓
    配置 (config.py)
```

---

## 代码量统计

| 模块 | 文件数 | 行数 | 主要功能 |
|------|--------|------|---------|
| 后端模型 | 3 | ~150 | 数据定义 |
| 后端API | 4 | ~1000 | REST接口 |
| 后端服务 | 2 | ~300 | 业务逻辑 |
| 前端页面 | 4 | ~35000 | UI视图 |
| 前端组件 | 3 | ~10000 | 可复用UI |
| 前端API | 1 | ~50 | 接口封装 |

---

## 关键代码片段位置速查

| 功能 | 文件 | 行数 |
|------|------|------|
| 脚本创建 | `/backend/api/scripts.py` | 40-93 |
| 脚本编辑 | `/backend/api/scripts.py` | 95-145 |
| 脚本执行 | `/backend/api/executions.py` | 15-84 |
| 执行引擎 | `/backend/services/executor.py` | 14-164 |
| 实时日志SSE | `/backend/api/executions.py` | 160-216 |
| 执行表单 | `/frontend/src/views/Scripts.vue` | 84-108 |
| 日志窗口 | `/frontend/src/views/Scripts.vue` | 110-147 |
| 文件上传 | `/frontend/src/components/FileUpload.vue` | 全文 |
| 代码编辑 | `/frontend/src/components/CodeEditor.vue` | 全文 |
