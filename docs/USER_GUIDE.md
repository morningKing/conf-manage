# 使用指南（重构后）

> 本文档对应重构后的当前版本：专业后台主题（真实深色模式）、紧凑密度、MCP 服务、双层 E2E 测试。
> 架构与开发约定见 `CLAUDE.md`；存量数据升级见 `docs/DATA_MIGRATION.md`。

## 1. 环境要求

| 组件 | 版本/说明 |
|---|---|
| Python | 3.12+（开发环境实测） |
| Node.js | 18+ |
| PostgreSQL | 13+（需可用业务库） |
| pg_dump | 可选——备份页的"数据库导出"功能需要 |

## 2. 首次部署

```bash
# 1) 配置环境变量（数据库密码、SECRET_KEY 必填）
cp .env.example .env

# 2) 后端依赖
pip install -r requirements.txt

# 3) 建库 + 迁移（自动建表/列/索引）
CREATE DATABASE confmanage;            # 任意 SQL 客户端
cd backend && python -m alembic upgrade head

# 4) 启动
python app.py                          # 后端 0.0.0.0:5001

# 5) 前端
cd frontend && npm install && npm run dev   # http://localhost:5177
```

生产环境：`SECRET_KEY` 必须更换、`HOST_DEBUG=false`、参见 `docs/NGINX_DEPLOYMENT.md`。

### 启动方式

**一键启动（推荐）**：

```bash
python start.py                 # .env 加载 → PG/端口预检 → Alembic 迁移 → 双端并行启动
python start.py --skip-migrate  # 跳过迁移
```

- 前端 http://localhost:5177，后端健康检查 http://localhost:5001/health
- Ctrl+C 或任一服务退出即整体停止（含 vite 进程）
- 依赖检查：Python 依赖缺失 / 前端 node_modules 缺失会给出明确安装指引
- 前端代理目标自动指向 `HOST_PORT`（后端端口非 5001 也无需改配置）

手动分步启动（等价）：`cd backend && python -m alembic upgrade head && python app.py` +
`cd frontend && npm install && npm run dev`。根目录 `start-backend.*` / `start-frontend.*`
为旧的两个终端各跑一个的方式，仍可用但不再推荐。

## 3. 界面导览（侧边栏 12 页）

| 分组 | 页面 | 说明 |
|---|---|---|
| 主业务 | 脚本管理 / 执行记录 / 定时任务 / 工作流 | 核心 CRUD 与执行链路 |
| 资源 | 文件管理 / 环境配置 / 全局变量 / 标签管理 | 上传文件、Python/Node 解释器、脚本参数来源、脚本分组 |
| 运维 | Webhook / 备份管理 / 系统设置 | 触发器、pg_dump 备份、AI 配置 + 清理策略 |

- **主题切换**：侧边栏底部 ☀/🌙 按钮，或 `Ctrl+D`——真实生效（Element Plus 官方深色机制），localStorage 持久化
- **使用指南**：侧边栏底部 ？ 或 `Ctrl+K`（脚本参数示例、工作流空间说明、Cron 语法、故障排查）
- **快捷键**：`Ctrl+1~4` 直达脚本/执行/定时/文件；`Ctrl+F11` 全屏；完整列表在 Ctrl+K 弹窗

## 4. 核心功能用法

### 4.1 脚本管理

- 新建脚本三步：基础信息（名称/类型）→ 输入信息（参数定义）→ 脚本（代码必填，空代码无法保存）
- 列表为紧凑列表：**双击文件夹**进入、**右键**卡片/行打开操作菜单（执行/编辑/查看/白名单/删除）、脚本可**拖拽入文件夹**
- ⭐ 白名单（preserve）：加入后其执行记录不会被自动清理

**参数定义 JSON 结构**（"输入信息"Tab）：

```json
[
  {"key": "TARGET", "type": "text", "required": true,
   "validation": {"min_length": 1, "max_length": 64}},
  {"key": "LEVEL", "type": "select",
   "options": [{"value": "info", "label": "信息"}, {"value": "debug", "label": "调试"}]},
  {"key": "TAGS", "type": "multiselect",
   "options": [{"value": "a", "label": "A"}, {"value": "b", "label": "B"}]},
  {"key": "RETRY", "type": "number", "validation": {"min_value": 0, "max_value": 10}},
  {"key": "INPUT", "type": "file"}
]
```

脚本内读取方式：所有参数按**环境变量**注入（执行参数 > 全局变量），`process.env.TARGET` / `os.environ['TARGET']`。

### 4.2 执行

- 每次执行有**独立执行空间** `execution_spaces/execution_<id>/`，上传文件与输出文件都在其中
- 上传文件的文件名清单通过 `FILES` 环境变量（JSON 数组）提供
- 执行记录页：日志（SSE 实时）/ 文件 / 中断 / 重新执行 / 批量删除与取消
- 全局变量页配置的变量会注入所有执行（同名时被执行参数覆盖）

### 4.3 工作流（管道化）

工作流采用**线性管道**模型：按顺序编排步骤，前一步产生的文件可供后续步骤读取。

- **编排**：创建工作流 → 按序添加"脚本步骤"（选择脚本 + 可选步骤独立参数 JSON）或"延时步骤"；支持上移/下移/删除
- **参数优先级**：步骤级参数 > 管道级参数（执行时填写的）> 全局变量
- **数据传递**：所有步骤在同一个共享工作流空间执行，脚本通过 `WORKFLOW_SPACE` 环境变量定位该目录，用文件在步骤间传递数据（例：步骤 1 写 `result.json`，步骤 2 读取处理）
- **执行语义**：顺序执行、失败即停；执行面板实时显示每步状态与耗时，支持取消（同时终止运行中的脚本进程，剩余步骤标记 skipped）
- **旧 DAG 兼容**：历史画布工作流编辑时按节点序号拍平为线性步骤，条件边丢弃并提示；既有数据与执行能力不受影响
- **MCP**：`list_pipelines` / `get_pipeline` / `run_workflow`（见第 5 节）

### 4.4 Webhook

- `POST /api/webhook/<webhook_key>`，开启 Token 时需 `Authorization: Bearer <token>`
- 完整请求体写入执行空间的 `webhook_request.json`，脚本可直接读取
- 支持同步/异步两种模式；调用日志在详情页

### 4.5 Excel

- **执行空间文件预览**（Univer）：执行记录 → 文件 → Excel 预览弹窗
- **独立编辑页**（Luckysheet + 协同）：文件管理页发起，新窗口 `/excel-editor`

### 4.6 备份与清理

- 备份管理：系统备份（tar 包 + pg_dump 快照）、数据库导出、下载/删除、按天清理
- 清理策略在"系统设置"：阈值（50–10000，仅运行时生效）；白名单对象不参与清理

### 4.7 AI 配置

- 系统设置 → AI 配置：OpenAI 兼容接口；`api_key` 界面只显示尾 4 位掩码，编辑时留空即不修改
- 安全边界：默认允许私网地址（本地 Ollama 场景）；加固部署设 `ALLOW_PRIVATE_API_TARGETS=false`

## 5. MCP 服务（AI 客户端接入）

把脚本/工作流执行能力暴露为 MCP 工具，供 Claude Desktop、Cursor 等使用：

```bash
cd backend
python mcp_server.py                       # Streamable HTTP，默认 127.0.0.1:8808
python mcp_server.py --transport stdio     # 本地客户端直连
```

- 鉴权：`MCP_TOKEN` 设置后 http 模式要求 Bearer；端口 `MCP_PORT` 可配
- 自动加载根目录 `.env`；进程内已清空定时任务（不会与主服务重复触发）
- 工具：`list_scripts` / `get_script` / `run_script` / `wait_execution` / `get_execution` / `list_executions` / `cancel_execution` / **`list_pipelines` / `get_pipeline`** / `run_workflow`（执行管道）/ `wait_workflow_execution`

Claude Desktop 配置示例：

```json
{
  "mcpServers": {
    "script-tool-manager": {
      "command": "python",
      "args": ["E:/path/to/conf-manage/backend/mcp_server.py", "--transport", "stdio"]
    }
  }
}
```

## 6. 测试与工具链

```bash
# 后端
cd backend
python -m pytest tests/ -q        # 冒烟测试（SQLite 内存，无需 PG）
python -m pytest tests_e2e -q     # API E2E（真实服务 5101 + 独立库 confmanage_e2e）
python -m ruff check .            # lint

# 前端
cd frontend
npm run lint                      # ESLint
npm run build                     # 构建
npm run test:e2e                  # Playwright 浏览器 E2E（23 用例，自动拉起双服务）
```

E2E 注意事项：5101 端口被残留进程占用时测试会明确报错（Windows `SO_REUSEADDR` 会静默堆叠僵尸进程），按提示 `netstat -ano | findstr :5101` 清理。

## 7. 常见问题

| 现象 | 处理 |
|---|---|
| 前端页面空白/接口 404 | 后端未启动或端口不是 5001；vite 代理目标可用 `VITE_PROXY_TARGET` 覆盖 |
| 保存脚本提示"脚本代码不能为空" | 设计如此——切到"脚本"Tab 输入代码 |
| ExcelEditor 变量告警/样式异常 | 已随重构迁移到 EP 变量；如仍见旧样式请强刷（Ctrl+F5） |
| 帮助内容在哪 | 侧边栏 ？ 按钮 / `Ctrl+K`（HelpDialog 组件，内容与业务示例齐全） |
| 深色模式某页面局部仍是浅色 | 逐页截图验收已覆盖主要页面；如发现遗漏请报告页面名 |

## 8. 重构后有哪些变化（老用户速览）

- 侧边栏新增：**全局变量 / 标签管理 / 备份管理**（此前只能 URL 直达）
- 脚本管理：磁贴网格 → 紧凑列表；保存必填代码
- **工作流：画布 DAG 编辑器 → 线性管道步骤列表**（步骤独立参数、顺序执行、失败即停、可取消）
- 执行记录：列宽重排不再横向溢出；操作列紧凑
- 主题切换真实生效；全局密度收紧（一屏可见行数明显增加）
- 教程从首页弹窗移至 `Ctrl+K` 帮助；删除了无效的 300ms 假加载
- 界面文案与交互逻辑（按钮文字、占位符、右键菜单）均未变化，E2E 23 用例保障核心流程
