# 项目快速参考指南

## 项目结构速览

```
conf-manage/
├── backend/                    # Flask后端
│   ├── models/                # 数据模型
│   │   ├── script.py         # Script 和 ScriptVersion
│   │   ├── execution.py      # Execution 
│   │   └── schedule.py       # Schedule
│   ├── api/                  # API路由
│   │   ├── scripts.py        # 脚本CRUD和版本管理
│   │   ├── executions.py     # 执行历史和日志
│   │   ├── schedules.py      # 定时任务管理
│   │   └── files.py          # 文件管理
│   ├── services/             # 业务逻辑
│   │   ├── executor.py       # 脚本执行引擎
│   │   └── scheduler.py      # 定时调度管理
│   ├── app.py               # Flask应用入口
│   └── config.py            # 配置（路径、超时等）
│
├── frontend/                  # Vue 3前端
│   ├── src/
│   │   ├── views/           # 页面
│   │   │   ├── Scripts.vue        # 脚本管理
│   │   │   ├── Executions.vue     # 执行历史
│   │   │   ├── Schedules.vue      # 定时任务
│   │   │   └── Files.vue          # 文件管理
│   │   ├── components/      # 组件
│   │   │   ├── CodeEditor.vue     # 代码编辑器
│   │   │   ├── FileUpload.vue     # 文件上传
│   │   │   └── ExecutionFiles.vue # 执行文件查看
│   │   └── api/             # API服务
│   │       └── index.js     # API接口封装
│   └── package.json
│
├── data/
│   ├── database.db          # SQLite数据库
│   └── uploads/             # 上传文件存储
│
├── execution_spaces/        # 执行空间（每次执行一个）
│   ├── execution_1/
│   │   ├── script_1.py      # 临时脚本文件
│   │   └── ...              # 上传的文件和输出文件
│   └── ...
│
└── logs/                    # 执行日志
    ├── execution_1.log
    └── ...
```

---

## 数据模型关系图

```
Script
├── ScriptVersion (一对多)
├── Execution (一对多)
└── Schedule (一对多)

Execution
└── Script (多对一)

Schedule
└── Script (多对一)
```

---

## 脚本创建流程

```
前端 (Scripts.vue)
  ↓
  表单输入: name, type, description, code, dependencies
  ↓
  handleSave() → createScript(form)
  ↓
后端 API (POST /api/scripts)
  ↓
  验证: 名称唯一性, 必填字段
  ↓
  创建 Script 数据库记录
  ↓
  创建 ScriptVersion 初始版本
  ↓
  创建脚本工作目录
  ↓
  返回脚本ID和信息
```

---

## 脚本执行流程

```
前端 (Scripts.vue)
  ↓
  1. 选择脚本
  2. 上传文件 (FileUpload.vue)
  3. 输入参数 (JSON格式)
  4. 点击"执行"
  ↓
后端 API (POST /api/scripts/<id>/execute)
  ↓
  1. 创建 Execution 记录 (pending)
  2. 为执行创建独立的执行空间
  3. 保存上传的文件到执行空间
  4. 启动后台线程
  ↓
后台执行线程 (services/executor.py)
  ↓
  1. 更新状态为 running
  2. 创建临时脚本文件到执行空间
  3. 安装依赖 (pip/npm)
  4. 构建命令: python script.py [参数]
  5. 在执行空间中执行脚本
  6. 实时输出到日志文件
  7. 等待进程完成
  8. 更新状态为 success/failed
  ↓
前端实时监听 (openLogStream)
  ↓
  使用SSE连接: GET /api/executions/<id>/logs/stream
  ↓
  实时显示日志, 当执行完成时显示状态
```

---

## 参数和文件传递

### 执行参数结构

**表单数据：**
```json
{
  "params": {
    "key1": "value1",
    "key2": "value2"
  },
  "files": [File, File]
}
```

**发送给API：**
```
FormData:
  - file0: File
  - file1: File
  - params: '{"key1":"value1"}'
```

**保存到数据库 (Execution.params)：**
```json
{
  "key1": "value1",
  "key2": "value2",
  "uploaded_files": [
    {
      "original_name": "input.csv",
      "saved_name": "input.csv",
      "path": "/absolute/path"
    }
  ]
}
```

### Python脚本参数接收

```python
import sys
import json
import os

# 命令行参数
for i in range(1, len(sys.argv), 2):
    if sys.argv[i].startswith('--'):
        key = sys.argv[i][2:]
        value = sys.argv[i+1] if i+1 < len(sys.argv) else None
        print(f"{key}: {value}")

# 文件列表
if '--files' in sys.argv:
    idx = sys.argv.index('--files')
    files = json.loads(sys.argv[idx+1])
    for filename in files:
        with open(filename) as f:
            print(f.read())
```

### JavaScript脚本参数接收

```javascript
// 环境变量
const param1 = process.env.PARAM_PARAM1
const files = JSON.parse(process.env.PARAM_FILES || '[]')

// 读取文件
const fs = require('fs')
files.forEach(filename => {
  const content = fs.readFileSync(filename, 'utf-8')
  console.log(content)
})
```

---

## API快速查询

### 脚本操作
```bash
# 获取所有脚本
curl http://localhost:5000/api/scripts

# 创建脚本
curl -X POST http://localhost:5000/api/scripts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test",
    "type": "python",
    "code": "print(\"hello\")",
    "description": "test script"
  }'

# 更新脚本
curl -X PUT http://localhost:5000/api/scripts/1 \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"updated\")"}'

# 执行脚本（不上传文件）
curl -X POST http://localhost:5000/api/scripts/1/execute \
  -H "Content-Type: multipart/form-data" \
  -F 'params={"key":"value"}'

# 执行脚本（上传文件）
curl -X POST http://localhost:5000/api/scripts/1/execute \
  -F 'file0=@input.csv' \
  -F 'params={"key":"value"}'
```

### 执行历史
```bash
# 获取执行列表
curl http://localhost:5000/api/executions

# 获取执行详情
curl http://localhost:5000/api/executions/1

# 获取日志内容
curl http://localhost:5000/api/executions/1/logs

# 流式获取日志（SSE）
curl http://localhost:5000/api/executions/1/logs/stream

# 获取执行空间的文件
curl http://localhost:5000/api/executions/1/files

# 查看/下载执行空间的文件
curl http://localhost:5000/api/executions/1/files/output.txt
```

---

## 版本管理

### 版本创建触发条件
- 创建脚本时 → 版本1
- 修改脚本代码 → 版本+1
- 修改脚本依赖 → 版本+1
- 修改脚本名称/描述 → 不创建新版本

### 版本回滚
```bash
# 回滚到指定版本
curl -X POST http://localhost:5000/api/scripts/1/rollback/2

# 效果：
# 1. 将脚本代码恢复到版本2
# 2. 创建新版本 (版本号+1)
# 3. 新版本描述为 "回滚到版本2"
```

---

## 定时任务

### Cron表达式示例

```
# 每天午夜执行
0 0 * * *

# 每小时执行
0 * * * *

# 每5分钟执行
*/5 * * * *

# 每周一早上8点执行
0 8 * * 1

# 工作日每天下午6点执行
0 18 * * 1-5
```

### 任务执行流程

```
Schedule定时触发
  ↓
后台调度器 (APScheduler)
  ↓
创建 Execution 记录
  ↓
执行脚本 (同步执行API)
  ↓
记录执行结果
  ↓
更新Schedule的 last_run 和 next_run
```

---

## 文件管理

### 文件上传位置
- **脚本执行时上传的文件** → `/execution_spaces/execution_{id}/`
- **通过文件管理上传的文件** → `/data/uploads/`

### 执行空间文件查看
```bash
# 获取执行空间的文件列表
curl http://localhost:5000/api/executions/1/files

# 响应示例：
{
  "files": [
    {
      "name": "input.csv",
      "path": "input.csv",
      "size": 1024,
      "modified_time": "2025-11-30T10:30:00",
      "is_text": true
    },
    {
      "name": "output.txt",
      "path": "output.txt",
      "size": 2048,
      "modified_time": "2025-11-30T10:31:00",
      "is_text": true
    }
  ],
  "total_size": 3072,
  "space_path": "/path/to/execution_spaces/execution_1"
}
```

### 执行空间文件预览/下载
```bash
# 预览文本文件
curl http://localhost:5000/api/executions/1/files/output.txt

# 下载文件
curl "http://localhost:5000/api/executions/1/files/output.txt?download=true" \
  -o output.txt
```

---

## 常见问题处理

### Q: 脚本代码存储在哪里？
A: 在SQLite数据库的 `scripts` 表的 `code` 字段中。每次执行时，代码会临时写入执行空间的脚本文件中。

### Q: 脚本执行时参数如何传递？
A: 
- Python: 命令行参数 `--key value`
- JavaScript: 环境变量 `PARAM_KEY=value`

### Q: 如何访问上传的文件？
A: 文件保存在执行空间中，脚本可以用相对路径或绝对路径访问。在Python中用`open(filename)`，在JavaScript中用`fs.readFileSync(filename)`。

### Q: 脚本超时时间是多少？
A: 配置中定义 `EXECUTION_TIMEOUT = 300` 秒（5分钟）。可在 `/backend/config.py` 中修改。

### Q: 执行日志保存多久？
A: 日志保存在 `/logs/` 目录中，不会自动删除。删除执行记录时会删除日志文件。

### Q: 可以同时执行多个脚本吗？
A: 可以。每次执行都在独立的后台线程中进行，不会相互阻塞。

### Q: 版本历史会一直保存吗？
A: 是的。删除脚本时会删除其所有版本和执行历史。

---

## 配置调整

### 修改脚本执行超时时间

**文件：** `/backend/config.py`

```python
# 改为600秒（10分钟）
EXECUTION_TIMEOUT = 600
```

### 修改跨域策略

**文件：** `/backend/config.py`

```python
# 允许来自其他域的请求
CORS_ORIGINS = ['http://localhost:5173', 'http://localhost:3000', 'http://example.com']
```

### 修改最大上传文件大小

**文件：** `/backend/config.py`

```python
# 改为100MB
MAX_CONTENT_LENGTH = 100 * 1024 * 1024
```

### 修改Python/Node.js路径

**文件：** `/backend/config.py`

```python
# 使用特定版本
PYTHON_EXECUTABLE = '/usr/bin/python3.9'
NODE_EXECUTABLE = '/usr/bin/node'
```

---

## 调试技巧

### 查看实时日志
```bash
# 后端
tail -f logs/execution_*.log

# 数据库查询
sqlite3 data/database.db "SELECT * FROM executions ORDER BY created_at DESC LIMIT 5;"
```

### 查看执行空间
```bash
# 列出某个执行的文件
ls -la execution_spaces/execution_1/

# 查看日志
cat logs/execution_1.log
```

### 前端调试
```javascript
// 在浏览器控制台查看API请求
// Network标签 → 查看请求和响应
// 查看SSE连接
fetch('/api/executions/1/logs/stream')
  .then(r => r.body.getReader())
  .then(reader => {
    while (true) {
      const {done, value} = await reader.read()
      if (done) break
      console.log(new TextDecoder().decode(value))
    }
  })
```

---

## 重要路径汇总

| 项目 | 路径 |
|------|------|
| 数据库 | `/data/database.db` |
| 执行日志 | `/logs/` |
| 执行空间 | `/execution_spaces/` |
| 上传文件 | `/data/uploads/` |
| 后端主程序 | `/backend/app.py` |
| 前端主程序 | `/frontend/src/main.js` |
| 配置文件 | `/backend/config.py` |
| 脚本API | `/backend/api/scripts.py` |
| 执行引擎 | `/backend/services/executor.py` |
