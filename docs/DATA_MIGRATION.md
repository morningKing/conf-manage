# 数据迁移指南（重构后）

> 适用对象：**已有存量数据**的部署（PostgreSQL 中已有脚本/执行记录等业务数据），升级到本轮重构后的版本。
> 全新部署请直接看《使用指南》的"首次部署"章节，无需迁移。

## 一、本轮重构改了什么（与数据相关）

### 1. 引入 Alembic 迁移体系（替代 db.create_all）

此前建表依赖启动时的 `db.create_all()`——它**只为新库建表，永远不会给已存在的表加列/加索引**。重构后所有 schema 变更走 Alembic 迁移链：

| Revision | 内容 | 影响对象 |
|---|---|---|
| `0001_baseline` | 基线：按当前模型建全部表（对已存在的表是**空操作**） | 全部 20 张表 |
| `0002_add_preserve` | 幂等新增 `preserve`（清理白名单）列 | `scripts`、`schedules` |
| `0003_add_indexes` | 幂等新增热点列索引 | `executions(script_id/status/created_at)`、`webhook_logs(webhook_id/created_at)`、`workflow_node_executions(workflow_execution_id)` |

> **为什么存量库必须迁移**：`preserve` 列在重构前只存在于模型定义中。存量库未加列时，启动后"清理白名单"相关接口会直接报 `column "preserve" of relation "scripts" does not exist`。索引缺失则导致执行历史/清理等高频查询在大数据量下变慢。

### 2. 删除了 SQLite 时代的迁移脚本

`quick_migrate.sh`、`migrate_database.py` 等一批 SQLite→PG 时代的一次性脚本已删除（引用的文件不存在，脚本本身已损坏）。SQLite 数据的迁移属**更早期**的历史工作，如仍需处理请参考 `docs/archive/MIGRATION_GUIDE.md`（归档文档）。本轮重构**不涉及** SQLite。

### 3. 测试库与业务库完全隔离

E2E 测试使用独立数据库 `confmanage_e2e`（每轮测试自动重建），**绝不读写业务库 `confmanage`**。运行测试不会影响你的数据。

## 二、迁移步骤（存量 PostgreSQL 部署）

### 第 0 步：备份（强烈建议）

任选其一：

```bash
# 方式 A：系统备份界面（推荐）
# 前端 → 备份管理 → 创建系统备份（含 pg_dump 数据库导出 + 文件系统 tar 包）

# 方式 B：手动 pg_dump
pg_dump -h localhost -U postgres -d confmanage -F c -f backups/confmanage_before_migration.dump
```

### 第 1 步：停服

停止后端进程（避免迁移期间有写入）。

### 第 2 步：配置环境变量

```bash
# 方式 A：复制并编辑 .env（推荐）
cp .env.example .env   # 填入 DB_PASSWORD / SECRET_KEY 等

# 方式 B：直接在当前 shell 设置
# export DB_PASSWORD=... / DB_NAME=... / DATABASE_URL=...
```

### 第 3 步：执行迁移

```bash
cd backend
python -m alembic upgrade head
```

- `0001_baseline` 对已存在的表是空操作（`create_all` 自动跳过已存在的表），**不需要**先 `stamp`
- 如果之前已经手动执行过 `stamp 0001_baseline`，直接 `upgrade head` 同样正确
- 预期输出：依次执行 `0001_baseline -> 0002_add_preserve -> 0003_add_indexes`（已存在列/索引会自动跳过）

### 第 4 步：验证迁移结果

```bash
# 方式 A：用迁移工具核对（只读）
python migrations/postgres_migrations.py check --table scripts   # 应列出含 preserve 列
python migrations/postgres_migrations.py status                  # 表结构总览

# 方式 B：启动后端，通过界面验证
# 备份管理 → 刷新数据库信息；脚本管理页对脚本 ⭐ 切换白名单不报错
```

### 第 5 步：重启服务

```bash
python app.py    # 或 start-backend 脚本
```

## 三、全新部署（无存量数据）

```bash
# 1. 创建数据库（任意工具执行）
CREATE DATABASE confmanage;

# 2. 配置 .env 后执行迁移链（自动建全部表 + 列 + 索引）
cd backend && python -m alembic upgrade head

# 3. 启动
python app.py
```

## 四、回滚

```bash
# 用迁移前的备份恢复
pg_restore -h localhost -U postgres -d confmanage --clean backups/confmanage_before_migration.dump

# 或仅回退 schema（业务数据保留，但 preserve 列/索引会被删除——不建议）
cd backend && python -m alembic downgrade 0001_baseline
```

## 五、常见问题

| 现象 | 原因与处理 |
|---|---|
| 启动后脚本页报 `column preserve does not exist` | 未执行迁移：`alembic upgrade head` |
| `alembic` 报 `Can't locate revision` | `backend/migrations/versions/` 目录不完整，确认三个迁移文件都在 |
| 连不上数据库 | `.env` 未配置或 PostgreSQL 未启动；`config.py` 默认值仅为开发兜底 |
| 备份页"数据库导出失败" | 本机无 `pg_dump` 客户端；安装 PostgreSQL 客户端工具后重试（文件部分备份不受影响） |
| E2E 测试后业务数据"消失"了？ | 不会。测试只操作 `confmanage_e2e`；如连接到了业务库，是 `DATABASE_URL`/`DB_NAME` 配置错误，请检查 `.env` |
| `postgres_migrations.py` 与 Alembic 什么关系 | 两者都能加列（该脚本已做注入加固且幂等）。**以 Alembic 为准**，此脚本仅作为辅助核对工具（status/check 只读场景） |

## 六、本轮重构中修复的与数据相关的缺陷

- 备份/导出功能此前完全损坏（引用已删除的 `Config.DATABASE_PATH`）→ 已重写为 pg_dump + SQLAlchemy 反射
- 清理白名单（preserve）在存量库上不可用 → 0002 迁移补列
- 执行历史/统计在大数据量下无索引 → 0003 补索引
- `datetime.utcnow`（弃用 API）→ 全库 `datetime.now(timezone.utc)`
