#!/bin/bash

# 航班抓取系统启动脚本

set -e

echo "🚀 启动航班抓取系统..."

# 检查 Docker 服务是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 服务未运行，请先启动 Docker"
    exit 1
fi

# 检查 Appium 是否运行
if ! curl -s http://localhost:4723/status > /dev/null 2>&1; then
    echo "⚠️  Appium 服务未运行，请先启动 Appium:"
    echo "   ./scripts/start_appium.sh"
    echo ""
    echo "是否现在启动 Appium? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "启动 Appium..."
        ./scripts/start_appium.sh &
        sleep 5
    else
        echo "请手动启动 Appium 后重新运行此脚本"
        exit 1
    fi
fi

# 启动 Docker 服务
echo "📦 启动 Docker 服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

echo ""
echo "✅ 系统启动完成！"
echo ""
echo "📋 服务访问地址:"
echo "   - Web API: http://localhost:8000"
echo "   - Frontend: http://localhost:3000"
echo "   - Appium: http://localhost:4723"
echo ""
echo "🔧 管理命令:"
echo "   - 查看日志: docker-compose logs -f"
echo "   - 停止服务: docker-compose down"
echo "   - 重启服务: docker-compose restart"