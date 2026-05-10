# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

脚本工具管理系统 (Script Tool Management System) - A Vue 3 + Flask full-stack application for managing, executing, and scheduling Python/JavaScript scripts. Supports script versioning, workflow orchestration (DAG), scheduled tasks (cron), webhook triggers, global variables, execution environments, and AI-assisted script writing.

## Development Commands

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
```

No automated tests are currently configured. Testing is listed as a TODO item.

## Architecture

### Backend Structure
- `backend/app.py` - Flask entry point with SocketIO, registers API blueprint
- `backend/api/` - Route handlers (16 files), all use `api_bp` blueprint
- `backend/models/` - SQLAlchemy ORM models (11 files)
- `backend/services/` - Business logic: `executor.py` (script execution), `scheduler.py` (APScheduler), `workflow_executor.py`, `webhook_executor.py`
- `backend/config.py` - Centralized configuration (paths, timeouts, CORS)
- `backend/websocket/` - SocketIO handlers for Excel collaboration

### Frontend Structure
- `frontend/src/views/` - 14 page components (Scripts, Executions, Schedules, Workflows, Webhooks, GlobalVariables, AISettings, etc.)
- `frontend/src/components/` - Reusable components (CodeEditor with CodeMirror 6, WorkflowEditor with Vue Flow DAG, ExcelEditor)
- `frontend/src/api/index.js` - Centralized API client
- `frontend/src/router/index.js` - Vue Router configuration
- Vite proxy: `/api` → `http://localhost:5001`

### Key Data Models
- `Script` + `ScriptVersion` - Scripts with version history, parameters, folder/tags
- `Execution` - Execution records with status, progress stages, environment selection
- `Schedule` - Cron-based scheduled tasks with whitelist support
- `Workflow` + `WorkflowNode` + `WorkflowEdge` - DAG workflow definitions
- `WorkflowExecution` + `WorkflowNodeExecution` - Workflow execution tracking
- `Webhook` + `WebhookTrigger` - External trigger integration
- `GlobalVariable` - Shared environment variables for all scripts
- `Environment` - Python/JavaScript interpreter configurations
- `Folder` - Script organization hierarchy

## Key Patterns

### API Response Format
All endpoints return JSON: `{code: 0/1, data: {}, message: ""}` where code=0 means success.

### Script Execution Flow
1. Create Execution record (pending status)
2. Create isolated execution space directory (`execution_spaces/execution_{id}/`)
3. Write script file and uploaded files to execution space
4. Install dependencies (pip/npm) if specified
5. Execute with environment variables: Python uses `-u` flag for unbuffered output, all params injected as env vars
6. Stream logs via SSE at `/api/executions/<id>/logs/stream`
7. Update status with progress stages: preparing → installing_deps → running → finishing → completed/failed

### Parameter Injection
Parameters are passed via environment variables:
- Script-defined parameters (JSON schema) → env vars
- Global variables → env vars (script params override)
- File uploads → `FILES` env var with JSON array of filenames
- Special types: `multiselect` → comma-separated, `switch` → 'true'/'false', `file` → file path

### Version Control Triggers
New version created when: script code changes, dependencies change. No new version for name/description changes.

### Real-time Communication
- SSE (Server-Sent Events) for log streaming at `/api/executions/<id>/logs/stream`
- SocketIO for Excel editor collaboration at `/excel`

## Configuration Reference

Key values in `backend/config.py`:
- `EXECUTION_TIMEOUT = 300` - Script timeout in seconds
- `MAX_CONTENT_LENGTH = 16MB` - Max upload size
- `PYTHON_EXECUTABLE = 'python'`, `NODE_EXECUTABLE = 'node'`
- `CORS_ORIGINS` - Allowed frontend origins (multiple localhost ports)
- `CLEANUP_THRESHOLD = 500` - Retain last N execution records during cleanup
- PostgreSQL connection via environment variables: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`

## Database

PostgreSQL (migrated from SQLite). No migrations system - direct SQLAlchemy model creation. Connection pool configured with `pool_size=10`, `max_overflow=20`.

## Documentation

Extensive Chinese documentation available: README.md (quick start), PROJECT_STRUCTURE.md (architecture), TODO.md (roadmap), QUICK_REFERENCE.md (commands).

## Language

Code comments and documentation are primarily in Chinese. User-facing messages are in Chinese.