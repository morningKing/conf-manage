# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

脚本工具管理系统 (Script Tool Management System) - A Vue 3 + Flask full-stack application for managing, executing, and scheduling Python/JavaScript scripts. Supports script versioning, workflow orchestration (DAG), scheduled tasks (cron), webhook triggers, and AI-assisted script writing.

## Development Commands

### Backend (Flask on port 5000)
```bash
pip install -r requirements.txt
python backend/app.py
```

### Frontend (Vue 3 + Vite on port 5173)
```bash
cd frontend
npm install
npm run dev      # Development
npm run build    # Production build
```

No automated tests are currently configured. Testing is listed as a TODO item.

## Architecture

### Backend Structure
- `backend/app.py` - Flask entry point, registers API blueprint
- `backend/api/` - Route handlers (16 files), all use `api_bp` blueprint
- `backend/models/` - SQLAlchemy ORM models (11 files)
- `backend/services/` - Business logic: `executor.py` (script execution), `scheduler.py` (APScheduler), `workflow_executor.py`, `webhook_executor.py`
- `backend/config.py` - Centralized configuration (paths, timeouts, CORS)

### Frontend Structure
- `frontend/src/views/` - 14 page components (Scripts, Executions, Schedules, Workflows, etc.)
- `frontend/src/components/` - Reusable components (CodeEditor with CodeMirror 6, WorkflowEditor with Vue Flow DAG)
- `frontend/src/api/index.js` - Centralized API client
- Vite proxy: `/api` → `http://localhost:5000`

### Key Data Models
- `Script` + `ScriptVersion` - Scripts with version history
- `Execution` - Execution records with status (pending/running/success/failed)
- `Schedule` - Cron-based scheduled tasks
- `Workflow` + `WorkflowNode` + `WorkflowEdge` - DAG workflow definitions

## Key Patterns

### API Response Format
All endpoints return JSON: `{code: 0/1, data: {}, message: ""}` where code=0 means success.

### Script Execution Flow
1. Create Execution record (pending status)
2. Create isolated execution space directory (`execution_spaces/execution_{id}/`)
3. Write script file and uploaded files to execution space
4. Install dependencies (pip/npm)
5. Execute: Python uses CLI args `--key value`, JavaScript uses env vars `PARAM_KEY=value`
6. Stream logs via SSE at `/api/executions/<id>/logs/stream`
7. Update status to success/failed

### Version Control Triggers
New version created when: script code changes, dependencies change. No new version for name/description changes.

### Real-time Communication
SSE (Server-Sent Events) for log streaming. Frontend connects to `/api/executions/<id>/logs/stream`.

## Configuration Reference

Key values in `backend/config.py`:
- `EXECUTION_TIMEOUT = 300` - Script timeout in seconds
- `MAX_CONTENT_LENGTH = 16MB` - Max upload size
- `PYTHON_EXECUTABLE = 'python3'`, `NODE_EXECUTABLE = 'node'`
- `CORS_ORIGINS` - Allowed frontend origins (multiple localhost ports)

## Database

SQLite at `data/database.db`. No migrations system - direct SQLAlchemy model creation. See `database_schema.sql` for schema reference.

## Documentation

Extensive Chinese documentation available: README.md (quick start), QUICK_REFERENCE.md (commands and troubleshooting), PROJECT_STRUCTURE.md (architecture), TODO.md (roadmap with 150+ items).

## Language

Code comments and documentation are primarily in Chinese. User-facing messages are in Chinese.