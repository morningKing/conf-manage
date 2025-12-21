"""
脚本执行引擎
"""
import os
import subprocess
import json
import shutil
import threading
from datetime import datetime
from models import db, Execution, Script, Environment, GlobalVariable
from config import Config
import tempfile


def get_global_variables_dict():
    """获取全局变量字典"""
    try:
        variables = GlobalVariable.query.all()
        return {var.key: var.value for var in variables}
    except Exception as e:
        print(f'获取全局变量失败: {str(e)}')
        return {}


def stream_output_to_file(pipe, log_file_path):
    """
    实时读取进程输出并写入日志文件
    这个函数在单独的线程中运行，确保日志实时刷新到磁盘
    """
    try:
        with open(log_file_path, 'a', encoding='utf-8', buffering=1) as log_f:
            for line in iter(pipe.readline, b''):
                if line:
                    decoded_line = line.decode('utf-8', errors='replace')
                    log_f.write(decoded_line)
                    log_f.flush()  # 立即刷新到磁盘
                    os.fsync(log_f.fileno())  # 强制操作系统写入磁盘
    except Exception as e:
        print(f"流式输出线程错误: {e}")
    finally:
        pipe.close()



def execute_script(execution_id, custom_cwd=None):
    """执行脚本

    Args:
        execution_id: 执行记录ID
        custom_cwd: 自定义工作目录（可选，用于工作流节点在共享空间中执行）
    """
    try:
        # 在新线程中，需要移除旧的会话并创建新的会话
        db.session.remove()

        # 获取执行记录
        execution = Execution.query.get(execution_id)
        if not execution:
            return

        # 获取脚本
        script = Script.query.get(execution.script_id)
        if not script:
            execution.status = 'failed'
            execution.error = '脚本不存在'
            db.session.commit()
            return

        # 更新状态为运行中
        execution.status = 'running'
        execution.stage = 'preparing'
        execution.progress = 10
        execution.start_time = datetime.utcnow()
        db.session.commit()

        # 解析参数
        params = {}
        uploaded_files = []
        workflow_space = None  # 工作流执行空间（如果有）
        if execution.params:
            try:
                params = json.loads(execution.params)
                # 提取上传的文件信息
                if 'uploaded_files' in params:
                    uploaded_files = params.pop('uploaded_files')
                # 提取工作流空间路径（如果是工作流节点执行）
                if 'WORKFLOW_SPACE' in params:
                    workflow_space = params.pop('WORKFLOW_SPACE')
            except:
                pass

        # 确保执行空间存在（文件上传时已创建，这里再次确保）
        execution_space = Config.ensure_execution_space(execution_id)
        print(f"执行 {execution_id} 的执行空间: {execution_space}")

        # 确定工作目录：优先使用自定义目录，其次使用工作流空间，最后使用执行空间
        working_dir = custom_cwd or workflow_space or execution_space
        if working_dir != execution_space:
            print(f"使用自定义工作目录: {working_dir}")
            # 确保自定义工作目录存在
            os.makedirs(working_dir, exist_ok=True)

        # 准备文件列表（文件已在执行空间中，无需复制）
        execution_files = []
        for file_info in uploaded_files:
            filename = file_info['original_name']
            # 对于工作流节点，文件在工作流空间中；对于普通执行，文件在执行空间中
            file_path = os.path.join(working_dir, filename)
            if os.path.exists(file_path):
                execution_files.append({
                    'name': filename,
                    'path': file_path
                })
                print(f"工作目录中的文件: {filename}")

        # 创建临时脚本文件（放在工作目录中）
        script_ext = '.py' if script.type == 'python' else '.js'
        script_filename = f'script_{execution_id}{script_ext}'
        script_file = os.path.join(working_dir, script_filename)
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script.code)

        # 创建日志文件
        log_dir = Config.LOGS_DIR
        os.makedirs(log_dir, exist_ok=True)  # 确保日志目录存在
        log_file = os.path.join(log_dir, f'execution_{execution_id}.log')
        execution.log_file = log_file
        db.session.commit()  # 立即提交，让SSE端点能找到日志文件路径

        try:
            # 获取解释器路径
            python_executable = Config.PYTHON_EXECUTABLE
            node_executable = Config.NODE_EXECUTABLE

            # 确定使用的执行环境（优先级：execution.environment_id > script.environment_id）
            env_id = execution.environment_id or script.environment_id

            if env_id:
                environment = Environment.query.get(env_id)
                if environment:
                    if script.type == 'python' and environment.type == 'python':
                        python_executable = environment.executable_path
                    elif script.type == 'javascript' and environment.type == 'javascript':
                        node_executable = environment.executable_path

                    source = "执行时指定" if execution.environment_id else "脚本默认"
                    print(f"使用{source}的环境 '{environment.name}' 的解释器: {environment.executable_path}")

            # 准备执行命令
            if script.type == 'python':
                # 安装依赖
                if script.dependencies:
                    execution.stage = 'installing_deps'
                    execution.progress = 30
                    db.session.commit()
                    install_dependencies_python(script.dependencies, python_executable)

                # 构建命令 (-u 参数禁用输出缓冲，确保实时输出)
                cmd = [python_executable, '-u', script_filename]

                # 准备环境变量，包含所有参数
                env = os.environ.copy()

                # 注入全局变量
                global_vars = get_global_variables_dict()
                for key, value in global_vars.items():
                    env[key] = str(value)

                # 注入执行参数（执行参数优先级高于全局变量）
                for key, value in params.items():
                    env[key] = str(value)

                # 添加文件路径环境变量（使用相对路径）
                if execution_files:
                    file_names = [f['name'] for f in execution_files]
                    env['FILES'] = json.dumps(file_names)

            elif script.type == 'javascript':
                # 安装依赖
                if script.dependencies:
                    execution.stage = 'installing_deps'
                    execution.progress = 30
                    db.session.commit()
                    install_dependencies_node(script.dependencies, node_executable)

                # 构建命令
                cmd = [node_executable, script_filename]

                # 准备环境变量，包含所有参数
                env = os.environ.copy()

                # 注入全局变量
                global_vars = get_global_variables_dict()
                for key, value in global_vars.items():
                    env[key] = str(value)

                # 注入执行参数（执行参数优先级高于全局变量）
                for key, value in params.items():
                    env[key] = str(value)

                # 添加文件路径环境变量（使用相对路径）
                if execution_files:
                    file_names = [f['name'] for f in execution_files]
                    env['FILES'] = json.dumps(file_names)
            else:
                raise Exception(f'不支持的脚本类型: {script.type}')

            # 执行脚本（在工作目录中执行）
            execution.stage = 'running'
            execution.progress = 50
            db.session.commit()

            # 创建空的日志文件
            with open(log_file, 'w', encoding='utf-8') as f:
                pass  # 只是创建文件

            # 使用 PIPE 捕获输出，通过线程实时写入日志文件
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                cwd=working_dir,  # 在工作目录中执行
                bufsize=0  # 无缓冲
            )

            # 保存进程ID
            execution.pid = process.pid
            db.session.commit()

            # 启动线程实时读取输出并写入日志文件
            output_thread = threading.Thread(
                target=stream_output_to_file,
                args=(process.stdout, log_file),
                daemon=True
            )
            output_thread.start()

            # 等待执行完成（带超时）
            try:
                process.wait(timeout=Config.EXECUTION_TIMEOUT)
            except subprocess.TimeoutExpired:
                process.kill()
                raise Exception('脚本执行超时')

            # 等待输出线程完成
            output_thread.join(timeout=5)

            # 完成阶段
            execution.stage = 'finishing'
            execution.progress = 90
            db.session.commit()

            # 读取输出
            with open(log_file, 'r', encoding='utf-8') as log_f:
                output = log_f.read()

            # 更新执行结果
            if process.returncode == 0:
                execution.status = 'success'
                execution.progress = 100
                execution.stage = 'completed'
                execution.output = output[:10000]  # 限制输出长度
            else:
                execution.status = 'failed'
                execution.progress = 100
                execution.stage = 'failed'
                execution.error = output[-5000:]  # 保存最后的错误信息

        except Exception as e:
            execution.status = 'failed'
            execution.progress = 100
            execution.stage = 'failed'
            execution.error = str(e)

        finally:
            # 脚本文件保留在工作目录中，供后续查看
            # 对于普通执行，文件在执行空间；对于工作流节点，文件在工作流空间

            # 更新结束时间
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


def install_dependencies_python(dependencies, python_executable=None):
    """安装Python依赖"""
    try:
        if python_executable is None:
            python_executable = Config.PYTHON_EXECUTABLE

        deps = json.loads(dependencies) if isinstance(dependencies, str) else dependencies
        if isinstance(deps, dict):
            deps = deps.get('packages', [])
        elif isinstance(deps, str):
            deps = [d.strip() for d in deps.split(',') if d.strip()]

        if deps:
            cmd = [python_executable, '-m', 'pip', 'install'] + deps
            subprocess.run(cmd, check=True, capture_output=True)
    except Exception as e:
        print(f'安装Python依赖失败: {str(e)}')


def install_dependencies_node(dependencies, node_executable=None):
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
