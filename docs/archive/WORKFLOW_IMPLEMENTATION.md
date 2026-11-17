# 脚本工作流功能实现文档

## 📋 实现概览

本次实现了 TODO.md 中 **P1 - 脚本工作流** 的后端核心功能，包括工作流定义、执行引擎、依赖关系管理和条件执行等。

---

## ✅ 已完成功能

### 1. 数据模型设计 ✅

#### 1.1 Workflow (工作流表)
**文件**: `backend/models/workflow.py`

**字段**:
- `id`: 主键
- `name`: 工作流名称（唯一）
- `description`: 描述
- `config`: JSON格式的工作流配置
- `enabled`: 是否启用
- `created_at`, `updated_at`: 时间戳

**关系**:
- `nodes`: 一对多关联 WorkflowNode
- `executions`: 一对多关联 WorkflowExecution

#### 1.2 WorkflowNode (工作流节点表)
**字段**:
- `id`: 主键
- `workflow_id`: 工作流ID
- `node_id`: 节点唯一标识
- `node_type`: 节点类型 (script, condition, parallel, delay)
- `script_id`: 关联的脚本ID（script类型节点）
- `config`: JSON格式的节点配置
- `position_x`, `position_y`: 节点坐标（用于可视化）

**节点类型**:
- **script**: 脚本执行节点
- **condition**: 条件判断节点
- **parallel**: 并行执行节点（预留）
- **delay**: 延迟节点

#### 1.3 WorkflowEdge (工作流边表)
**字段**:
- `id`: 主键
- `workflow_id`: 工作流ID
- `edge_id`: 边唯一标识
- `source_node_id`: 源节点ID
- `target_node_id`: 目标节点ID
- `condition`: JSON格式的条件配置

**用途**: 定义节点之间的连接关系和执行顺序

#### 1.4 WorkflowExecution (工作流执行记录表)
**字段**:
- `id`: 主键
- `workflow_id`: 工作流ID
- `status`: 执行状态 (pending, running, success, failed, cancelled)
- `params`: JSON格式的执行参数
- `start_time`, `end_time`: 时间戳
- `error`: 错误信息

#### 1.5 WorkflowNodeExecution (节点执行记录表)
**字段**:
- `id`: 主键
- `workflow_execution_id`: 工作流执行ID
- `node_id`: 节点ID
- `execution_id`: 关联的脚本执行ID
- `status`: 执行状态 (pending, running, success, failed, skipped)
- `output`: 输出结果
- `error`: 错误信息
- `start_time`, `end_time`: 时间戳

---

### 2. 后端API实现 ✅

**文件**: `backend/api/workflows.py`

#### 2.1 工作流管理API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/workflows` | 获取工作流列表 |
| GET | `/api/workflows/<id>` | 获取工作流详情（含节点和边） |
| POST | `/api/workflows` | 创建工作流 |
| PUT | `/api/workflows/<id>` | 更新工作流 |
| DELETE | `/api/workflows/<id>` | 删除工作流 |
| POST | `/api/workflows/<id>/execute` | 执行工作流 |
| POST | `/api/workflows/<id>/toggle` | 启用/禁用工作流 |

#### 2.2 执行历史API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/workflow-executions` | 获取执行历史（支持分页和筛选） |
| GET | `/api/workflow-executions/<id>` | 获取执行详情（含节点执行记录） |
| POST | `/api/workflow-executions/<id>/cancel` | 取消正在执行的工作流 |

#### API请求示例

**创建工作流**:
```json
POST /api/workflows
{
  "name": "数据处理工作流",
  "description": "下载数据 -> 清洗 -> 分析 -> 上传",
  "config": {},
  "enabled": true,
  "nodes": [
    {
      "node_id": "node_1",
      "node_type": "script",
      "script_id": 1,
      "config": {},
      "position": {"x": 100, "y": 100}
    },
    {
      "node_id": "node_2",
      "node_type": "script",
      "script_id": 2,
      "config": {},
      "position": {"x": 300, "y": 100}
    }
  ],
  "edges": [
    {
      "edge_id": "edge_1",
      "source": "node_1",
      "target": "node_2",
      "condition": null
    }
  ]
}
```

**执行工作流**:
```json
POST /api/workflows/1/execute
{
  "params": {
    "input_file": "data.csv",
    "output_dir": "/tmp/output"
  }
}
```

---

### 3. 工作流执行引擎 ✅

**文件**: `backend/services/workflow_executor.py`

#### 3.1 核心功能

1. **依赖关系图构建**
   - 自动分析节点之间的依赖关系
   - 构建有向无环图（DAG）
   - 识别入口节点（无依赖的节点）

2. **拓扑排序执行**
   - 按依赖关系顺序执行节点
   - 支持多个入口节点
   - 自动处理节点执行队列

3. **条件执行**
   - 支持基于前置节点状态的条件判断
   - 条件不满足时自动跳过节点
   - 支持表达式条件（简单实现）

4. **节点类型支持**
   - **script**: 执行关联的脚本，创建脚本执行记录
   - **delay**: 延迟指定秒数
   - **condition**: 条件判断节点

5. **执行状态管理**
   - 实时更新工作流和节点执行状态
   - 记录执行开始和结束时间
   - 记录输出和错误信息

#### 3.2 执行流程

```
1. 创建工作流执行记录（status: pending）
2. 更新状态为 running
3. 加载工作流定义（节点和边）
4. 构建依赖关系图
5. 找到入口节点
6. 按拓扑顺序执行节点：
   a. 检查依赖是否都已执行
   b. 评估条件（如果有）
   c. 执行节点
   d. 记录执行结果
   e. 将下一个节点加入队列
7. 更新工作流执行状态（success/failed）
```

#### 3.3 条件执行

支持的条件类型：

1. **success条件**: 前置节点执行成功
```json
{
  "type": "success",
  "node_id": "node_1"
}
```

2. **failed条件**: 前置节点执行失败
```json
{
  "type": "failed",
  "node_id": "node_1"
}
```

3. **expression条件**: 自定义表达式
```json
{
  "type": "expression",
  "expression": "node_1['status'] == 'success' and node_1['output']"
}
```

---

### 4. 数据库迁移 ✅

**文件**: `backend/migrations/add_workflow_tables.py`

**创建的表**:
- `workflows`
- `workflow_nodes`
- `workflow_edges`
- `workflow_executions`
- `workflow_node_executions`

**运行方式**:
```bash
PYTHONPATH=/path/to/backend:$PYTHONPATH python3 backend/migrations/add_workflow_tables.py
```

---

## 🎯 核心特性

### 1. 脚本依赖关系定义 ✅
- 通过 WorkflowEdge 定义节点之间的依赖
- 自动构建 DAG
- 支持多个依赖和多个后继

### 2. 条件执行 ✅
- 基于前置节点状态的条件判断
- 条件不满足时跳过节点
- 支持自定义条件表达式

### 3. 执行历史记录 ✅
- 完整的工作流执行记录
- 每个节点的执行记录
- 执行时间、状态、输出、错误信息

### 4. 并行执行支持 ⚠️
- 数据模型已预留 parallel 节点类型
- 执行引擎需进一步优化以支持真正的并行

### 5. DAG可视化 ⚠️
- 节点已存储坐标信息（position_x, position_y）
- 前端可视化编辑器待实现
- 建议使用 Vue Flow 或 React Flow 库

---

## 📊 工作流示例

### 示例1: 简单线性工作流

```
下载数据 -> 数据清洗 -> 数据分析 -> 生成报告
```

**配置**:
```json
{
  "nodes": [
    {"node_id": "download", "node_type": "script", "script_id": 1},
    {"node_id": "clean", "node_type": "script", "script_id": 2},
    {"node_id": "analyze", "node_type": "script", "script_id": 3},
    {"node_id": "report", "node_type": "script", "script_id": 4}
  ],
  "edges": [
    {"source": "download", "target": "clean"},
    {"source": "clean", "target": "analyze"},
    {"source": "analyze", "target": "report"}
  ]
}
```

### 示例2: 条件分支工作流

```
数据验证 -> 成功 -> 数据处理
          -> 失败 -> 发送告警
```

**配置**:
```json
{
  "nodes": [
    {"node_id": "validate", "node_type": "script", "script_id": 1},
    {"node_id": "process", "node_type": "script", "script_id": 2},
    {"node_id": "alert", "node_type": "script", "script_id": 3}
  ],
  "edges": [
    {
      "source": "validate",
      "target": "process",
      "condition": {"type": "success", "node_id": "validate"}
    },
    {
      "source": "validate",
      "target": "alert",
      "condition": {"type": "failed", "node_id": "validate"}
    }
  ]
}
```

### 示例3: 并行执行工作流（预留）

```
数据下载 -> 处理A
         -> 处理B  -> 合并结果
         -> 处理C
```

---

## 🔧 技术实现细节

### 依赖关系图构建

```python
def build_dependency_graph(nodes, edges):
    """构建依赖关系图"""
    graph = {node_id: {'deps': [], 'next': []} for node_id in nodes.keys()}

    for edge in edges:
        # source -> target: target依赖于source
        graph[edge.target_node_id]['deps'].append({
            'node_id': edge.source_node_id,
            'condition': edge.condition
        })
        graph[edge.source_node_id]['next'].append({
            'node_id': edge.target_node_id,
            'condition': edge.condition
        })

    return graph
```

### 节点执行

```python
def execute_node(workflow_execution, node, params, node_results):
    """执行单个节点"""
    if node.node_type == 'script':
        # 创建脚本执行记录并执行
        script_execution = Execution(...)
        execute_script(script_execution.id)

    elif node.node_type == 'delay':
        # 延迟指定时间
        time.sleep(delay_seconds)

    elif node.node_type == 'condition':
        # 仅评估条件
        evaluate_condition(...)
```

---

## 📝 待实现功能

### 1. DAG可视化编辑器 ✅ (已完成)
- ✅ 使用 Vue Flow 实现可视化编辑器
- ✅ 拖拽创建节点
- ✅ 连线定义依赖关系
- ✅ 实时预览工作流图
- ✅ 自定义节点样式（脚本节点、延迟节点）

**实现文件**:
- `frontend/src/components/WorkflowEditor.vue` - 主编辑器组件
- `frontend/src/components/workflow-nodes/ScriptNode.vue` - 脚本节点
- `frontend/src/components/workflow-nodes/DelayNode.vue` - 延迟节点

### 2. 工作流模板 ✅ (已完成)
- ✅ 模板数据模型 (`WorkflowTemplate`)
- ✅ 模板管理 API (创建、查询、删除)
- ✅ 内置 5 个常用模板
- ✅ 模板分类和筛选
- ✅ 一键使用模板创建工作流
- ✅ 前端模板选择界面

**内置模板**:
1. 简单顺序执行
2. 条件分支执行
3. 数据处理流水线（ETL）
4. 延迟执行模板
5. API 调用链

### 3. 真正的并行执行
- 使用线程池或进程池
- 支持 parallel 节点类型
- 等待所有并行节点完成

### 4. 更强大的条件系统
- 支持复杂的逻辑表达式
- 变量替换
- 上下文传递

---

## 🚀 使用方式

### 1. 创建工作流

```bash
curl -X POST http://localhost:5000/api/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试工作流",
    "description": "测试工作流描述",
    "nodes": [...],
    "edges": [...]
  }'
```

### 2. 执行工作流

```bash
curl -X POST http://localhost:5000/api/workflows/1/execute \
  -H "Content-Type: application/json" \
  -d '{"params": {}}'
```

### 3. 查看执行历史

```bash
curl http://localhost:5000/api/workflow-executions
```

### 4. 查看执行详情

```bash
curl http://localhost:5000/api/workflow-executions/1
```

---

## 📈 完成状态

- ✅ 数据模型设计 (100%)
- ✅ 后端API实现 (100%)
- ✅ 工作流执行引擎 (100%)
- ✅ 条件执行逻辑 (100%)
- ✅ 依赖关系管理 (100%)
- ✅ DAG可视化编辑器 (100%)
- ✅ 工作流模板系统 (100%)
- ⚠️ 真正的并行执行 (50% - 模型已支持，执行引擎待优化)

**总体完成度**: 94% (7.5/8项)

---

## 🎉 总结

工作流功能已全面完成，包括：
- 完整的数据模型
- RESTful API
- 强大的执行引擎
- 条件执行支持
- 依赖关系管理
- **DAG可视化编辑器（Vue Flow）**
- **工作流模板系统（5个内置模板）**

前端可视化编辑器和模板系统已完成实现，用户可以通过拖拽方式创建工作流，或从模板快速开始。

---

**最后更新时间**: 2025-12-05
**版本**: v1.3.0
**维护者**: Claude Code

