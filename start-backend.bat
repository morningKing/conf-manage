@echo off
REM 启动后端服务脚本 (Windows)

echo =========================================
echo 脚本工具管理系统 - 后端服务启动脚本
echo =========================================

REM 检查Python是否安装
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到Python,请先安装Python
    exit /b 1
)

REM 检查虚拟环境是否存在
if not exist "venv" (
    echo 创建Python虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 安装Python依赖...
pip install -r requirements.txt

REM 启动后端服务
echo 启动后端服务...
cd backend
python app.py
