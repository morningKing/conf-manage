"""
AI脚本生成API
"""
import json
import requests
import tempfile
import os
import subprocess
import sys
from flask import request, jsonify, stream_with_context, Response
from . import api_bp
from models import AIConfig


def get_active_ai_config():
    """获取激活的AI配置"""
    config = AIConfig.query.filter_by(is_active=True).first()
    if not config:
        raise Exception('No active AI config found. Please configure AI settings first.')
    return config


def call_openai_api(config, messages, stream=False):
    """调用OpenAI兼容的API"""
    base_url = config.base_url or 'https://api.openai.com/v1'
    url = f"{base_url.rstrip('/')}/chat/completions"

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {config.api_key}'
    }

    data = {
        'model': config.model,
        'messages': messages,
        'stream': stream
    }

    response = requests.post(url, headers=headers, json=data, stream=stream)
    response.raise_for_status()

    return response


@api_bp.route('/ai/generate-script', methods=['POST'])
def generate_script():
    """生成脚本"""
    try:
        data = request.json
        prompt = data.get('prompt')
        context = data.get('context', '')  # 可选的上下文信息

        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        # 获取AI配置
        config = get_active_ai_config()

        # 构建消息 - 专门针对此平台的 Python 脚本生成
        system_message = """You are a helpful assistant that generates Python scripts for a script management platform.

IMPORTANT RULES:
1. ONLY generate Python scripts (Python 3.x)
2. The script will run in an isolated execution space (working directory)
3. Parameters are passed via environment variables - use os.environ.get() to access them
4. Uploaded files are listed in the FILES environment variable as a JSON array
5. Use relative paths to access uploaded files (they are in the same directory as the script)
6. Always add proper error handling and logging
7. Return ONLY the Python code without markdown formatting or explanations

PARAMETER ACCESS PATTERN:
```python
import os
import json

# Access parameters from environment variables
param_value = os.environ.get('PARAM_NAME', 'default_value')

# Access uploaded files
files_json = os.environ.get('FILES', '[]')
files = json.loads(files_json)
for filename in files:
    # File is in current directory, use directly
    with open(filename, 'r') as f:
        content = f.read()
```

SCRIPT STRUCTURE TEMPLATE:
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Script Description: [Brief description]
\"\"\"

import os
import json
import sys

def main():
    try:
        # Get parameters from environment variables
        # param1 = os.environ.get('PARAM1', 'default')

        # Get uploaded files if any
        # files_json = os.environ.get('FILES', '[]')
        # files = json.loads(files_json)

        # Your script logic here
        print("Script started...")

        # Example output
        print("Script completed successfully")

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
```

Generate a production-ready Python script based on the user's requirements."""

        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': f"{context}\n\n{prompt}" if context else prompt}
        ]

        # 调用AI API
        response = call_openai_api(config, messages, stream=False)
        result = response.json()

        # 提取生成的脚本
        script_content = result['choices'][0]['message']['content']

        # 清理可能的 markdown 代码块标记
        script_content = script_content.strip()
        if script_content.startswith('```python'):
            script_content = script_content[9:]
        elif script_content.startswith('```'):
            script_content = script_content[3:]
        if script_content.endswith('```'):
            script_content = script_content[:-3]
        script_content = script_content.strip()

        return jsonify({
            'script': script_content,
            'model': config.model
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/ai/generate-script-stream', methods=['POST'])
def generate_script_stream():
    """生成脚本（流式响应）"""
    try:
        data = request.json
        prompt = data.get('prompt')
        context = data.get('context', '')

        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        # 获取AI配置
        config = get_active_ai_config()

        # 构建消息
        system_message = """You are a helpful assistant that generates shell scripts.
When generating scripts:
1. Use bash as the default shell
2. Add proper error handling
3. Include comments to explain the code
4. Follow best practices for shell scripting
5. Make the script executable and production-ready
6. Return ONLY the script code without any explanation or markdown formatting"""

        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': f"{context}\n\n{prompt}" if context else prompt}
        ]

        def generate():
            """流式生成响应"""
            response = call_openai_api(config, messages, stream=True)

            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        line = line[6:]  # 移除 'data: ' 前缀

                        if line == '[DONE]':
                            break

                        try:
                            chunk = json.loads(line)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    yield f"data: {json.dumps({'content': delta['content']})}\n\n"
                        except json.JSONDecodeError:
                            continue

            yield f"data: {json.dumps({'done': True})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/ai/improve-script', methods=['POST'])
def improve_script():
    """改进现有脚本"""
    try:
        data = request.json
        script_content = data.get('script')
        improvement_request = data.get('request')

        if not script_content or not improvement_request:
            return jsonify({'error': 'Both script and improvement request are required'}), 400

        # 获取AI配置
        config = get_active_ai_config()

        # 构建消息
        system_message = """You are a helpful assistant that improves Python scripts for a script management platform.

IMPORTANT RULES:
1. Maintain Python 3.x syntax
2. The script will run in an isolated execution space
3. Parameters are passed via environment variables - use os.environ.get() to access them
4. Uploaded files are listed in the FILES environment variable as a JSON array
5. Keep the original functionality while adding requested improvements
6. Add proper error handling and logging
7. Return ONLY the improved Python code without markdown formatting or explanations"""

        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': f"Current script:\n```python\n{script_content}\n```\n\nImprovement request: {improvement_request}"}
        ]

        # 调用AI API
        response = call_openai_api(config, messages, stream=False)
        result = response.json()

        # 提取改进的脚本
        improved_script = result['choices'][0]['message']['content']

        # 清理可能的 markdown 代码块标记
        improved_script = improved_script.strip()
        if improved_script.startswith('```python'):
            improved_script = improved_script[9:]
        elif improved_script.startswith('```'):
            improved_script = improved_script[3:]
        if improved_script.endswith('```'):
            improved_script = improved_script[:-3]
        improved_script = improved_script.strip()

        return jsonify({
            'script': improved_script,
            'model': config.model
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/ai/explain-script', methods=['POST'])
def explain_script():
    """解释脚本代码"""
    try:
        data = request.json
        script_content = data.get('script')

        if not script_content:
            return jsonify({'error': 'Script is required'}), 400

        # 获取AI配置
        config = get_active_ai_config()

        # 构建消息
        system_message = """You are a helpful assistant that explains Python scripts for a script management platform.

Context:
- The script is a Python 3.x script
- Parameters are passed via environment variables (accessed with os.environ.get())
- Uploaded files are listed in the FILES environment variable as a JSON array
- The script runs in an isolated execution space

Provide a clear, concise explanation including:
1. Overall purpose and functionality
2. Key steps and logic flow
3. How parameters are accessed and used
4. How files are processed (if applicable)
5. Any important considerations or warnings

Use Chinese (中文) for the explanation."""

        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': f"Please explain this Python script:\n```python\n{script_content}\n```"}
        ]

        # 调用AI API
        response = call_openai_api(config, messages, stream=False)
        result = response.json()

        # 提取解释
        explanation = result['choices'][0]['message']['content']

        return jsonify({
            'explanation': explanation,
            'model': config.model
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/ai/preview-execute', methods=['POST'])
def preview_execute_script():
    """预览执行AI生成的脚本（不创建数据库记录）"""
    try:
        # 支持两种格式：JSON和FormData（用于文件上传）
        if request.content_type and 'multipart/form-data' in request.content_type:
            # FormData格式（带文件上传）
            script_code = request.form.get('code')
            params_str = request.form.get('params', '{}')
            try:
                params = json.loads(params_str) if params_str else {}
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid params JSON format'}), 400

            # 获取上传的文件
            uploaded_files = request.files.getlist('files')
        else:
            # JSON格式（兼容旧版本）
            data = request.json
            script_code = data.get('code')
            params = data.get('params', {})
            uploaded_files = []

        if not script_code:
            return jsonify({'error': 'Script code is required'}), 400

        # 创建临时脚本文件
        temp_dir = tempfile.mkdtemp(prefix='ai_preview_')
        temp_script_path = os.path.join(temp_dir, 'temp_script.py')

        with open(temp_script_path, 'w', encoding='utf-8') as f:
            f.write(script_code)

        # 保存上传的文件到临时目录
        uploaded_file_paths = []
        if uploaded_files:
            for file in uploaded_files:
                if file.filename:
                    # 使用安全的文件名
                    from werkzeug.utils import secure_filename
                    safe_filename = secure_filename(file.filename)
                    file_path = os.path.join(temp_dir, safe_filename)
                    file.save(file_path)
                    uploaded_file_paths.append(safe_filename)

        try:
            # 准备环境变量
            env = os.environ.copy()
            env.update(params)

            # 添加文件列表到环境变量，方便脚本获取
            if uploaded_file_paths:
                env['UPLOADED_FILES'] = ','.join(uploaded_file_paths)

            # 执行脚本
            process = subprocess.Popen(
                [sys.executable, temp_script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=temp_dir,
                env=env,
                text=True
            )

            stdout, stderr = process.communicate(timeout=300)  # 5分钟超时

            # 返回执行结果
            status = 'success' if process.returncode == 0 else 'failed'

            return jsonify({
                'status': status,
                'output': stdout,
                'error': stderr if stderr else None,
                'temp_dir': temp_dir,
                'uploaded_files': uploaded_file_paths,
                'return_code': process.returncode
            })

        except subprocess.TimeoutExpired:
            process.kill()
            return jsonify({'error': 'Execution timeout (5 minutes)'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500
