# 使用指南

## 快速开始

### 1. 启动后端服务

**Linux/Mac:**
```bash
./start-backend.sh
```

**Windows:**
```bash
start-backend.bat
```

后端服务将运行在: http://localhost:5000

### 2. 启动前端服务

**Linux/Mac:**
```bash
./start-frontend.sh
```

**Windows:**
```bash
start-frontend.bat
```

前端应用将运行在: http://localhost:5173

## 功能使用说明

### 1. 脚本管理

#### 创建Python脚本示例

```python
import sys
import json

# 脚本可以接收命令行参数
if len(sys.argv) > 1:
    print(f"接收到参数: {sys.argv[1:]}")

# 输出结果
print("Hello from Python script!")

# 可以读写文件
with open('data/uploads/output.txt', 'w') as f:
    f.write("Script executed successfully")
```

**依赖配置:**
```
requests,pandas,numpy
```

#### 创建JavaScript脚本示例

```javascript
// Node.js脚本可以通过环境变量接收参数
const param1 = process.env.PARAM_KEY1;
const param2 = process.env.PARAM_KEY2;

console.log('Hello from JavaScript!');
console.log('Parameters:', param1, param2);

// 可以使用Node.js的fs模块读写文件
const fs = require('fs');
fs.writeFileSync('data/uploads/js-output.txt', 'JS Script executed');
```

**依赖配置:**
```
axios,lodash,moment
```

### 2. 执行脚本

#### 执行时传递参数

在"执行脚本"对话框中,输入JSON格式的参数:

```json
{
  "key1": "value1",
  "key2": "value2",
  "count": 100
}
```

- Python脚本: 参数会作为命令行参数传递,格式为 `--key1 value1 --key2 value2`
- JavaScript脚本: 参数会作为环境变量传递,格式为 `PARAM_KEY1=value1 PARAM_KEY2=value2`

#### 查看执行日志

1. 点击"执行历史"菜单
2. 找到对应的执行记录
3. 点击"查看日志"按钮
4. 可以看到脚本的标准输出和错误信息

### 3. 定时任务

#### Cron表达式说明

格式: `分 时 日 月 周`

常用示例:
- `0 0 * * *` - 每天午夜12点执行
- `0 */2 * * *` - 每2小时执行一次
- `30 8 * * 1-5` - 周一到周五早上8:30执行
- `0 0 1 * *` - 每月1号午夜执行
- `*/5 * * * *` - 每5分钟执行一次

#### 创建定时任务

1. 点击"定时任务"菜单
2. 点击"新建任务"
3. 选择要执行的脚本
4. 输入Cron表达式
5. 可选:配置执行参数(JSON格式)
6. 保存后任务会自动按计划执行

### 4. 文件管理

#### 上传文件

1. 点击"文件管理"菜单
2. 点击"上传文件"按钮
3. 选择要上传的文件
4. 文件会保存在 `data/uploads/` 目录下

#### 脚本中访问文件

**Python示例:**
```python
# 读取上传的文件
with open('data/uploads/input.txt', 'r') as f:
    content = f.read()
    print(content)

# 写入文件供下载
with open('data/uploads/output.txt', 'w') as f:
    f.write('Processing result')
```

**JavaScript示例:**
```javascript
const fs = require('fs');

// 读取文件
const content = fs.readFileSync('data/uploads/input.txt', 'utf-8');
console.log(content);

// 写入文件
fs.writeFileSync('data/uploads/output.txt', 'Processing result');
```

### 5. 版本管理

#### 查看版本历史

1. 在脚本列表中点击"版本"按钮
2. 可以看到所有历史版本
3. 点击"查看"可以查看历史代码
4. 点击"回滚"可以恢复到指定版本

#### 版本自动管理

系统会在以下情况自动创建新版本:
- 修改脚本代码时
- 修改依赖配置时
- 手动回滚到历史版本时

## 高级用法

### 1. 脚本间协作

多个脚本可以通过文件系统共享数据:

**脚本A (数据生成器):**
```python
import json

data = {"status": "success", "count": 100}
with open('data/uploads/shared_data.json', 'w') as f:
    json.dump(data, f)
```

**脚本B (数据处理器):**
```python
import json

with open('data/uploads/shared_data.json', 'r') as f:
    data = json.load(f)
    print(f"Received data: {data}")
```

### 2. 使用外部依赖

在"依赖配置"中输入需要的包名,系统会自动安装:

**Python:**
- 包名用逗号分隔: `requests,pandas,numpy`
- 或使用JSON格式: `{"packages": ["requests", "pandas"]}`

**JavaScript:**
- 包名用逗号分隔: `axios,lodash,moment`
- 系统会使用 `npm install -g` 全局安装

### 3. 错误处理

脚本执行失败时:
1. 执行状态会标记为"失败"
2. 在执行历史中点击"查看日志"可以看到错误信息
3. 检查脚本代码和依赖配置
4. 修复后重新执行

## 注意事项

1. **脚本超时**: 默认脚本执行超时时间为300秒(5分钟),超时会被强制终止
2. **文件路径**: 脚本中使用相对路径访问文件,相对于项目根目录
3. **依赖安装**: 首次使用新依赖时可能需要较长时间安装
4. **并发执行**: 系统支持多个脚本同时执行
5. **日志大小**: 执行日志会被限制大小,避免占用过多磁盘空间

## 故障排查

### 后端无法启动

1. 检查Python版本 (需要Python 3.7+)
2. 检查依赖是否正确安装: `pip list`
3. 查看终端错误信息

### 前端无法启动

1. 检查Node.js版本 (需要Node.js 16+)
2. 删除 `node_modules` 重新安装: `rm -rf node_modules && npm install`
3. 查看终端错误信息

### 脚本执行失败

1. 查看执行日志中的错误信息
2. 检查依赖是否正确配置
3. 检查脚本语法是否正确
4. 确认文件路径是否正确

### 定时任务未执行

1. 确认任务状态为"启用"
2. 检查Cron表达式是否正确
3. 查看后端日志是否有错误信息
4. 查看"执行历史"确认任务是否被触发

## API接口文档

系统提供RESTful API,可以通过编程方式调用:

**基础URL:** `http://localhost:5000/api`

**认证:** 当前版本无需认证

详细API文档请参考 README.md 中的API部分。
