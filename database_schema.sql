-- =====================================================
-- 脚本工具管理系统 - 数据库建表语句
-- =====================================================
-- 数据库类型: SQLite
-- 生成时间: 2025-12-19
-- 说明: 本文件包含系统所有表的建表语句和索引
-- =====================================================

-- =====================================================
-- AI配置相关表
-- =====================================================

-- AI配置表
-- 用途: 存储AI服务配置信息（API Key、Base URL、模型等）
CREATE TABLE IF NOT EXISTS ai_configs (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    provider VARCHAR(50) NOT NULL DEFAULT 'openai',          -- AI提供商 (openai, anthropic, custom)
    api_key VARCHAR(500) NOT NULL,                           -- API密钥
    base_url VARCHAR(500),                                   -- API基础URL
    model VARCHAR(100) DEFAULT 'gpt-4',                      -- 模型名称
    is_active BOOLEAN DEFAULT 1,                             -- 是否激活
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 创建时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP            -- 更新时间
);

-- =====================================================
-- 脚本管理相关表
-- =====================================================

-- 脚本表
-- 用途: 存储脚本的基本信息和代码
CREATE TABLE IF NOT EXISTS scripts (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,                       -- 脚本名称（唯一）
    description TEXT,                                        -- 脚本描述
    type VARCHAR(20) NOT NULL,                               -- 脚本类型 (python, javascript, bash)
    code TEXT NOT NULL,                                      -- 脚本代码
    dependencies TEXT,                                       -- 依赖包（JSON格式）
    parameters TEXT,                                         -- 参数定义（JSON格式）
    environment_id INTEGER,                                  -- 执行环境ID
    category_id INTEGER,                                     -- 分类ID
    version INTEGER DEFAULT 1,                               -- 版本号
    is_favorite BOOLEAN DEFAULT 0,                           -- 是否收藏
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 创建时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 更新时间
    FOREIGN KEY(environment_id) REFERENCES environments(id),
    FOREIGN KEY(category_id) REFERENCES categories(id)
);

-- 脚本版本表
-- 用途: 存储脚本的历史版本
CREATE TABLE IF NOT EXISTS script_versions (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER NOT NULL,                              -- 脚本ID
    version INTEGER NOT NULL,                                -- 版本号
    code TEXT NOT NULL,                                      -- 版本代码
    dependencies TEXT,                                       -- 依赖包
    description TEXT,                                        -- 版本说明
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 创建时间
    FOREIGN KEY(script_id) REFERENCES scripts(id)
);

-- =====================================================
-- 分类和标签相关表
-- =====================================================

-- 分类表
-- 用途: 脚本分类管理
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,                        -- 分类名称（唯一）
    description TEXT,                                        -- 分类描述
    color VARCHAR(20),                                       -- 分类颜色
    icon VARCHAR(50),                                        -- 分类图标
    sort_order INTEGER DEFAULT 0,                            -- 排序顺序
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 创建时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP            -- 更新时间
);

-- 标签表
-- 用途: 脚本标签管理
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,                        -- 标签名称（唯一）
    color VARCHAR(20),                                       -- 标签颜色
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP            -- 创建时间
);

-- 脚本标签关联表
-- 用途: 多对多关联脚本和标签
CREATE TABLE IF NOT EXISTS script_tags (
    script_id INTEGER NOT NULL,                              -- 脚本ID
    tag_id INTEGER NOT NULL,                                 -- 标签ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 创建时间
    PRIMARY KEY (script_id, tag_id),
    FOREIGN KEY(script_id) REFERENCES scripts(id) ON DELETE CASCADE,
    FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- =====================================================
-- 执行相关表
-- =====================================================

-- 执行环境表
-- 用途: 存储不同的Python/Node.js执行环境配置
CREATE TABLE IF NOT EXISTS environments (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,                       -- 环境名称（唯一）
    type VARCHAR(20) NOT NULL,                               -- 环境类型 (python, javascript)
    executable_path VARCHAR(500) NOT NULL,                   -- 解释器路径
    description TEXT,                                        -- 环境描述
    is_default BOOLEAN DEFAULT 0,                            -- 是否默认环境
    version VARCHAR(50),                                     -- 版本信息
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 创建时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP            -- 更新时间
);

-- 执行记录表
-- 用途: 存储脚本执行历史和状态
CREATE TABLE IF NOT EXISTS executions (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER NOT NULL,                              -- 脚本ID
    environment_id INTEGER,                                  -- 执行环境ID（可选）
    status VARCHAR(20) NOT NULL,                             -- 执行状态 (pending, running, success, failed, cancelled)
    progress INTEGER DEFAULT 0,                              -- 执行进度 (0-100)
    stage VARCHAR(50),                                       -- 执行阶段 (preparing, installing_deps, running, finishing)
    pid INTEGER,                                             -- 进程ID
    params TEXT,                                             -- 执行参数（JSON格式）
    output TEXT,                                             -- 执行输出
    error TEXT,                                              -- 错误信息
    log_file VARCHAR(255),                                   -- 日志文件路径
    start_time DATETIME,                                     -- 开始时间
    end_time DATETIME,                                       -- 结束时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 创建时间
    FOREIGN KEY(script_id) REFERENCES scripts(id),
    FOREIGN KEY(environment_id) REFERENCES environments(id)
);

-- =====================================================
-- 定时任务相关表
-- =====================================================

-- 定时任务表
-- 用途: 存储定时执行脚本的配置
CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER NOT NULL,                              -- 脚本ID
    name VARCHAR(100) NOT NULL,                              -- 任务名称
    description TEXT,                                        -- 任务描述
    cron VARCHAR(100) NOT NULL,                              -- Cron表达式
    params TEXT,                                             -- 执行参数（JSON格式）
    enabled BOOLEAN DEFAULT 1,                               -- 是否启用
    last_run DATETIME,                                       -- 上次运行时间
    next_run DATETIME,                                       -- 下次运行时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 创建时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 更新时间
    FOREIGN KEY(script_id) REFERENCES scripts(id)
);

-- =====================================================
-- 工作流相关表
-- =====================================================

-- 工作流表
-- 用途: 存储工作流定义
CREATE TABLE IF NOT EXISTS workflows (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,                       -- 工作流名称（唯一）
    description TEXT,                                        -- 工作流描述
    config TEXT NOT NULL,                                    -- 工作流配置（JSON格式，包含节点和边）
    enabled BOOLEAN DEFAULT 1,                               -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 创建时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP            -- 更新时间
);

-- 工作流节点表
-- 用途: 存储工作流中的节点定义
CREATE TABLE IF NOT EXISTS workflow_nodes (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER NOT NULL,                            -- 工作流ID
    node_id VARCHAR(50) NOT NULL,                            -- 节点ID（在工作流中唯一）
    node_type VARCHAR(20) NOT NULL,                          -- 节点类型 (script, delay, condition)
    script_id INTEGER,                                       -- 脚本ID（脚本节点使用）
    config TEXT,                                             -- 节点配置（JSON格式）
    position_x INTEGER DEFAULT 0,                            -- X坐标（用于可视化）
    position_y INTEGER DEFAULT 0,                            -- Y坐标（用于可视化）
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 创建时间
    FOREIGN KEY(workflow_id) REFERENCES workflows(id),
    FOREIGN KEY(script_id) REFERENCES scripts(id)
);

-- 工作流边表
-- 用途: 存储工作流节点之间的连接关系
CREATE TABLE IF NOT EXISTS workflow_edges (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER NOT NULL,                            -- 工作流ID
    edge_id VARCHAR(50) NOT NULL,                            -- 边ID（在工作流中唯一）
    source_node_id VARCHAR(50) NOT NULL,                     -- 源节点ID
    target_node_id VARCHAR(50) NOT NULL,                     -- 目标节点ID
    condition TEXT,                                          -- 条件配置（JSON格式）
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 创建时间
    FOREIGN KEY(workflow_id) REFERENCES workflows(id)
);

-- 工作流执行记录表
-- 用途: 存储工作流执行历史
CREATE TABLE IF NOT EXISTS workflow_executions (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER NOT NULL,                            -- 工作流ID
    status VARCHAR(20) NOT NULL,                             -- 执行状态 (pending, running, success, failed)
    params TEXT,                                             -- 执行参数（JSON格式）
    start_time DATETIME,                                     -- 开始时间
    end_time DATETIME,                                       -- 结束时间
    error TEXT,                                              -- 错误信息
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 创建时间
    FOREIGN KEY(workflow_id) REFERENCES workflows(id)
);

-- 工作流节点执行记录表
-- 用途: 存储工作流中每个节点的执行记录
CREATE TABLE IF NOT EXISTS workflow_node_executions (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    workflow_execution_id INTEGER NOT NULL,                  -- 工作流执行ID
    node_id VARCHAR(50) NOT NULL,                            -- 节点ID
    execution_id INTEGER,                                    -- 脚本执行ID（脚本节点使用）
    status VARCHAR(20) NOT NULL,                             -- 执行状态 (pending, running, success, failed, skipped)
    output TEXT,                                             -- 输出信息
    error TEXT,                                              -- 错误信息
    start_time DATETIME,                                     -- 开始时间
    end_time DATETIME,                                       -- 结束时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 创建时间
    FOREIGN KEY(workflow_execution_id) REFERENCES workflow_executions(id),
    FOREIGN KEY(execution_id) REFERENCES executions(id)
);

-- 工作流模板表
-- 用途: 存储预定义的工作流模板
CREATE TABLE IF NOT EXISTS workflow_templates (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,                              -- 模板名称
    description TEXT,                                        -- 模板描述
    category VARCHAR(50),                                    -- 模板分类
    icon VARCHAR(50),                                        -- 模板图标
    template_config TEXT NOT NULL,                           -- 模板配置（JSON格式）
    is_builtin BOOLEAN DEFAULT 0,                            -- 是否内置模板
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 创建时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP            -- 更新时间
);

-- =====================================================
-- 全局配置相关表
-- =====================================================

-- 全局变量表
-- 用途: 存储全局环境变量，可在所有脚本中使用
CREATE TABLE IF NOT EXISTS global_variables (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    key VARCHAR(100) NOT NULL UNIQUE,                        -- 变量名（唯一）
    value TEXT NOT NULL,                                     -- 变量值
    description TEXT,                                        -- 变量描述
    is_encrypted BOOLEAN DEFAULT 0,                          -- 是否加密
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 创建时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP            -- 更新时间
);

-- =====================================================
-- 索引创建
-- =====================================================

-- 脚本表索引
CREATE INDEX IF NOT EXISTS idx_scripts_category_id ON scripts(category_id);
CREATE INDEX IF NOT EXISTS idx_scripts_type ON scripts(type);
CREATE INDEX IF NOT EXISTS idx_scripts_created_at ON scripts(created_at);

-- 执行记录表索引
CREATE INDEX IF NOT EXISTS idx_executions_script_id ON executions(script_id);
CREATE INDEX IF NOT EXISTS idx_executions_status ON executions(status);
CREATE INDEX IF NOT EXISTS idx_executions_created_at ON executions(created_at);

-- 定时任务表索引
CREATE INDEX IF NOT EXISTS idx_schedules_script_id ON schedules(script_id);
CREATE INDEX IF NOT EXISTS idx_schedules_enabled ON schedules(enabled);
CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON schedules(next_run);

-- 工作流节点表索引
CREATE INDEX IF NOT EXISTS idx_workflow_nodes_workflow_id ON workflow_nodes(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_nodes_node_id ON workflow_nodes(node_id);

-- 工作流边表索引
CREATE INDEX IF NOT EXISTS idx_workflow_edges_workflow_id ON workflow_edges(workflow_id);

-- 工作流执行记录表索引
CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflow_executions(status);

-- 工作流节点执行记录表索引
CREATE INDEX IF NOT EXISTS idx_workflow_node_executions_workflow_execution_id ON workflow_node_executions(workflow_execution_id);
CREATE INDEX IF NOT EXISTS idx_workflow_node_executions_node_id ON workflow_node_executions(node_id);

-- =====================================================
-- 说明文档
-- =====================================================

-- 数据库设计说明：
--
-- 1. 脚本管理
--    - scripts: 存储脚本代码和元信息
--    - script_versions: 支持脚本版本控制
--    - categories/tags: 支持分类和标签管理
--
-- 2. 执行管理
--    - environments: 支持多个Python/Node.js环境
--    - executions: 记录每次脚本执行的详细信息
--    - 支持实时进度跟踪和日志输出
--
-- 3. 定时任务
--    - schedules: 使用Cron表达式定时执行脚本
--    - 支持启用/禁用和参数配置
--
-- 4. 工作流引擎
--    - workflows: 工作流定义
--    - workflow_nodes: 工作流节点（脚本/延迟/条件）
--    - workflow_edges: 节点连接关系
--    - workflow_executions: 工作流执行记录
--    - workflow_node_executions: 节点执行记录
--    - workflow_templates: 预定义模板
--
-- 5. AI功能
--    - ai_configs: AI服务配置
--    - 支持多个AI提供商和模型
--
-- 6. 全局配置
--    - global_variables: 全局环境变量
--    - 所有脚本执行时自动注入
