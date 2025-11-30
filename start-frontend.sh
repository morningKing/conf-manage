#!/bin/bash

# 启动前端服务脚本

echo "========================================="
echo "脚本工具管理系统 - 前端服务启动脚本"
echo "========================================="

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo "错误: 未找到Node.js,请先安装Node.js"
    exit 1
fi

# 检查npm是否安装
if ! command -v npm &> /dev/null; then
    echo "错误: 未找到npm,请先安装npm"
    exit 1
fi

# 进入前端目录
cd frontend

# 检查node_modules是否存在
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

# 启动前端服务
echo "启动前端服务..."
npm run dev
