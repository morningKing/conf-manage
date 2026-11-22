# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

脚本工具管理系统 (Script Tool Management System) - A Vue 3 + Flask full-stack application for managing, executing, and scheduling Python/JavaScript scripts. Supports script versioning, workflow orchestration (linear pipelines), scheduled tasks (cron), webhook triggers, global variables, execution environments, and AI-assisted script writing.

## Development Commands

### One-click dev stack
```bash
python start.py                 # loads .env, checks PG/ports, runs alembic upgrade,
                                # starts backend 5001 + frontend 5177 (Ctrl+C stops both)
python start.py --skip-migrate  # skip DB migrations
```

### Backend (Flask on port 5001)
```bash
pip install -r requirements.txt
python backend/app.py
```

### Frontend (Vue 3 + Vite on port 5177)
```bash
cd frontend
npm install
npm run dev      # Development
npm run build    # Production build
npm run lint     # ESLint
```

### Tests & Lint
```bash
cd backend
python -m pytest tests/ -q       # Smoke tests (SQLite in-memory, no PG dependency)
python -m pytest tests_e2e -q    # API E2E: real server subprocess on 5101 +
                                 # dedicated PG db confmanage_e2e (never the user DB;
                                 # dbsetup.py recreates it, SQLite fallback)
python -m ruff check .           # Backend lint (rules: F821/F811/E9, see backend/pyproject.toml)

cd frontend
npm run test:e2e                 # Playwright browser E2E (auto-starts backend+vite)
```

E2E infrastructure notes (backend/tests_e2e/):
- `dbsetup.py` must NOT import config at module load (env must be applied first)
- server output goes to a log FILE, never an unread PIPE (deadlock trap)
- port 5101 must be free; Windows SO_REUSEADDR lets zombie servers stack up
- dialogs: Element Plus el-select placeholder is NOT an input placeholder — click `.el-select`; ElMessageBox confirm buttons may be English OK/Cancel; script card actions live in the right-click context menu; new-script dialog requires typing code (backend rejects empty code)

## Architecture

### Backend Structure
- `backend/app.py` - Flask entry point (app factory `create_app`, logging setup, global error handlers)
- `backend/api/` - Route handlers (18 files), all use `api_bp` blueprint; `errors.py` provides `ApiError` + global JSON handlers (HTTPException → JSON, not swallowed into 500)
- `backend/services/` - Business logic: `executor.py` (script execution), `execution_service.py` (delete/kill/retry shared ops), `cleanup_service.py`, `backup_service.py`, `scheduler.py` (APScheduler), `workflow_executor.py`, `webhook_executor.py`
- `backend/models/` - SQLAlchemy ORM models; `tag.py` holds Tag/script_tags
- `backend/utils/` - Pure helpers only (no business logic): `safe_io.py` (containment-checked file IO — use it for all variable-path writes), `http_utils.py` (SSRF-boundary HTTP), `expr_eval.py` (AST-whitelist evaluator, no eval), `file_utils.py`, `excel_converter.py`
- `backend/migrations/` - Alembic (0001 baseline via metadata.create_all, 0002 preserve columns, 0003 hot-column indexes)
- `backend/config.py` - Centralized config; DB/SECRET_KEY/host/CORS from env vars (see `.env.example`)
- `backend/mcp_server.py` - MCP server exposing script/pipeline execution as tools
  (transports: streamable-http on MCP_PORT:8808 with optional MCP_TOKEN bearer auth,
  or stdio for local clients). Tools: script list/get/run, execution wait/get/list/cancel,
  `list_pipelines` / `get_pipeline` / `run_workflow` / `wait_workflow_execution`.
  Reuses the executor/service layer; clears APScheduler jobs in-process to avoid double
  cron; polls with `populate_existing=True` because long-lived sessions otherwise
  cache rows updated by worker threads.
- `backend/websocket/` - SocketIO handlers for Excel collaboration

### Frontend Structure
- `frontend/src/views/` - 13 page components
- `frontend/src/components/` - Reusable components (CodeEditor with CodeMirror 6, PipelineBuilder for workflow editing); Excel editing has two stacks: Univer (in ExecutionFiles dialog preview) and Luckysheet (standalone /excel-editor page with socket.io collab) — both intentional, see README
- `frontend/src/utils/pipeline.js` - steps ↔ backend `{nodes, edges}` conversion layer (toGraph generates chain edges; fromGraph flattens legacy DAGs by node order and reports dropped condition edges; validateSteps)
- `frontend/src/api/` - `request.js` (axios instance, interceptor unwraps `response.data`, pops ElMessage on error) + per-domain modules; workflow endpoints live in `workflow.js` and are re-exported from `index.js`
- `frontend/src/composables/useEventSource.js` - SSE lifecycle helper (used by log streams in Scripts.vue and Workflows.vue)
- `frontend/src/router/index.js` - Vue Router configuration; Vite proxy `/api` → `http://localhost:5001`

### Key Data Models
- `Script` + `ScriptVersion` (+ `preserve` cleanup-whitelist flag), `Execution`, `Schedule`, `Workflow` + `WorkflowNode` + `WorkflowEdge`, `WorkflowExecution` + `WorkflowNodeExecution`, `Webhook`/`WebhookLog`, `GlobalVariable`, `Environment`, `Folder`, `AIConfig` (api_key masked in `to_dict`)

## Key Patterns

### API Response Format
All endpoints return JSON: `{code: 0/1, data: {}, message: ""}` where code=0 means success. Routes re-raise `HTTPException` so `get_or_404` yields real 404s; unexpected exceptions fall through to the global handler.

### File/URL Safety
- Any variable-path file IO goes through `utils/safe_io.py` (`ensure_contained` / `safe_write_text` / `safe_open`) — realpath containment against a required `base_dir`
- Outbound HTTP to user-configurable URLs goes through `utils/http_utils.safe_post_json` (scheme whitelist + resolved-IP boundary + no redirects; `ALLOW_PRIVATE_API_TARGETS` env relaxes for local LLMs — note this machine's DNS is Fake-IP mode so the default must stay permissive)
- Workflow condition expressions use `utils/expr_eval.safe_eval` (never `eval`)

### Script Execution Flow
1. Create Execution record (pending status)
2. Create isolated execution space directory (`execution_spaces/execution_{id}/`)
3. Write script file and uploaded files to execution space
4. Install dependencies (pip/npm) if specified
5. Execute with environment variables: Python uses `-u` flag for unbuffered output; all params injected as env vars (`build_exec_env`)
6. Stream logs via SSE at `/api/executions/<id>/logs/stream`
7. Update status with progress stages: preparing → installing_deps → running → finishing → completed/failed

Threads started for background execution MUST wrap in `with app.app_context():` (see `_run_script_with_context` in api/executions.py). Note `execute_script` calls `db.session.remove()` — never touch ORM instances from the calling scope afterwards; use pre-captured ids.

### Parameter Injection
Parameters are passed via environment variables:
- Script-defined parameters (JSON schema, options as `[{value,label}]`) → env vars
- Global variables → env vars (script params override)
- File uploads → `FILES` env var with JSON array of filenames
- Special types: `multiselect` → comma-separated, `switch` → 'true'/'false', `file` → file path

### Workflow = Linear Pipeline
The workflow feature is a linear pipeline (backend keeps the generic DAG models; the
frontend edits ordered `steps` and converts via `utils/pipeline.js`):
- Steps run sequentially, fail-fast; data flows via files in the shared
  WORKFLOW_SPACE directory (env var available inside each step's script).
- Per-step params: `node config.params` merge over workflow-level params
  (step > workflow > global variables); WORKFLOW_SPACE always wins.
- Cancel is real: the cancel API kills the running step's script process; the
  executor checks `cancelled` at node boundaries, marks remaining node executions
  `skipped` and preserves the cancelled terminal state.
- Legacy DAGs opened in the editor flatten by node-id order (condition edges dropped
  with a warning); stored graphs still execute unchanged.

### Version Control Triggers
New version created when: script code changes, dependencies change. No new version for name/description changes.

### Real-time Communication
- SSE (Server-Sent Events) for log streaming at `/api/executions/<id>/logs/stream`
- SocketIO for Excel editor collaboration at `/excel`

## MCP

`python backend/mcp_server.py` (Streamable HTTP, default 127.0.0.1:8808, optional
`MCP_TOKEN` bearer auth) or `--transport stdio` for local clients (auto-loads root
`.env`). E2E coverage lives in `backend/tests_e2e/test_mcp.py` (runs the server as a
subprocess on port 5102 and drives it with the official client SDK; the tool-name
assertions there are a contract — extend, don't rename).

## Configuration Reference

Key values in `backend/config.py` (env-overridable where noted):
- `EXECUTION_TIMEOUT = 300` - Script timeout in seconds
- `MAX_CONTENT_LENGTH = 16MB` - Max upload size
- `PYTHON_EXECUTABLE = 'python'`, `NODE_EXECUTABLE = 'node'`
- `CORS_ORIGINS` - Allowed frontend origins (`CORS_ORIGINS` env, comma-separated)
- `CLEANUP_THRESHOLD = 500` - Retain last N execution records during cleanup
- `HOST_BIND/HOST_PORT/HOST_DEBUG` - server bind (env)
- `ALLOW_PRIVATE_API_TARGETS` - AI endpoint private-network boundary (default true)
- `MCP_HOST/MCP_PORT/MCP_TOKEN` - MCP server (env)
- PostgreSQL connection via `DATABASE_URL` or `DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME`

## Database

PostgreSQL (migrated from SQLite). Schema changes go through Alembic (`backend/migrations/versions/`); `db.create_all()` only helps fresh DBs — for existing tables always write a migration. Existing DBs created before Alembic: `python -m alembic stamp 0001_baseline` then `upgrade head`. Migration steps for operators: `docs/DATA_MIGRATION.md`. Connection pool configured with `pool_size=10`, `max_overflow=20`.

## Documentation

README.md (quick start, toolchain), docs/USER_GUIDE.md (post-refactor usage), docs/DATA_MIGRATION.md (schema upgrades), docs/NGINX_DEPLOYMENT.md (deployment), docs/archive/ (historical process docs). PROJECT_STRUCTURE.md may lag behind this file — trust CLAUDE.md first.

## Language

Code comments and documentation are primarily in Chinese. User-facing messages are in Chinese.
