# 数据库结构说明

## 概述

本系统使用 SQLite 数据库，包含 15 个主要数据表，涵盖脚本管理、执行控制、工作流引擎、AI功能等模块。

## 表结构概览

### 1. AI功能模块

#### ai_configs (AI配置表)
存储AI服务配置信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| provider | VARCHAR(50) | AI提供商 (openai/anthropic/custom) |
| api_key | VARCHAR(500) | API密钥 |
| base_url | VARCHAR(500) | API基础URL（可选） |
| model | VARCHAR(100) | 模型名称（如 gpt-4） |
| is_active | BOOLEAN | 是否激活 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**关键特性**：
- 支持多个AI配置，但同时只能激活一个
- 支持 OpenAI 兼容的所有 API

---

### 2. 脚本管理模块

#### scripts (脚本表)
存储脚本的基本信息和代码。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | VARCHAR(100) | 脚本名称（唯一） |
| description | TEXT | 脚本描述 |
| type | VARCHAR(20) | 脚本类型 (python/javascript/bash) |
| code | TEXT | 脚本代码 |
| dependencies | TEXT | 依赖包（JSON格式） |
| parameters | TEXT | 参数定义（JSON格式） |
| environment_id | INTEGER | 执行环境ID（外键） |
| category_id | INTEGER | 分类ID（外键） |
| version | INTEGER | 版本号 |
| is_favorite | BOOLEAN | 是否收藏 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**关键特性**：
- 支持多种脚本类型
- 支持版本控制
- 支持依赖包自动安装

#### script_versions (脚本版本表)
存储脚本的历史版本。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| script_id | INTEGER | 脚本ID（外键） |
| version | INTEGER | 版本号 |
| code | TEXT | 版本代码 |
| dependencies | TEXT | 依赖包 |
| description | TEXT | 版本说明 |
| created_at | DATETIME | 创建时间 |

---

### 3. 分类和标签模块

#### categories (分类表)
脚本分类管理。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | VARCHAR(50) | 分类名称（唯一） |
| description | TEXT | 分类描述 |
| color | VARCHAR(20) | 分类颜色 |
| icon | VARCHAR(50) | 分类图标 |
| sort_order | INTEGER | 排序顺序 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### tags (标签表)
脚本标签管理。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | VARCHAR(50) | 标签名称（唯一） |
| color | VARCHAR(20) | 标签颜色 |
| created_at | DATETIME | 创建时间 |

#### script_tags (脚本标签关联表)
多对多关联脚本和标签。

| 字段 | 类型 | 说明 |
|------|------|------|
| script_id | INTEGER | 脚本ID（外键，级联删除） |
| tag_id | INTEGER | 标签ID（外键，级联删除） |
| created_at | DATETIME | 创建时间 |

---

### 4. 执行管理模块

#### environments (执行环境表)
存储不同的 Python/Node.js 执行环境配置。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | VARCHAR(100) | 环境名称（唯一） |
| type | VARCHAR(20) | 环境类型 (python/javascript) |
| executable_path | VARCHAR(500) | 解释器路径 |
| description | TEXT | 环境描述 |
| is_default | BOOLEAN | 是否默认环境 |
| version | VARCHAR(50) | 版本信息 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### executions (执行记录表)
存储脚本执行历史和状态。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| script_id | INTEGER | 脚本ID（外键） |
| environment_id | INTEGER | 执行环境ID（可选） |
| status | VARCHAR(20) | 执行状态 |
| progress | INTEGER | 执行进度 (0-100) |
| stage | VARCHAR(50) | 执行阶段 |
| pid | INTEGER | 进程ID |
| params | TEXT | 执行参数（JSON格式） |
| output | TEXT | 执行输出 |
| error | TEXT | 错误信息 |
| log_file | VARCHAR(255) | 日志文件路径 |
| start_time | DATETIME | 开始时间 |
| end_time | DATETIME | 结束时间 |
| created_at | DATETIME | 创建时间 |

**执行状态**：
- `pending`: 待执行
- `running`: 执行中
- `success`: 执行成功
- `failed`: 执行失败
- `cancelled`: 已取消

**执行阶段**：
- `preparing`: 准备中
- `installing_deps`: 安装依赖
- `running`: 运行中
- `finishing`: 完成中

---

### 5. 定时任务模块

#### schedules (定时任务表)
存储定时执行脚本的配置。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| script_id | INTEGER | 脚本ID（外键） |
| name | VARCHAR(100) | 任务名称 |
| description | TEXT | 任务描述 |
| cron | VARCHAR(100) | Cron表达式 |
| params | TEXT | 执行参数（JSON格式） |
| enabled | BOOLEAN | 是否启用 |
| last_run | DATETIME | 上次运行时间 |
| next_run | DATETIME | 下次运行时间 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**Cron表达式格式**：
```
* * * * *
│ │ │ │ │
│ │ │ │ └─ 星期 (0-6, 0=Sunday)
│ │ │ └─── 月份 (1-12)
│ │ └───── 日期 (1-31)
│ └─────── 小时 (0-23)
└───────── 分钟 (0-59)
```

---

### 6. 工作流引擎模块

#### workflows (工作流表)
存储工作流定义。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | VARCHAR(100) | 工作流名称（唯一） |
| description | TEXT | 工作流描述 |
| config | TEXT | 工作流配置（JSON格式） |
| enabled | BOOLEAN | 是否启用 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### workflow_nodes (工作流节点表)
存储工作流中的节点定义。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| workflow_id | INTEGER | 工作流ID（外键） |
| node_id | VARCHAR(50) | 节点ID（工作流内唯一） |
| node_type | VARCHAR(20) | 节点类型 |
| script_id | INTEGER | 脚本ID（脚本节点使用） |
| config | TEXT | 节点配置（JSON格式） |
| position_x | INTEGER | X坐标 |
| position_y | INTEGER | Y坐标 |
| created_at | DATETIME | 创建时间 |

**节点类型**：
- `script`: 脚本节点
- `delay`: 延迟节点
- `condition`: 条件节点

#### workflow_edges (工作流边表)
存储工作流节点之间的连接关系。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| workflow_id | INTEGER | 工作流ID（外键） |
| edge_id | VARCHAR(50) | 边ID（工作流内唯一） |
| source_node_id | VARCHAR(50) | 源节点ID |
| target_node_id | VARCHAR(50) | 目标节点ID |
| condition | TEXT | 条件配置（JSON格式） |
| created_at | DATETIME | 创建时间 |

**条件类型**：
- `success`: 前置节点成功时执行
- `failed`: 前置节点失败时执行
- `expression`: 表达式条件

#### workflow_executions (工作流执行记录表)
存储工作流执行历史。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| workflow_id | INTEGER | 工作流ID（外键） |
| status | VARCHAR(20) | 执行状态 |
| params | TEXT | 执行参数（JSON格式） |
| start_time | DATETIME | 开始时间 |
| end_time | DATETIME | 结束时间 |
| error | TEXT | 错误信息 |
| created_at | DATETIME | 创建时间 |

#### workflow_node_executions (工作流节点执行记录表)
存储工作流中每个节点的执行记录。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| workflow_execution_id | INTEGER | 工作流执行ID（外键） |
| node_id | VARCHAR(50) | 节点ID |
| execution_id | INTEGER | 脚本执行ID（脚本节点） |
| status | VARCHAR(20) | 执行状态 |
| output | TEXT | 输出信息 |
| error | TEXT | 错误信息 |
| start_time | DATETIME | 开始时间 |
| end_time | DATETIME | 结束时间 |
| created_at | DATETIME | 创建时间 |

**节点执行状态**：
- `pending`: 待执行
- `running`: 执行中
- `success`: 执行成功
- `failed`: 执行失败
- `skipped`: 跳过（条件不满足）

#### workflow_templates (工作流模板表)
存储预定义的工作流模板。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | VARCHAR(100) | 模板名称 |
| description | TEXT | 模板描述 |
| category | VARCHAR(50) | 模板分类 |
| icon | VARCHAR(50) | 模板图标 |
| template_config | TEXT | 模板配置（JSON格式） |
| is_builtin | BOOLEAN | 是否内置模板 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

---

### 7. 全局配置模块

#### global_variables (全局变量表)
存储全局环境变量，可在所有脚本中使用。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| key | VARCHAR(100) | 变量名（唯一） |
| value | TEXT | 变量值 |
| description | TEXT | 变量描述 |
| is_encrypted | BOOLEAN | 是否加密 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**使用方式**：
- 全局变量会自动注入到所有脚本的执行环境中
- 可通过环境变量访问：`os.environ.get('变量名')`

---

## 索引说明

系统为以下字段创建了索引以优化查询性能：

### 脚本相关
- `idx_scripts_category_id`: 按分类查询
- `idx_scripts_type`: 按类型查询
- `idx_scripts_created_at`: 按创建时间排序

### 执行记录相关
- `idx_executions_script_id`: 查询脚本的执行历史
- `idx_executions_status`: 按状态筛选
- `idx_executions_created_at`: 按时间排序

### 定时任务相关
- `idx_schedules_script_id`: 查询脚本的定时任务
- `idx_schedules_enabled`: 查询启用的任务
- `idx_schedules_next_run`: 按下次运行时间排序

### 工作流相关
- `idx_workflow_nodes_workflow_id`: 查询工作流的节点
- `idx_workflow_edges_workflow_id`: 查询工作流的边
- `idx_workflow_executions_workflow_id`: 查询工作流的执行历史
- `idx_workflow_node_executions_workflow_execution_id`: 查询执行记录的节点

---

## 数据关系图

```
脚本管理:
scripts ──┬── script_versions (1:N)
          ├── executions (1:N)
          ├── schedules (1:N)
          ├── script_tags (N:M) ── tags
          ├── category (N:1) ── categories
          └── environment (N:1) ── environments

工作流引擎:
workflows ──┬── workflow_nodes (1:N) ── scripts
            ├── workflow_edges (1:N)
            └── workflow_executions (1:N) ── workflow_node_executions (1:N) ── executions

AI功能:
ai_configs (独立表)

全局配置:
global_variables (独立表)
```

---

## 参数传递规范

### 脚本执行参数
所有参数通过环境变量传递：

```python
import os
import json

# 1. 获取单个参数
param_value = os.environ.get('PARAM_NAME', 'default_value')

# 2. 获取上传的文件列表
files_json = os.environ.get('FILES', '[]')
files = json.loads(files_json)

# 3. 获取全局变量
global_var = os.environ.get('GLOBAL_VAR_NAME')
```

### 文件处理
上传的文件会被复制到执行空间（独立目录），使用相对路径访问：

```python
# FILES环境变量格式: ["file1.txt", "file2.csv"]
files_json = os.environ.get('FILES', '[]')
files = json.loads(files_json)

for filename in files:
    # 直接使用文件名（相对路径）
    with open(filename, 'r') as f:
        content = f.read()
```

---

## 数据库初始化

使用提供的 `database_schema.sql` 文件初始化数据库：

```bash
sqlite3 database.db < database_schema.sql
```

或者使用 Python 初始化：

```python
from flask import Flask
from models import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db.init_app(app)

with app.app_context():
    db.create_all()
```

---

## 版本历史

- **v1.0** (2024-12): 初始版本
  - 基础脚本管理
  - 执行引擎
  - 定时任务

- **v1.1** (2024-12): 工作流引擎
  - 工作流可视化编辑
  - DAG执行引擎
  - 条件分支

- **v1.2** (2024-12): AI功能
  - AI配置管理
  - AI脚本生成
  - 脚本改进和解释

---

## 注意事项

1. **外键约束**：SQLite 默认不启用外键约束，需要在连接时启用
2. **事务处理**：所有写操作应在事务中进行
3. **索引维护**：定期重建索引以保持性能
4. **备份策略**：建议每日备份数据库文件
5. **日志清理**：定期清理旧的执行日志和输出

---

## 相关文件

- `database_schema.sql`: 完整的建表SQL语句
- `backend/models/*.py`: SQLAlchemy模型定义
- `backend/migrations/*.py`: 数据库迁移脚本
