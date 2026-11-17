# 脚本工具管理系统

基于 Vue 3 + Flask 的脚本工具管理系统：Python / JavaScript 脚本的管理、执行、定时调度、工作流编排、Webhook 触发与 AI 辅助编写。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Flask 3 + Flask-SQLAlchemy 3 + PostgreSQL + APScheduler + Flask-SocketIO |
| 前端 | Vue 3 + Element Plus + CodeMirror 6 + Vue Flow + Univer（弹窗预览）/ Luckysheet（独立编辑页） |
| 构建 | Vite 5（前端 dev 端口 5177，`/api` 代理到 5001） |

## 快速开始

```bash
# 1. 准备 PostgreSQL（默认库 confmanage / 用户 postgres）
cp .env.example .env   # 修改 DB_PASSWORD、SECRET_KEY 等

# 2. 后端（端口 5001）
cd backend
pip install -r ../requirements.txt
python app.py

# 3. 前端
cd frontend
npm install
npm run dev
```

### 数据库迁移（Alembic）

```bash
cd backend
python -m alembic upgrade head          # 新库建表 / 存量库补列补索引
python -m alembic stamp 0001_baseline   # 已由 db.create_all() 建过表的存量库先盖章再 upgrade
```

### 工具链

```bash
cd backend && python -m pytest tests/ -q    # 冒烟测试（SQLite 内存库，无需 PG）
python -m ruff check .                      # 后端 lint
cd ../frontend && npm run lint              # 前端 lint
npm run build                               # 前端构建
```

## 环境变量

见 [.env.example](.env.example)：数据库连接（或整串 `DATABASE_URL`）、`SECRET_KEY`、监听 `HOST_BIND/HOST_PORT/HOST_DEBUG`、`CORS_ORIGINS`、`ALLOW_PRIVATE_API_TARGETS`（AI 接口私网边界，默认允许以兼容本地大模型，加固部署设 false）。

## 目录结构

```
backend/
  api/          # 路由层（errors.py 统一错误处理）
  services/     # 业务服务：executor / execution_service / cleanup_service /
                # backup_service / scheduler / workflow_executor / webhook_executor
  models/       # SQLAlchemy 模型
  migrations/   # Alembic 迁移（0001 基线 / 0002 preserve 列 / 0003 索引）
  utils/        # 纯工具：safe_io / http_utils / expr_eval / file_utils / excel_converter
  websocket/    # Excel 协同 SocketIO
  tests/        # pytest 冒烟测试
frontend/src/
  views/        # 13 个页面
  components/   # 通用组件（含 workflow-nodes）
  api/          # 统一 API 层（request.js 拦截器 + 按域模块）
  composables/  # useEventSource 等
docs/           # Nginx 部署指南 + archive/（历史过程文档）
```

## 核心功能

1. **脚本管理**：CRUD、版本与回滚、收藏、文件夹/标签、依赖管理
2. **脚本执行**：独立执行空间（每次执行隔离目录）、实时日志 SSE、参数注入（环境变量）、执行环境管理
3. **定时任务**：APScheduler Cron、清理白名单（script/schedule.preserve）
4. **工作流**：DAG 编辑器、条件分支（AST 白名单表达式求值）、节点级日志与状态流
5. **Webhook**：Token 校验（恒定时间比较）、同步/异步触发、调用日志
6. **Excel**：执行空间文件预览（Univer）与独立编辑页（Luckysheet + socket.io 协同）
7. **备份**：pg_dump 数据库导出 + 文件系统 tar 包
8. **系统设置**：AI 配置（api_key 掩码存储显示）、清理策略

## 部署

Nginx 反代部署见 [docs/NGINX_DEPLOYMENT.md](docs/NGINX_DEPLOYMENT.md)。生产环境注意：`SECRET_KEY` 必须更换、`HOST_DEBUG=false`、数据库密码不使用默认值。
