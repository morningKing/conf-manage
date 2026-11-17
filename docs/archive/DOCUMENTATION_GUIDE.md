# 文档导读指南

## 项目文档总览

本项目包含以下文档，按照用途分类：

### 1. 核心技术文档

#### PROJECT_ANALYSIS.md (34KB - 最全面)
**用途：** 深入理解项目的完整技术文档

**包含内容：**
- 项目概览和技术栈（Vue3、Flask、SQLite）
- 完整的数据库模型定义（Script、ScriptVersion、Execution、Schedule）
- 脚本创建/编辑流程（前端表单 → 后端API → 数据库）
- 脚本执行流程（执行参数、文件上传、后台执行、实时日志）
- 文件系统结构（execution_spaces、logs、uploads目录）
- 前端组件架构（CodeEditor、FileUpload、ExecutionFiles）
- 完整的API端点文档
- 参数传递方式（Python命令行、JavaScript环境变量）
- 所有关键代码的位置

**适合人群：** 需要深入了解系统架构的开发人员

---

### 2. 快速参考文档

#### QUICK_REFERENCE.md (11KB - 最实用)
**用途：** 日常开发和问题排查的快速查询

**包含内容：**
- 项目结构速览（树形目录结构）
- 数据模型关系图
- 脚本创建/执行/定时任务流程图
- 参数和文件传递详解（实例代码）
- API快速查询（curl命令示例）
- 版本管理说明（如何触发版本创建、如何回滚）
- 定时任务Cron表达式示例
- 常见问题解答（Q&A）
- 配置调整指南（如何修改超时、跨域、文件大小限制等）
- 调试技巧（查看日志、数据库查询、SSE监控）

**适合人群：** 日常使用和维护项目的开发人员

---

### 3. 文件索引文档

#### FILE_INDEX.md (11KB - 最详细)
**用途：** 快速定位具体的文件和代码

**包含内容：**
- 后端文件完整索引（app.py、config.py、所有模型、所有API端点）
- 前端文件完整索引（所有视图、所有组件、API服务）
- 数据库和日志文件说明
- 配置和启动脚本说明
- 文件关系图（组件依赖关系）
- 代码量统计
- 关键代码片段位置速查表（快速找到某个功能的代码）

**适合人群：** 需要定位具体代码的开发人员

---

### 4. 特定功能文档

#### CODE_EDITOR_GUIDE.md (5.2KB)
**用途：** 代码编辑器使用和开发指南

**包含内容：**
- CodeEditor组件的使用
- CodeMirror集成
- 支持的语言和主题
- 与Scripts.vue的集成

---

#### FILE_UPLOAD_GUIDE.md (6.1KB)
**用途：** 文件上传功能的使用和开发指南

**包含内容：**
- FileUpload组件的使用
- 拖拽上传实现
- 与执行流程的集成
- 文件大小限制

---

#### WORKSPACE_GUIDE.md (9.7KB)
**用途：** 执行空间和工作目录的说明

**包含内容：**
- 执行空间的概念
- 文件管理
- 日志管理
- 清理和维护

---

#### USAGE.md (5.6KB)
**用途：** 系统的使用手册

**包含内容：**
- 快速开始步骤
- 主要功能的使用方法
- 常见操作流程

---

### 5. 项目文档

#### README.md (4.0KB)
**用途：** 项目简介和快速开始

**包含内容：**
- 系统简介
- 技术栈
- 核心功能
- 目录结构
- 快速开始
- API文档概览
- 数据库模型概览

---

## 文档选读指南

### 如果你想...

#### 快速了解项目是什么
→ 阅读 **README.md** (5分钟)

#### 了解如何使用系统
→ 阅读 **USAGE.md** (10分钟)

#### 深入了解技术架构
→ 阅读 **PROJECT_ANALYSIS.md** (30分钟)

#### 日常开发时查询信息
→ 使用 **QUICK_REFERENCE.md** (按需查阅)

#### 找到某个具体的代码
→ 使用 **FILE_INDEX.md** (按需查阅)

#### 了解某个特定功能
→ 阅读对应的功能文档：
- 代码编辑 → CODE_EDITOR_GUIDE.md
- 文件上传 → FILE_UPLOAD_GUIDE.md
- 工作空间 → WORKSPACE_GUIDE.md

---

## 按功能区分的学习路径

### 1. 脚本管理功能
阅读顺序：
1. QUICK_REFERENCE.md - 脚本创建流程部分
2. PROJECT_ANALYSIS.md - 第三章（脚本创建/编辑流程）
3. FILE_INDEX.md - 找到具体的文件位置

关键文件：
- `/backend/api/scripts.py` - 脚本API
- `/frontend/src/views/Scripts.vue` - 脚本页面
- `/backend/models/script.py` - 数据模型

---

### 2. 脚本执行功能
阅读顺序：
1. QUICK_REFERENCE.md - 脚本执行流程和参数传递部分
2. PROJECT_ANALYSIS.md - 第四章（脚本执行流程）
3. FILE_UPLOAD_GUIDE.md - 文件上传部分
4. FILE_INDEX.md - 找到具体的文件位置

关键文件：
- `/backend/services/executor.py` - 执行引擎
- `/backend/api/executions.py` - 执行API
- `/frontend/src/views/Scripts.vue` - 执行对话框
- `/frontend/src/components/FileUpload.vue` - 文件上传组件

---

### 3. 代码编辑功能
阅读顺序：
1. CODE_EDITOR_GUIDE.md
2. PROJECT_ANALYSIS.md - CodeEditor组件部分
3. 查看 `/frontend/src/components/CodeEditor.vue`

---

### 4. 文件管理功能
阅读顺序：
1. FILE_UPLOAD_GUIDE.md
2. WORKSPACE_GUIDE.md
3. PROJECT_ANALYSIS.md - 文件系统结构部分
4. 查看 `/frontend/src/views/Files.vue`

---

### 5. 定时任务功能
阅读顺序：
1. QUICK_REFERENCE.md - 定时任务部分
2. PROJECT_ANALYSIS.md - Schedule模型和API
3. 查看 `/backend/api/schedules.py`

---

## 重要概念速查

### 脚本存储位置
**数据库：** SQLite (`/data/database.db`)
- `scripts` 表：脚本代码存在 `code` 字段
- `script_versions` 表：版本历史

**执行时：** `/execution_spaces/execution_{id}/` 目录

### 参数传递方式
**Python脚本：** 命令行参数
```
script.py --param1 value1 --param2 value2
```

**JavaScript脚本：** 环境变量
```
PARAM_PARAM1=value1 PARAM_PARAM2=value2
```

### 文件上传位置
**执行时上传：** `/execution_spaces/execution_{id}/`
**管理面板上传：** `/data/uploads/`

### 日志位置
**执行日志：** `/logs/execution_{id}.log`

---

## 代码示例速查

### Python脚本接收参数
```python
import sys
for i in range(1, len(sys.argv), 2):
    key = sys.argv[i][2:]  # 去掉 --
    value = sys.argv[i+1]
```

### JavaScript脚本接收参数
```javascript
const param = process.env.PARAM_NAME
const files = JSON.parse(process.env.PARAM_FILES || '[]')
```

### 创建脚本API调用
```bash
curl -X POST http://localhost:5000/api/scripts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test",
    "type": "python",
    "code": "print(\"hello\")"
  }'
```

### 执行脚本API调用
```bash
curl -X POST http://localhost:5000/api/scripts/1/execute \
  -F 'file0=@input.csv' \
  -F 'params={"key":"value"}'
```

---

## 常见疑问

### Q: 脚本代码存在哪里？
A: SQLite数据库的 `scripts` 表的 `code` 字段。查看：PROJECT_ANALYSIS.md 第二章

### Q: 怎样修改脚本执行超时时间？
A: 修改 `/backend/config.py` 中的 `EXECUTION_TIMEOUT`。查看：QUICK_REFERENCE.md 配置调整部分

### Q: 怎样添加新的脚本类型（如Ruby）？
A: 需要修改 config.py 的 SUPPORTED_SCRIPT_TYPES，然后在 executor.py 中添加对应的执行逻辑

### Q: 怎样调试脚本执行？
A: 查看 QUICK_REFERENCE.md 的调试技巧部分

### Q: 怎样查看执行空间的文件？
A: 使用 `GET /api/executions/<id>/files` API。查看：PROJECT_ANALYSIS.md 第四章或 FILE_INDEX.md

---

## 文档更新说明

这份文档包含以下新生成的内容：
- **PROJECT_ANALYSIS.md** - 完整的技术分析文档（本次生成）
- **QUICK_REFERENCE.md** - 快速参考指南（本次生成）
- **FILE_INDEX.md** - 文件索引（本次生成）
- **DOCUMENTATION_GUIDE.md** - 本文档（本次生成）

其他文档由项目原作者提供。

---

## 获得帮助

如果你在查阅文档时遇到问题：

1. 首先查看 **QUICK_REFERENCE.md** 的常见问题解答
2. 如果问题涉及代码，使用 **FILE_INDEX.md** 找到对应的文件
3. 阅读找到的文件的代码注释
4. 如果还是不清楚，查看 **PROJECT_ANALYSIS.md** 获得更详细的解释

---

## 快速导航

| 我想要... | 文档 | 章节 |
|---------|------|------|
| 项目简介 | README.md | 所有 |
| 快速开始 | README.md | 快速开始 |
| 使用教程 | USAGE.md | 所有 |
| 代码编辑器 | CODE_EDITOR_GUIDE.md | 所有 |
| 文件上传 | FILE_UPLOAD_GUIDE.md | 所有 |
| 工作空间 | WORKSPACE_GUIDE.md | 所有 |
| 技术架构 | PROJECT_ANALYSIS.md | 一到九 |
| 快速查询 | QUICK_REFERENCE.md | 所有 |
| 文件位置 | FILE_INDEX.md | 所有 |
| 脚本创建流程 | QUICK_REFERENCE.md | 脚本创建流程 |
| 脚本执行流程 | QUICK_REFERENCE.md | 脚本执行流程 |
| API文档 | PROJECT_ANALYSIS.md | 第七章 |
| 参数传递 | QUICK_REFERENCE.md | 参数和文件传递 |
| 配置修改 | QUICK_REFERENCE.md | 配置调整 |
| 问题排查 | QUICK_REFERENCE.md | 常见问题处理 |
| 调试技巧 | QUICK_REFERENCE.md | 调试技巧 |

