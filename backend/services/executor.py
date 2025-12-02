"""
脚本执行引擎
"""
import os
import subprocess
import json
import shutil
from datetime import datetime
from models import db, Execution, Script, Environment
from config import Config
import tempfile


def execute_script(execution_id):
    """执行脚本"""
    try:
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
        execution.start_time = datetime.utcnow()
        db.session.commit()

        # 解析参数
        params = {}
        uploaded_files = []
        if execution.params:
            try:
                params = json.loads(execution.params)
                # 提取上传的文件信息
                if 'uploaded_files' in params:
                    uploaded_files = params.pop('uploaded_files')
            except:
                pass

        # 确保执行空间存在（文件上传时已创建，这里再次确保）
        execution_space = Config.ensure_execution_space(execution_id)
        print(f"执行 {execution_id} 的执行空间: {execution_space}")

        # 准备文件列表（文件已在执行空间中，无需复制）
        execution_files = []
        for file_info in uploaded_files:
            filename = file_info['original_name']
            file_path = os.path.join(execution_space, filename)
            if os.path.exists(file_path):
                execution_files.append({
                    'name': filename,
                    'path': file_path
                })
                print(f"执行空间中的文件: {filename}")

        # 创建临时脚本文件（放在执行空间中）
        script_ext = '.py' if script.type == 'python' else '.js'
        script_filename = f'script_{execution_id}{script_ext}'
        script_file = os.path.join(execution_space, script_filename)
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

            # 如果脚本指定了执行环境，使用环境的解释器
            if script.environment_id:
                environment = Environment.query.get(script.environment_id)
                if environment:
                    if script.type == 'python' and environment.type == 'python':
                        python_executable = environment.executable_path
                    elif script.type == 'javascript' and environment.type == 'javascript':
                        node_executable = environment.executable_path
                    print(f"使用环境 '{environment.name}' 的解释器: {environment.executable_path}")

            # 准备执行命令
            if script.type == 'python':
                # 安装依赖
                if script.dependencies:
                    install_dependencies_python(script.dependencies, python_executable)

                # 构建命令
                cmd = [python_executable, script_filename]

                # 准备环境变量，包含所有参数
                env = os.environ.copy()
                for key, value in params.items():
                    env[key] = str(value)

                # 添加文件路径环境变量（使用相对路径）
                if execution_files:
                    file_names = [f['name'] for f in execution_files]
                    env['FILES'] = json.dumps(file_names)

            elif script.type == 'javascript':
                # 安装依赖
                if script.dependencies:
                    install_dependencies_node(script.dependencies, node_executable)

                # 构建命令
                cmd = [node_executable, script_filename]

                # 准备环境变量，包含所有参数
                env = os.environ.copy()
                for key, value in params.items():
                    env[key] = str(value)

                # 添加文件路径环境变量（使用相对路径）
                if execution_files:
                    file_names = [f['name'] for f in execution_files]
                    env['FILES'] = json.dumps(file_names)
            else:
                raise Exception(f'不支持的脚本类型: {script.type}')

            # 执行脚本（在执行空间中执行）
            with open(log_file, 'w', encoding='utf-8') as log_f:
                process = subprocess.Popen(
                    cmd,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    env=env,
                    cwd=execution_space  # 在执行空间中执行
                )

                # 等待执行完成（带超时）
                try:
                    process.wait(timeout=Config.EXECUTION_TIMEOUT)
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
            # 脚本文件保留在执行空间中，供后续查看
            # 删除执行记录时会一并删除整个执行空间

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
