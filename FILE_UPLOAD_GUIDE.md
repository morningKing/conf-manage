# 文件上传和实时日志功能使用指南

## 新增功能

### 1. 文件上传支持 📎

脚本执行时现在支持上传文件作为参数，有以下特性：

- ✅ **拖拽上传**: 直接拖拽文件到上传区域
- ✅ **点击上传**: 点击上传区域选择文件
- ✅ **多文件支持**: 可以同时上传多个文件
- ✅ **文件预览**: 显示已选择的文件列表和大小
- ✅ **文件管理**: 可以单独删除或清空所有文件

### 2. 实时日志查看 📊

脚本执行后自动打开实时日志窗口：

- ✅ **实时更新**: 使用 Server-Sent Events (SSE) 技术实时推送日志
- ✅ **自动滚动**: 日志自动滚动到最新内容
- ✅ **状态显示**: 实时显示执行状态（等待中、运行中、成功、失败）
- ✅ **错误高亮**: 错误信息单独显示，红色高亮
- ✅ **终端样式**: 黑色背景的终端风格，易于阅读

## 使用步骤

### 步骤1：创建脚本

在脚本列表页面，点击"新建脚本"，创建一个支持文件处理的脚本。

**Python 脚本示例：**

```python
import argparse
import json
import os

parser = argparse.ArgumentParser()
parser.add_argument('--files', type=str, help='上传的文件路径(JSON格式)')
args = parser.parse_args()

# 解析文件路径
if args.files:
    file_paths = json.loads(args.files)
    for filepath in file_paths:
        print(f"处理文件: {filepath}")
        # 读取并处理文件
        with open(filepath, 'r') as f:
            content = f.read()
            print(f"文件大小: {len(content)} 字节")
```

**JavaScript 脚本示例：**

```javascript
// 从环境变量获取文件路径
const filesJson = process.env.PARAM_FILES;

if (filesJson) {
    const filePaths = JSON.parse(filesJson);
    const fs = require('fs');

    filePaths.forEach(filepath => {
        console.log(`处理文件: ${filepath}`);
        const content = fs.readFileSync(filepath, 'utf8');
        console.log(`文件大小: ${content.length} 字节`);
    });
}
```

### 步骤2：执行脚本

1. 在脚本列表中点击要执行的脚本的"执行"按钮
2. 在执行对话框中：
   - **上传文件**: 拖拽或点击上传区域选择文件
   - **其他参数**: （可选）输入其他JSON格式的参数
3. 点击"执行"按钮

### 步骤3：查看实时日志

执行后会自动打开实时日志窗口：

- 顶部显示当前执行状态
- 中间区域实时显示日志输出
- 底部显示错误信息（如果有）
- 脚本执行完成后状态自动更新

## 文件路径获取方式

### Python 脚本

上传的文件会通过 `--files` 参数传递，格式为 JSON 数组：

```python
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument('--files', type=str)
args = parser.parse_args()

file_paths = json.loads(args.files)  # 解析为列表
# file_paths = ['/path/to/file1.txt', '/path/to/file2.csv']

for filepath in file_paths:
    # 处理每个文件
    pass
```

### JavaScript 脚本

上传的文件会通过 `PARAM_FILES` 环境变量传递：

```javascript
const filesJson = process.env.PARAM_FILES;
const filePaths = JSON.parse(filesJson);  // 解析为数组
// filePaths = ['/path/to/file1.txt', '/path/to/file2.csv']

filePaths.forEach(filepath => {
    // 处理每个文件
});
```

## 示例脚本

系统提供了一个完整的示例脚本：`example_scripts/file_processor.py`

这个脚本演示了：
- 接收上传的文件
- 显示文件信息
- 统计文本文件行数
- 计算文件 MD5 校验和

**使用方法：**

1. 在系统中创建新脚本
2. 复制 `example_scripts/file_processor.py` 的内容
3. 执行时上传一些文件
4. 可以添加参数 `{"action": "count"}` 来统计行数
5. 或使用 `{"action": "checksum"}` 来计算 MD5

## API 变化

### 后端 API

**执行脚本端点** (已更新)
```
POST /api/scripts/{id}/execute
Content-Type: multipart/form-data

参数:
- file0, file1, ... : 上传的文件
- params (可选): JSON格式的其他参数
```

**实时日志流端点** (新增)
```
GET /api/executions/{id}/logs/stream
Response: text/event-stream (SSE)

事件数据:
- type: 'log' - 日志内容
- type: 'status' - 执行状态更新
```

### 前端 API

**执行脚本 (新增)**
```javascript
import { executeScriptWithFiles } from '@/api'

const formData = new FormData()
formData.append('file0', file1)
formData.append('file1', file2)
formData.append('params', JSON.stringify({ key: 'value' }))

await executeScriptWithFiles(scriptId, formData)
```

## 技术实现

### 文件上传
- 前端使用 HTML5 拖拽 API
- FormData 封装文件和参数
- 后端使用 Flask 的 request.files 接收
- 文件保存到 `data/uploads/` 目录

### 实时日志
- Server-Sent Events (SSE) 推送日志
- EventSource API 接收实时数据
- 0.5秒轮询间隔，低延迟
- 自动重连和错误处理

### 文件路径传递
- Python: 通过命令行参数 `--files`
- JavaScript: 通过环境变量 `PARAM_FILES`
- 统一使用 JSON 数组格式

## 注意事项

⚠️ **重要提示：**

1. **文件大小限制**: 默认最大 16MB（可在配置中修改）
2. **文件安全**: 上传的文件会自动添加时间戳避免冲突
3. **文件清理**: 执行完成后文件会保留在 uploads 目录，需要定期清理
4. **日志连接**: 关闭日志窗口会断开 SSE 连接
5. **路径格式**: 脚本接收到的是绝对路径

## 故障排除

**问题1: 文件上传失败**
- 检查文件大小是否超过限制
- 确认后端服务正常运行
- 查看浏览器控制台错误信息

**问题2: 实时日志不显示**
- 确认脚本有输出内容
- 检查浏览器是否支持 EventSource
- 查看网络请求是否建立 SSE 连接

**问题3: 脚本无法读取文件**
- 确认脚本正确解析 `--files` 参数（Python）
- 确认脚本正确读取 `PARAM_FILES` 环境变量（JavaScript）
- 检查文件路径是否正确

## 更多信息

- 后端实现: `backend/api/executions.py`
- 前端组件: `frontend/src/components/FileUpload.vue`
- 执行引擎: `backend/services/executor.py`
- 示例脚本: `example_scripts/file_processor.py`
