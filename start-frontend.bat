@echo off
REM 启动前端服务脚本 (Windows)

echo =========================================
echo 脚本工具管理系统 - 前端服务启动脚本
echo =========================================

REM 检查Node.js是否安装
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到Node.js,请先安装Node.js
    exit /b 1
)

REM 检查npm是否安装
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到npm,请先安装npm
    exit /b 1
)

REM 进入前端目录
cd frontend

REM 检查node_modules是否存在
if not exist "node_modules" (
    echo 安装前端依赖...
    npm install
)

REM 启动前端服务
echo 启动前端服务...
npm run dev
