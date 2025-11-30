# 脚本工具管理系统

## 系统简介

这是一个基于Vue3 + Flask的脚本工具管理系统,支持Python和JavaScript脚本的管理、执行、定时调度和版本管理。

## 技术栈

### 前端
- Vue 3
- Vue Router
- Axios
- Element Plus (UI组件库)
- CodeMirror (代码编辑器)

### 后端
- Flask
- SQLAlchemy (ORM)
- APScheduler (定时任务)
- SQLite (数据库)

## 核心功能

1. **脚本管理**
   - 脚本的增删改查
   - 支持Python和JavaScript脚本
   - 脚本版本管理
   - 脚本依赖管理

2. **脚本执行**
   - 手动执行脚本
   - 参数输入支持
   - 实时日志输出
   - 执行历史记录

3. **定时任务**
   - 定时任务配置
   - Cron表达式支持
   - 任务启用/禁用
   - 执行日志查看

4. **文件处理**
   - 文件上传下载
   - 脚本读写文件
   - 文件列表管理

## 目录结构

```
.
├── backend/              # 后端服务
│   ├── app.py           # Flask应用入口
│   ├── config.py        # 配置文件
│   ├── models/          # 数据模型
│   ├── api/             # API路由
│   ├── services/        # 业务逻辑层
│   ├── executor/        # 脚本执行引擎
│   ├── scheduler/       # 定时任务调度
│   └── utils/           # 工具函数
├── frontend/            # 前端应用
│   ├── src/
│   │   ├── components/  # Vue组件
│   │   ├── views/       # 页面视图
│   │   ├── api/         # API接口
│   │   ├── router/      # 路由配置
│   │   └── App.vue      # 根组件
│   └── package.json
├── scripts/             # 脚本存储目录
├── logs/                # 执行日志目录
├── data/                # 数据文件目录
└── requirements.txt     # Python依赖

```

## 快速开始

### 后端启动

```bash
# 安装Python依赖
pip install -r requirements.txt

# 启动后端服务
python backend/app.py
```

后端服务将运行在 http://localhost:5000

### 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端应用将运行在 http://localhost:5173

## API文档

### 脚本管理

- `GET /api/scripts` - 获取脚本列表
- `GET /api/scripts/<id>` - 获取脚本详情
- `POST /api/scripts` - 创建脚本
- `PUT /api/scripts/<id>` - 更新脚本
- `DELETE /api/scripts/<id>` - 删除脚本
- `GET /api/scripts/<id>/versions` - 获取脚本版本列表

### 脚本执行

- `POST /api/scripts/<id>/execute` - 执行脚本
- `GET /api/executions` - 获取执行历史
- `GET /api/executions/<id>` - 获取执行详情
- `GET /api/executions/<id>/logs` - 获取执行日志

### 定时任务

- `GET /api/schedules` - 获取定时任务列表
- `POST /api/schedules` - 创建定时任务
- `PUT /api/schedules/<id>` - 更新定时任务
- `DELETE /api/schedules/<id>` - 删除定时任务
- `POST /api/schedules/<id>/toggle` - 启用/禁用任务

### 文件管理

- `GET /api/files` - 获取文件列表
- `POST /api/files/upload` - 上传文件
- `GET /api/files/<path>` - 下载文件
- `DELETE /api/files/<path>` - 删除文件

## 数据库模型

### Script (脚本表)
- id: 主键
- name: 脚本名称
- type: 脚本类型 (python/javascript)
- code: 脚本代码
- dependencies: 依赖配置
- version: 当前版本号
- created_at: 创建时间
- updated_at: 更新时间

### ScriptVersion (脚本版本表)
- id: 主键
- script_id: 脚本ID
- version: 版本号
- code: 代码内容
- dependencies: 依赖配置
- created_at: 创建时间

### Execution (执行记录表)
- id: 主键
- script_id: 脚本ID
- status: 执行状态
- params: 执行参数
- start_time: 开始时间
- end_time: 结束时间
- log_file: 日志文件路径

### Schedule (定时任务表)
- id: 主键
- script_id: 脚本ID
- name: 任务名称
- cron: Cron表达式
- params: 执行参数
- enabled: 是否启用
- created_at: 创建时间

## 许可证

MIT
