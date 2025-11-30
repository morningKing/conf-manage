#!/bin/bash

# 启动后端服务脚本

echo "========================================="
echo "脚本工具管理系统 - 后端服务启动脚本"
echo "========================================="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3,请先安装Python3"
    exit 1
fi

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 启动后端服务
echo "启动后端服务..."
cd backend
python app.py
