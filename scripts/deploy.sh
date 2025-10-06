#!/bin/bash

# 项目部署脚本

set -e

echo "🚀 部署 Flight Scraper 项目"
echo "=========================="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 创建必要目录
mkdir -p data
mkdir -p ssl

# 构建和启动服务
echo "🔨 构建和启动服务..."
docker-compose up --build -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

echo ""
echo "🎉 部署完成！"
echo "============="
echo "服务地址："
echo "  Web 服务: http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "  Android 模拟器: http://localhost:6080"
echo "  Appium 服务: http://localhost:4723"
echo ""
echo "管理命令："
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
