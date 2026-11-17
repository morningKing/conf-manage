# 脚本工具管理系统 - 代码结构分析报告

## 一、项目概览

这是一个**Vue3 + Flask**的前后端分离的脚本管理和执行系统，支持Python和JavaScript脚本的创建、编辑、执行、版本管理和定时调度。

### 技术栈

**前端：**
- Vue 3（框架）
- Vue Router（路由）
- Axios（HTTP客户端）
- Element Plus（UI组件库）
- CodeMirror（代码编辑器）
- Vite（构建工具）

**后端：**
- Flask（Web框架）
- SQLAlchemy（ORM）
- SQLite（数据库）
- APScheduler（定时任务调度）
- Flask-CORS（跨域支持）

---

## 二、数据库模型定义

### 脚本存储方式

脚本存储在SQLite数据库中，而不是文件系统。这是一个重要的设计点。

#### 2.1 Script 模型（脚本表）
**文件路径：** `/mnt/e/Code/ccr/conf-manage/backend/models/script.py`

```python
class Script(db.Model):
    __tablename__ = 'scripts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # 脚本名称（唯一）
    description = db.Column(db.Text)                               # 描述
    type = db.Column(db.String(20), nullable=False)               # 'python' 或 'javascript'
    code = db.Column(db.Text, nullable=False)                     # 脚本代码内容
    dependencies = db.Column(db.Text)                             # JSON格式的依赖配置
    version = db.Column(db.Integer, default=1)                    # 当前版本号
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系定义
    versions = db.relationship('ScriptVersion', ...)    # 版本关系
    executions = db.relationship('Execution', ...)      # 执行历史关系
    schedules = db.relationship('Schedule', ...)        # 定时任务关系
```

**关键点：**
- 脚本代码直接存储在数据库的 `code` 字段中
- 依赖配置为 JSON 格式，如：`{"packages": ["requests", "pandas"]}`
- 版本号自动递增，用于版本管理

#### 2.2 ScriptVersion 模型（版本表）
**文件路径：** `/mnt/e/Code/ccr/conf-manage/backend/models/script.py`

```python
class ScriptVersion(db.Model):
    __tablename__ = 'script_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    script_id = db.Column(db.Integer, db.ForeignKey('scripts.id'), nullable=False)
    version = db.Column(db.Integer, nullable=False)               # 版本号
    code = db.Column(db.Text, nullable=False)                     # 该版本的代码
    dependencies = db.Column(db.Text)                             # 该版本的依赖
    description = db.Column(db.Text)                              # 版本描述
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**关键点：**
- 每次编辑脚本代码或依赖时，自动创建新版本
- 支持版本回滚功能

#### 2.3 Execution 模型（执行记录表）
**文件路径：** `/mnt/e/Code/ccr/conf-manage/backend/models/execution.py`

```python
class Execution(db.Model):
    __tablename__ = 'executions'
    
    id = db.Column(db.Integer, primary_key=True)
    script_id = db.Column(db.Integer, db.ForeignKey('scripts.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)              # pending/running/success/failed
    params = db.Column(db.Text)                                    # JSON格式的执行参数
    output = db.Column(db.Text)                                    # 执行输出
    error = db.Column(db.Text)                                     # 错误信息
    log_file = db.Column(db.String(255))                          # 日志文件路径
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**关键点：**
- 状态有4种：pending(待执行), running(运行中), success(成功), failed(失败)
- 参数以JSON格式存储，可包含上传文件信息
- 日志以文件形式存储在文件系统中

#### 2.4 Schedule 模型（定时任务表）
**文件路径：** `/mnt/e/Code/ccr/conf-manage/backend/models/schedule.py`

```python
class Schedule(db.Model):
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    script_id = db.Column(db.Integer, db.ForeignKey('scripts.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)               # 任务名称
    description = db.Column(db.Text)
    cron = db.Column(db.String(100), nullable=False)              # Cron表达式
    params = db.Column(db.Text)                                    # 执行参数（JSON）
    enabled = db.Column(db.Boolean, default=True)                  # 是否启用
    last_run = db.Column(db.DateTime)                             # 上次执行时间
    next_run = db.Column(db.DateTime)                             # 下次执行时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## 三、脚本创建/编辑流程

### 3.1 前端表单结构

**文件路径：** `/mnt/e/Code/ccr/conf-manage/frontend/src/views/Scripts.vue`

**创建/编辑对话框的表单字段：**

```vue
<el-form :model="form" label-width="100px">
  <el-form-item label="脚本名称">
    <el-input v-model="form.name" />
  </el-form-item>
  
  <el-form-item label="脚本类型">
    <el-select v-model="form.type">
      <el-option label="Python" value="python" />
      <el-option label="JavaScript" value="javascript" />
    </el-select>
  </el-form-item>
  
  <el-form-item label="描述">
    <el-input v-model="form.description" type="textarea" rows="2" />
  </el-form-item>
  
  <el-form-item label="依赖配置">
    <el-input 
      v-model="form.dependencies" 
      type="textarea" 
      rows="2"
      placeholder="多个依赖用逗号分隔,例如: requests,pandas"
    />
  </el-form-item>
  
  <el-form-item label="脚本代码">
    <CodeEditor 
      v-model="form.code" 
      :language="form.type"
      height="500px" 
      theme="dark"
    />
  </el-form-item>
</el-form>
```

**表单数据结构：**
```javascript
form = {
  name: '',           // 脚本名称
  type: 'python',     // python 或 javascript
  description: '',    // 描述
  code: '',           // 脚本代码
  dependencies: ''    // 依赖列表，逗号分隔
}
```

### 3.2 创建脚本的API调用

**文件路径：** `/mnt/e/Code/ccr/conf-manage/frontend/src/api/index.js`

```javascript
export const createScript = (data) => request.post('/scripts', data)
export const updateScript = (id, data) => request.put(`/scripts/${id}`, data)
```

**前端调用逻辑（Scripts.vue）：**

```javascript
const handleSave = async () => {
  try {
    if (currentScript.value) {
      await updateScript(currentScript.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await createScript(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadScripts()
  } catch (error) {
    console.error(error)
  }
}
```

### 3.3 后端脚本创建API

**文件路径：** `/mnt/e/Code/ccr/conf-manage/backend/api/scripts.py`

```python
@api_bp.route('/scripts', methods=['POST'])
def create_script():
    """创建脚本"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name') or not data.get('type') or not data.get('code'):
            return jsonify({'code': 1, 'message': '缺少必填字段'}), 400
        
        # 检查名称是否重复
        if Script.query.filter_by(name=data['name']).first():
            return jsonify({'code': 1, 'message': '脚本名称已存在'}), 400
        
        # 创建脚本
        script = Script(
            name=data['name'],
            description=data.get('description', ''),
            type=data['type'],
            code=data['code'],
            dependencies=data.get('dependencies', ''),
            version=1
        )
        db.session.add(script)
        db.session.flush()  # 获取脚本ID
        
        # 为脚本创建工作目录
        workspace_path = Config.ensure_script_workspace(script.id)
        
        # 创建第一个版本记录
        version = ScriptVersion(
            script_id=script.id,
            version=1,
            code=data['code'],
            dependencies=data.get('dependencies', ''),
            description='初始版本'
        )
        db.session.add(version)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': script.to_dict(),
            'message': '脚本创建成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500
```

### 3.4 脚本编辑API

**文件路径：** `/mnt/e/Code/ccr/conf-manage/backend/api/scripts.py`

```python
@api_bp.route('/scripts/<int:script_id>', methods=['PUT'])
def update_script(script_id):
    """更新脚本"""
    try:
        script = Script.query.get_or_404(script_id)
        data = request.get_json()
        
        # 检查代码或依赖是否有变化
        code_changed = 'code' in data and data['code'] != script.code
        dependencies_changed = 'dependencies' in data and data['dependencies'] != script.dependencies
        
        # 更新脚本信息
        if 'name' in data:
            if data['name'] != script.name and Script.query.filter_by(name=data['name']).first():
                return jsonify({'code': 1, 'message': '脚本名称已存在'}), 400
            script.name = data['name']
        
        if 'description' in data:
            script.description = data['description']
        if 'type' in data:
            script.type = data['type']
        if 'code' in data:
            script.code = data['code']
        if 'dependencies' in data:
            script.dependencies = data['dependencies']
        
        script.updated_at = datetime.utcnow()
        
        # 如果代码或依赖有变化，创建新版本
        if code_changed or dependencies_changed:
            script.version += 1
            version = ScriptVersion(
                script_id=script.id,
                version=script.version,
                code=script.code,
                dependencies=script.dependencies,
                description=data.get('version_description', f'版本 {script.version}')
            )
            db.session.add(version)
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': script.to_dict(),
            'message': '脚本更新成功'
        })
```

---

## 四、脚本执行流程

### 4.1 执行页面结构

**文件路径：** `/mnt/e/Code/ccr/conf-manage/frontend/src/views/Scripts.vue`

**执行对话框：**

```vue
<el-dialog v-model="executeVisible" title="执行脚本" width="700px">
  <el-form :model="executeForm" label-width="100px">
    <el-form-item label="脚本名称">
      <el-input :value="currentScript?.name" disabled />
    </el-form-item>

    <el-form-item label="上传文件">
      <FileUpload v-model="uploadFiles" />
    </el-form-item>

    <el-form-item label="其他参数">
      <el-input
        v-model="executeParams"
        type="textarea"
        rows="3"
        placeholder='可选：输入JSON格式参数,例如: {"key": "value"}'
      />
    </el-form-item>
  </el-form>
  <template #footer>
    <el-button @click="executeVisible = false">取消</el-button>
    <el-button type="primary" @click="handleExecuteConfirm">执行</el-button>
  </template>
</el-dialog>
```

### 4.2 前端执行流程

```javascript
const handleExecuteConfirm = async () => {
  try {
    const formData = new FormData()
    
    // 添加上传的文件
    uploadFiles.value.forEach((file, index) => {
      formData.append(`file${index}`, file)
    })
    
    // 添加其他参数（JSON格式）
    if (executeParams.value.trim()) {
      const params = JSON.parse(executeParams.value)
      formData.append('params', JSON.stringify(params))
    }
    
    // 调用执行API
    const res = await executeScriptWithFiles(currentScript.value.id, formData)
    const executionId = res.data.id
    
    ElMessage.success('脚本执行已启动')
    executeVisible.value = false
    
    // 打开实时日志窗口
    openLogStream(executionId)  // 使用SSE获取实时日志
  } catch (error) {
    ElMessage.error('参数格式错误或执行失败: ' + error.message)
  }
}
```

**文件上传组件：**
**路径：** `/mnt/e/Code/ccr/conf-manage/frontend/src/components/FileUpload.vue`

```vue
<template>
  <div class="file-upload">
    <!-- 拖拽上传区域 -->
    <div class="upload-area" @drop.prevent="handleDrop" @dragover.prevent>
      <input ref="fileInput" type="file" multiple style="display: none" @change="handleFileSelect" />
      <div class="upload-icon"><el-icon><upload-filled /></el-icon></div>
      <div class="upload-text">
        <p>点击或拖拽文件到此处上传</p>
        <p>支持多文件上传</p>
      </div>
    </div>
    
    <!-- 已选文件列表 -->
    <div v-if="fileList.length > 0" class="file-list">
      <div v-for="(file, index) in fileList" :key="index" class="file-item">
        <span>{{ file.name }}</span>
        <span>{{ formatFileSize(file.size) }}</span>
        <el-button link type="danger" @click="removeFile(index)">删除</el-button>
      </div>
    </div>
  </div>
</template>
```

### 4.3 后端执行API

**文件路径：** `/mnt/e/Code/ccr/conf-manage/backend/api/executions.py`

```python
@api_bp.route('/scripts/<int:script_id>/execute', methods=['POST'])
def execute_script_api(script_id):
    """执行脚本"""
    try:
        script = Script.query.get_or_404(script_id)
        
        # 获取参数
        params = {}
        if request.form.get('params'):
            params = json.loads(request.form.get('params'))
        
        # 创建执行记录
        execution = Execution(
            script_id=script_id,
            status='pending',
            params=json.dumps(params) if params else None
        )
        db.session.add(execution)
        db.session.commit()
        
        # 处理文件上传 - 直接保存到执行空间
        files = []
        if request.files:
            # 为当前执行创建独立的执行空间
            execution_space = Config.ensure_execution_space(execution.id)
            
            for file_key in request.files:
                file = request.files[file_key]
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(execution_space, filename)
                    file.save(filepath)
                    files.append({
                        'original_name': filename,
                        'saved_name': filename,
                        'path': os.path.abspath(filepath)
                    })
        
        # 将文件信息添加到参数中
        if files:
            params['uploaded_files'] = files
            execution.params = json.dumps(params)
            db.session.commit()
        
        # 异步执行脚本（后台线程）
        from threading import Thread
        thread = Thread(target=lambda: execute_script(execution.id))
        thread.start()
        
        return jsonify({
            'code': 0,
            'data': execution.to_dict(),
            'message': '脚本执行已启动'
        })
```

### 4.4 脚本执行引擎

**文件路径：** `/mnt/e/Code/ccr/conf-manage/backend/services/executor.py`

```python
def execute_script(execution_id):
    """执行脚本"""
    try:
        # 获取执行记录和脚本
        execution = Execution.query.get(execution_id)
        script = Script.query.get(execution.script_id)
        
        # 更新状态为运行中
        execution.status = 'running'
        execution.start_time = datetime.utcnow()
        db.session.commit()
        
        # 解析参数（包含上传的文件信息）
        params = {}
        uploaded_files = []
        if execution.params:
            try:
                params = json.loads(execution.params)
                if 'uploaded_files' in params:
                    uploaded_files = params.pop('uploaded_files')
            except:
                pass
        
        # 确保执行空间存在
        execution_space = Config.ensure_execution_space(execution_id)
        
        # 创建临时脚本文件（放在执行空间中）
        script_ext = '.py' if script.type == 'python' else '.js'
        script_filename = f'script_{execution_id}{script_ext}'
        script_file = os.path.join(execution_space, script_filename)
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script.code)
        
        # 创建日志文件
        log_file = os.path.join(Config.LOGS_DIR, f'execution_{execution_id}.log')
        execution.log_file = log_file
        db.session.commit()
        
        try:
            # 安装依赖
            if script.dependencies:
                if script.type == 'python':
                    install_dependencies_python(script.dependencies)
                elif script.type == 'javascript':
                    install_dependencies_node(script.dependencies)
            
            # 构建执行命令
            if script.type == 'python':
                cmd = [Config.PYTHON_EXECUTABLE, script_filename]
                # 添加参数
                for key, value in params.items():
                    cmd.extend([f'--{key}', str(value)])
                
                # 添加文件路径参数
                if uploaded_files:
                    file_names = [f['name'] for f in uploaded_files]
                    cmd.extend(['--files', json.dumps(file_names)])
            
            elif script.type == 'javascript':
                cmd = [Config.NODE_EXECUTABLE, script_filename]
                # 参数作为环境变量
                env = os.environ.copy()
                for key, value in params.items():
                    env[f'PARAM_{key.upper()}'] = str(value)
                
                if uploaded_files:
                    file_names = [f['name'] for f in uploaded_files]
                    env['PARAM_FILES'] = json.dumps(file_names)
            
            # 执行脚本（在执行空间中执行）
            with open(log_file, 'w', encoding='utf-8') as log_f:
                process = subprocess.Popen(
                    cmd,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    env=env if script.type == 'javascript' else None,
                    cwd=execution_space  # 在执行空间中执行
                )
                
                # 等待执行完成（带超时）
                try:
                    process.wait(timeout=Config.EXECUTION_TIMEOUT)  # 默认300秒
                except subprocess.TimeoutExpired:
                    process.kill()
                    raise Exception('脚本执行超时')
            
            # 读取输出
            with open(log_file, 'r', encoding='utf-8') as log_f:
                output = log_f.read()
            
            # 更新执行结果
            if process.returncode == 0:
                execution.status = 'success'
                execution.output = output[:10000]  # 限制输出长度
            else:
                execution.status = 'failed'
                execution.error = output[-5000:]  # 保存最后的错误信息
        
        except Exception as e:
            execution.status = 'failed'
            execution.error = str(e)
        
        finally:
            execution.end_time = datetime.utcnow()
            db.session.commit()
    
    except Exception as e:
        print(f'执行脚本时发生错误: {str(e)}')
        try:
            execution.status = 'failed'
            execution.error = str(e)
            execution.end_time = datetime.utcnow()
            db.session.commit()
        except:
            pass
```

**依赖安装：**

```python
def install_dependencies_python(dependencies):
    """安装Python依赖"""
    try:
        deps = json.loads(dependencies) if isinstance(dependencies, str) else dependencies
        if isinstance(deps, dict):
            deps = deps.get('packages', [])
        elif isinstance(deps, str):
            deps = [d.strip() for d in deps.split(',') if d.strip()]
        
        if deps:
            cmd = [Config.PYTHON_EXECUTABLE, '-m', 'pip', 'install'] + deps
            subprocess.run(cmd, check=True, capture_output=True)
    except Exception as e:
        print(f'安装Python依赖失败: {str(e)}')

def install_dependencies_node(dependencies):
    """安装Node.js依赖"""
    try:
        deps = json.loads(dependencies) if isinstance(dependencies, str) else dependencies
        if isinstance(deps, dict):
            deps = deps.get('packages', [])
        elif isinstance(deps, str):
            deps = [d.strip() for d in deps.split(',') if d.strip()]
        
        if deps:
            for dep in deps:
                cmd = ['npm', 'install', '-g', dep]
                subprocess.run(cmd, check=True, capture_output=True)
    except Exception as e:
        print(f'安装Node.js依赖失败: {str(e)}')
```

### 4.5 实时日志流（SSE）

**前端实时日志窗口：**

```javascript
const openLogStream = (executionId) => {
  // 重置日志状态
  realTimeLogs.value = ''
  logError.value = ''
  logStatus.value = 'pending'
  logVisible.value = true
  
  // 创建 SSE 连接
  const apiUrl = import.meta.env.VITE_API_URL || '/api'
  eventSource = new EventSource(`${apiUrl}/executions/${executionId}/logs/stream`)
  
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      
      if (data.type === 'log') {
        // 追加日志内容
        realTimeLogs.value += data.content
        // 自动滚动到底部
        nextTick(() => {
          if (logContainer.value) {
            logContainer.value.scrollTop = logContainer.value.scrollHeight
          }
        })
      } else if (data.type === 'status') {
        // 更新状态
        logStatus.value = data.status
        if (data.error) {
          logError.value = data.error
        }
        // 关闭连接
        eventSource.close()
        eventSource = null
      }
    } catch (error) {
      console.error('解析日志数据失败:', error)
    }
  }
}
```

**后端SSE端点：**

```python
@api_bp.route('/executions/<int:execution_id>/logs/stream', methods=['GET'])
def stream_execution_logs(execution_id):
    """实时流式传输执行日志 (Server-Sent Events)"""
    def generate():
        execution = Execution.query.get(execution_id)
        if not execution:
            yield f"data: {json.dumps({'error': '执行记录不存在'})}\n\n"
            return
        
        # 等待日志文件创建
        max_wait = 10  # 最多等待10秒
        waited = 0
        while not execution.log_file or not os.path.exists(execution.log_file):
            if waited >= max_wait:
                yield f"data: {json.dumps({'error': '日志文件未创建'})}\n\n"
                return
            time.sleep(0.5)
            waited += 0.5
            db.session.refresh(execution)
        
        # 流式读取日志
        with open(execution.log_file, 'r', encoding='utf-8') as f:
            # 发送已有内容
            content = f.read()
            if content:
                yield f"data: {json.dumps({'type': 'log', 'content': content})}\n\n"
            
            # 持续读取新内容
            while True:
                db.session.refresh(execution)
                
                # 检查执行状态
                if execution.status in ['success', 'failed']:
                    # 读取剩余内容
                    new_content = f.read()
                    if new_content:
                        yield f"data: {json.dumps({'type': 'log', 'content': new_content})}\n\n"
                    
                    # 发送完成信息
                    yield f"data: {json.dumps({'type': 'status', 'status': execution.status, 'error': execution.error or ''})}\n\n"
                    break
                
                # 读取新内容
                new_content = f.read()
                if new_content:
                    yield f"data: {json.dumps({'type': 'log', 'content': new_content})}\n\n"
                
                time.sleep(0.5)  # 每0.5秒检查一次
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )
```

---

## 五、文件系统结构

### 5.1 目录配置

**文件路径：** `/mnt/e/Code/ccr/conf-manage/backend/config.py`

```python
class Config:
    # 脚本存储路径
    SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')  # 废弃，不再使用
    
    # 脚本工作目录根路径（废弃，保留用于兼容）
    WORKSPACES_DIR = os.path.join(BASE_DIR, 'workspaces')
    
    # 执行空间根路径（每次执行独立的工作目录）
    EXECUTION_SPACES_DIR = os.path.join(BASE_DIR, 'execution_spaces')
    # 结构: execution_spaces/execution_{execution_id}/
    
    # 日志存储路径
    LOGS_DIR = os.path.join(BASE_DIR, 'logs')
    # 文件: logs/execution_{execution_id}.log
    
    # 数据文件路径
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    # 子目录: data/uploads/, data/database.db
```

### 5.2 脚本执行时的目录结构

```
project/
├── data/
│   ├── database.db              # SQLite数据库（脚本代码存储在这里）
│   └── uploads/                 # 前端上传的文件
├── execution_spaces/
│   ├── execution_1/
│   │   ├── script_1.py          # 待执行的脚本代码
│   │   ├── input_file.csv       # 上传的输入文件
│   │   └── output.txt           # 脚本执行生成的输出文件
│   └── execution_2/
│       └── ...
├── logs/
│   ├── execution_1.log          # 执行日志
│   ├── execution_2.log
│   └── ...
└── workspaces/                  # 旧目录，保留用于兼容
```

**关键设计点：**
- 每次执行都创建一个独立的执行空间（execution_spaces/execution_{id}/）
- 脚本代码临时写入执行空间的脚本文件中
- 上传的文件直接保存到执行空间中
- 日志文件单独存储在logs目录中
- 删除执行记录时，整个执行空间会被删除

---

## 六、前端组件架构

### 6.1 路由结构

**文件路径：** `/mnt/e/Code/ccr/conf-manage/frontend/src/router/index.js`

```
/           - 脚本管理 (Scripts.vue)
/executions - 执行历史 (Executions.vue)
/schedules  - 定时任务 (Schedules.vue)
/files      - 文件管理 (Files.vue)
```

### 6.2 核心组件

#### CodeEditor.vue - 代码编辑器
**文件路径：** `/mnt/e/Code/ccr/conf-manage/frontend/src/components/CodeEditor.vue`

基于CodeMirror的代码编辑组件：
- 支持Python和JavaScript的语法高亮
- 支持暗色和亮色主题
- 支持只读模式
- 自动换行和行号显示

**Props：**
```javascript
{
  modelValue: String,              // 代码内容
  language: 'python' | 'javascript' // 语言
  readonly: Boolean,               // 是否只读
  height: String,                  // 高度（如'500px'）
  theme: 'light' | 'dark'         // 主题
}
```

#### FileUpload.vue - 文件上传组件
**文件路径：** `/mnt/e/Code/ccr/conf-manage/frontend/src/components/FileUpload.vue`

支持拖拽和点击的文件上传组件：
- 支持多文件选择
- 支持拖拽上传
- 显示文件列表和大小

#### ExecutionFiles.vue - 执行空间文件查看器
**文件路径：** `/mnt/e/Code/ccr/conf-manage/frontend/src/components/ExecutionFiles.vue`

查看执行空间中的文件：
- 列表查看
- 文本文件预览
- 文件下载
- 文件删除

### 6.3 主要视图组件

#### Scripts.vue - 脚本管理
操作：
- 创建脚本（表单对话框）
- 编辑脚本（表单对话框）
- 删除脚本（确认对话框）
- 执行脚本（参数和文件上传对话框）
- 查看版本历史（版本列表和代码查看）
- 版本回滚

#### Executions.vue - 执行历史
操作：
- 列表展示（分页）
- 查看日志（读取日志文件）
- 查看执行空间的文件
- 删除执行记录

#### Schedules.vue - 定时任务
操作：
- 创建任务
- 编辑任务
- 删除任务
- 启用/禁用任务
- 立即运行任务

#### Files.vue - 文件管理
操作：
- 文件列表
- 上传文件
- 创建文件夹
- 删除文件

---

## 七、API端点总结

### 脚本管理
```
GET    /api/scripts                              # 获取脚本列表
GET    /api/scripts/<id>                         # 获取脚本详情
POST   /api/scripts                              # 创建脚本
PUT    /api/scripts/<id>                         # 更新脚本
DELETE /api/scripts/<id>                         # 删除脚本
GET    /api/scripts/<id>/versions                # 获取版本列表
GET    /api/scripts/<id>/versions/<version_id>   # 获取指定版本
POST   /api/scripts/<id>/rollback/<version_num>  # 回滚版本
```

### 脚本执行
```
POST   /api/scripts/<id>/execute                 # 执行脚本（支持文件上传）
GET    /api/executions                           # 获取执行历史
GET    /api/executions/<id>                      # 获取执行详情
GET    /api/executions/<id>/logs                 # 获取执行日志
GET    /api/executions/<id>/logs/stream          # 获取实时日志（SSE）
DELETE /api/executions/<id>                      # 删除执行记录
GET    /api/executions/<id>/files                # 获取执行空间的文件列表
GET    /api/executions/<id>/files/<path>         # 获取执行空间的文件内容
```

### 定时任务
```
GET    /api/schedules                            # 获取任务列表
GET    /api/schedules/<id>                       # 获取任务详情
POST   /api/schedules                            # 创建任务
PUT    /api/schedules/<id>                       # 更新任务
DELETE /api/schedules/<id>                       # 删除任务
POST   /api/schedules/<id>/toggle                # 启用/禁用任务
POST   /api/schedules/<id>/run                   # 立即运行任务
```

### 文件管理
```
GET    /api/files                                # 获取文件列表
POST   /api/files/upload                         # 上传文件
GET    /api/files/download                       # 下载文件
DELETE /api/files/delete                         # 删除文件
POST   /api/files/create-folder                  # 创建文件夹
```

---

## 八、执行参数格式

### Python脚本参数传递方式

**通过命令行参数传递：**
```python
# 脚本会接收形如：script.py --param1 value1 --param2 value2
import sys
import json

# 获取参数
for i, arg in enumerate(sys.argv):
    if arg == '--files':
        files = json.loads(sys.argv[i + 1])
```

**文件处理示例：**
```python
import os
import json

# 获取执行空间中的文件
files = json.loads(os.environ.get('files', '[]'))
for filename in files:
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            content = f.read()
```

### JavaScript脚本参数传递方式

**通过环境变量传递：**
```javascript
// 环境变量形式：PARAM_KEY=value
const param1 = process.env.PARAM_PARAM1
const files = JSON.parse(process.env.PARAM_FILES || '[]')
```

**文件处理示例：**
```javascript
const fs = require('fs')

// 读取执行空间中的文件
const files = JSON.parse(process.env.PARAM_FILES || '[]')
files.forEach(filename => {
  if (fs.existsSync(filename)) {
    const content = fs.readFileSync(filename, 'utf-8')
    console.log(content)
  }
})
```

---

## 九、关键代码位置总结

| 功能 | 文件路径 |
|------|---------|
| 脚本模型定义 | `/mnt/e/Code/ccr/conf-manage/backend/models/script.py` |
| 执行模型定义 | `/mnt/e/Code/ccr/conf-manage/backend/models/execution.py` |
| 任务模型定义 | `/mnt/e/Code/ccr/conf-manage/backend/models/schedule.py` |
| 脚本API | `/mnt/e/Code/ccr/conf-manage/backend/api/scripts.py` |
| 执行API | `/mnt/e/Code/ccr/conf-manage/backend/api/executions.py` |
| 任务API | `/mnt/e/Code/ccr/conf-manage/backend/api/schedules.py` |
| 文件API | `/mnt/e/Code/ccr/conf-manage/backend/api/files.py` |
| 执行引擎 | `/mnt/e/Code/ccr/conf-manage/backend/services/executor.py` |
| 任务调度器 | `/mnt/e/Code/ccr/conf-manage/backend/services/scheduler.py` |
| 配置文件 | `/mnt/e/Code/ccr/conf-manage/backend/config.py` |
| Flask应用入口 | `/mnt/e/Code/ccr/conf-manage/backend/app.py` |
| 前端API服务 | `/mnt/e/Code/ccr/conf-manage/frontend/src/api/index.js` |
| 脚本管理页面 | `/mnt/e/Code/ccr/conf-manage/frontend/src/views/Scripts.vue` |
| 执行历史页面 | `/mnt/e/Code/ccr/conf-manage/frontend/src/views/Executions.vue` |
| 任务管理页面 | `/mnt/e/Code/ccr/conf-manage/frontend/src/views/Schedules.vue` |
| 文件管理页面 | `/mnt/e/Code/ccr/conf-manage/frontend/src/views/Files.vue` |
| 代码编辑器组件 | `/mnt/e/Code/ccr/conf-manage/frontend/src/components/CodeEditor.vue` |
| 文件上传组件 | `/mnt/e/Code/ccr/conf-manage/frontend/src/components/FileUpload.vue` |
| 执行文件查看器 | `/mnt/e/Code/ccr/conf-manage/frontend/src/components/ExecutionFiles.vue` |

