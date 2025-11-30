# 脚本管理系统 - 项目结构说明

## 项目概述

这是一个基于 **Flask (后端) + Vue 3 (前端)** 的脚本管理和执行系统，支持 Python 和 JavaScript 脚本的管理、执行、版本控制和定时调度。

## 技术栈

### 后端
- **框架**: Flask 3.1.0
- **数据库**: SQLite + SQLAlchemy
- **任务调度**: APScheduler
- **CORS**: Flask-CORS

### 前端
- **框架**: Vue 3 (Composition API)
- **UI库**: Element Plus
- **构建工具**: Vite
- **代码编辑器**: CodeMirror 6
- **HTTP客户端**: Axios

## 目录结构

```
conf-manage/
├── backend/                    # 后端代码
│   ├── api/                   # API路由
│   │   ├── __init__.py       # API蓝图初始化
│   │   ├── executions.py     # 执行记录API
│   │   ├── schedules.py      # 定时任务API
│   │   └── scripts.py        # 脚本管理API
│   ├── models/               # 数据模型
│   │   ├── __init__.py       # 数据库初始化
│   │   ├── execution.py      # 执行记录模型
│   │   ├── schedule.py       # 定时任务模型
│   │   └── script.py         # 脚本模型
│   ├── services/             # 业务逻辑
│   │   ├── executor.py       # 脚本执行引擎
│   │   └── scheduler.py      # 定时任务调度器
│   ├── migrations/           # 数据库迁移脚本
│   │   └── add_parameters_field.py  # 参数字段迁移
│   ├── app.py               # Flask应用入口
│   └── config.py            # 配置文件
│
├── frontend/                  # 前端代码
│   ├── src/
│   │   ├── api/              # API请求封装
│   │   │   └── index.js      # API方法定义
│   │   ├── components/       # Vue组件
│   │   │   ├── CodeEditor.vue         # 代码编辑器
│   │   │   ├── ExecutionFiles.vue     # 执行文件列表
│   │   │   ├── ExecutionParams.vue    # 执行参数输入组件
│   │   │   ├── FileUpload.vue         # 文件上传组件
│   │   │   └── ParameterConfig.vue    # 参数配置组件
│   │   ├── views/            # 页面组件
│   │   │   ├── Executions.vue  # 执行历史页面
│   │   │   ├── Schedules.vue   # 定时任务页面
│   │   │   └── Scripts.vue     # 脚本管理页面
│   │   ├── App.vue           # 根组件
│   │   ├── main.js           # 应用入口
│   │   └── style.css         # 全局样式
│   ├── index.html            # HTML模板
│   ├── package.json          # 依赖配置
│   └── vite.config.js        # Vite配置
│
├── data/                      # 数据目录 (gitignore)
│   └── database.db           # SQLite数据库
├── logs/                      # 日志目录 (gitignore)
├── execution_spaces/          # 执行空间 (gitignore)
├── .gitignore                # Git忽略文件
└── 参数自定义功能说明.md      # 参数功能文档

```

## 核心功能模块

### 1. 脚本管理 (`backend/api/scripts.py` + `frontend/src/views/Scripts.vue`)

**功能**:
- 创建、编辑、删除脚本
- 支持 Python 和 JavaScript
- 依赖管理
- **参数配置** (新增)
- 版本控制和回滚

**数据模型** (`backend/models/script.py`):
```python
class Script:
    id, name, description, type, code
    dependencies      # 依赖配置 (JSON)
    parameters        # 参数定义 (JSON) - 新增
    version           # 版本号
    created_at, updated_at
```

**参数定义格式**:
```json
[
  {
    "key": "API_KEY",
    "description": "API密钥",
    "default_value": "",
    "required": true
  }
]
```

### 2. 脚本执行 (`backend/services/executor.py`)

**执行流程**:
1. 创建独立的执行空间 (`execution_spaces/execution_{id}/`)
2. 保存脚本文件到执行空间
3. 安装依赖（如有）
4. 通过**环境变量**传递参数
5. 执行脚本，实时记录日志
6. 保存执行结果

**参数传递方式**:
- Python: `os.getenv('PARAM_NAME')`
- JavaScript: `process.env.PARAM_NAME`

**执行记录** (`backend/models/execution.py`):
```python
class Execution:
    id, script_id, status
    params            # 执行参数 (JSON)
    output, error     # 输出和错误
    log_file          # 日志文件路径
    start_time, end_time
```

### 3. 定时任务 (`backend/services/scheduler.py`)

**调度器**: APScheduler (BackgroundScheduler)

**支持的 Cron 表达式**:
- 每分钟: `* * * * *`
- 每小时: `0 * * * *`
- 每天 2:00: `0 2 * * *`
- 每周一 9:00: `0 9 * * 1`

**数据模型** (`backend/models/schedule.py`):
```python
class Schedule:
    id, script_id, name
    cron_expression   # Cron表达式
    enabled           # 是否启用
    last_run_time, next_run_time
```

### 4. 实时日志 (`backend/api/executions.py`)

**技术**: Server-Sent Events (SSE)

**流程**:
1. 前端通过 `EventSource` 连接 `/api/executions/{id}/logs/stream`
2. 后端实时读取日志文件并推送
3. 执行完成后发送状态事件

### 5. 文件管理

**文件上传** (`frontend/src/components/FileUpload.vue`):
- 支持拖拽上传
- 多文件支持
- 文件预览

**文件存储**:
- 上传文件保存到执行空间
- 脚本可通过相对路径访问
- 执行完成后文件保留在执行空间，可查看/下载

## API 接口

### 脚本管理
```
GET    /api/scripts                    # 获取脚本列表
GET    /api/scripts/{id}               # 获取脚本详情
POST   /api/scripts                    # 创建脚本
PUT    /api/scripts/{id}               # 更新脚本
DELETE /api/scripts/{id}               # 删除脚本
GET    /api/scripts/{id}/versions      # 获取版本列表
POST   /api/scripts/{id}/rollback/{v}  # 回滚到指定版本
```

### 执行管理
```
POST   /api/scripts/{id}/execute       # 执行脚本
GET    /api/executions                 # 获取执行列表
GET    /api/executions/{id}            # 获取执行详情
GET    /api/executions/{id}/logs       # 获取日志
GET    /api/executions/{id}/logs/stream # 实时日志流 (SSE)
DELETE /api/executions/{id}            # 删除执行记录
GET    /api/executions/{id}/files      # 获取执行空间文件
GET    /api/executions/{id}/files/{path} # 下载/预览文件
```

### 定时任务
```
GET    /api/schedules                  # 获取任务列表
POST   /api/schedules                  # 创建任务
PUT    /api/schedules/{id}             # 更新任务
DELETE /api/schedules/{id}             # 删除任务
POST   /api/schedules/{id}/toggle      # 启用/禁用任务
```

## 配置说明 (`backend/config.py`)

```python
# 数据库
SQLALCHEMY_DATABASE_URI = 'sqlite:///data/database.db'

# 目录
EXECUTION_SPACES_DIR = 'execution_spaces/'  # 执行空间
LOGS_DIR = 'logs/'                          # 日志目录
DATA_DIR = 'data/'                          # 数据目录

# 执行器
PYTHON_EXECUTABLE = 'python3'
NODE_EXECUTABLE = 'node'
EXECUTION_TIMEOUT = 300  # 超时时间(秒)

# 跨域
CORS_ORIGINS = ['http://localhost:5173']
```

## 数据库表结构

### scripts (脚本表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | VARCHAR(100) | 脚本名称 (唯一) |
| description | TEXT | 描述 |
| type | VARCHAR(20) | 类型 (python/javascript) |
| code | TEXT | 脚本代码 |
| dependencies | TEXT | 依赖配置 (JSON) |
| **parameters** | TEXT | **参数定义 (JSON)** |
| version | INTEGER | 版本号 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### executions (执行记录表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| script_id | INTEGER | 脚本ID (外键) |
| status | VARCHAR(20) | 状态 (pending/running/success/failed) |
| params | TEXT | 执行参数 (JSON) |
| output | TEXT | 输出 |
| error | TEXT | 错误信息 |
| log_file | VARCHAR(500) | 日志文件路径 |
| start_time | DATETIME | 开始时间 |
| end_time | DATETIME | 结束时间 |
| created_at | DATETIME | 创建时间 |

### schedules (定时任务表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| script_id | INTEGER | 脚本ID (外键) |
| name | VARCHAR(100) | 任务名称 |
| cron_expression | VARCHAR(100) | Cron表达式 |
| enabled | BOOLEAN | 是否启用 |
| last_run_time | DATETIME | 上次运行时间 |
| next_run_time | DATETIME | 下次运行时间 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

## 启动方式

### 后端
```bash
cd backend
export PYTHONPATH=/path/to/conf-manage/backend:$PYTHONPATH
python3 app.py
```
访问: http://localhost:5000

### 前端
```bash
cd frontend
npm install
npm run dev
```
访问: http://localhost:5173

## 关键特性

### 1. 参数自定义功能 (新增)
- 创建脚本时配置参数
- 执行时动态生成输入表单
- 通过环境变量传递给脚本
- 支持默认值和必填验证

### 2. 独立执行空间
- 每次执行创建独立的工作目录
- 文件隔离，互不影响
- 执行完成后空间保留，可查看文件

### 3. 实时日志流
- Server-Sent Events 技术
- 浏览器实时显示执行日志
- 自动滚动到最新输出

### 4. 版本控制
- 代码修改自动创建新版本
- 支持查看历史版本
- 一键回滚到任意版本

### 5. 文件上传
- 拖拽上传
- 多文件支持
- 文件直接保存到执行空间

## 常见操作

### 创建带参数的脚本
1. 新建脚本，填写基本信息
2. 在"参数配置"区域添加参数
3. 在代码中使用 `os.getenv('PARAM_NAME')` 获取
4. 保存脚本

### 执行脚本
1. 点击"执行"按钮
2. 填写参数值
3. 上传所需文件（可选）
4. 点击"执行"，查看实时日志

### 设置定时任务
1. 进入"定时任务"页面
2. 新建任务，选择脚本
3. 填写 Cron 表达式
4. 启用任务

### 查看执行结果
1. 进入"执行历史"页面
2. 点击"查看日志"查看输出
3. 点击"执行空间"查看生成的文件
4. 下载或预览文件

## 数据库迁移

### 添加参数字段（已完成）
```bash
cd backend
python3 migrations/add_parameters_field.py migrate
```

### 回滚
```bash
python3 migrations/add_parameters_field.py rollback
```

## 开发注意事项

1. **后端修改**: 修改模型后需要手动创建迁移脚本
2. **前端开发**: 使用 Composition API，遵循 Vue 3 最佳实践
3. **API调用**: 统一使用 `src/api/index.js` 中的方法
4. **错误处理**: 后端返回统一格式 `{code: 0/1, data: {}, message: ""}`
5. **文件路径**: 执行空间中使用相对路径访问文件

## 扩展建议

1. **用户认证**: 添加用户登录和权限管理
2. **脚本分类**: 支持脚本分类和标签
3. **执行队列**: 支持并发控制和排队
4. **通知功能**: 执行完成后发送邮件/消息通知
5. **脚本市场**: 共享和导入脚本模板
6. **WebSocket**: 替代 SSE 实现双向通信
7. **Docker支持**: 在容器中隔离执行
8. **参数验证**: 添加参数类型和格式验证

## 故障排查

### 脚本执行失败
1. 检查日志文件内容
2. 验证依赖是否正确安装
3. 确认执行空间权限
4. 查看超时设置

### 实时日志不显示
1. 检查浏览器 SSE 支持
2. 确认后端日志文件已创建
3. 查看网络请求状态

### 定时任务未执行
1. 检查任务是否启用
2. 验证 Cron 表达式
3. 查看 APScheduler 日志

## 相关文档

- [参数自定义功能说明.md](./参数自定义功能说明.md) - 详细的参数功能使用指南
- Flask文档: https://flask.palletsprojects.com/
- Vue 3文档: https://vuejs.org/
- Element Plus: https://element-plus.org/
- APScheduler: https://apscheduler.readthedocs.io/
