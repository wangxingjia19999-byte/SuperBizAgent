#!/bin/bash

# 快速开始脚本

echo "=================================================="
echo "  Enterprise RAG 快速开始"
echo "=================================================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装"
    exit 1
fi

echo "✅ Python 3 已安装"
python3 --version

# 检查 pip
if ! command -v pip &> /dev/null; then
    echo "❌ pip 未安装"
    exit 1
fi

echo "✅ pip 已安装"

# 创建虚拟环境（可选）
if [ ! -d "venv" ]; then
    echo ""
    echo "创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ 虚拟环境已创建"
else
    echo "✅ 虚拟环境已存在"
    source venv/bin/activate
fi

# 安装依赖
echo ""
echo "安装依赖..."
pip install -r requirements.txt
echo "✅ 依赖安装完成"

# 创建 .env 文件
if [ ! -f ".env" ]; then
    echo ""
    echo "创建 .env 文件..."
    cp .env.example .env
    echo "✅ .env 文件已创建"
fi

# 运行演示
echo ""
echo "运行演示..."
python scripts/run_demo.py

# 启动 API 服务
echo ""
echo "=================================================="
echo "  演示完成！准备启动 API 服务..."
echo "=================================================="
echo ""
echo "按 Enter 启动 FastAPI 服务，或 Ctrl+C 退出"
read

echo "启动 FastAPI 服务..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000
