#!/bin/bash

echo "🚀 启动航班抓取系统"
echo "=================="

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 检查docker-compose是否可用
if ! command -v docker-compose >/dev/null 2>&1; then
    echo "❌ docker-compose未安装，请先安装docker-compose"
    exit 1
fi

echo "[$(date +'%Y-%m-%d %H:%M:%S')] 🐳 启动Docker Compose服务..."

# 启动基础服务
docker-compose up -d web frontend

echo "[$(date +'%Y-%m-%d %H:%M:%S')] ⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 🔍 检查服务状态..."

# 检查Web服务
if curl -s http://localhost:8000/health >/dev/null; then
    echo "✅ Web服务运行正常"
else
    echo "❌ Web服务启动失败"
fi

# 检查前端服务
if curl -s http://localhost:3000 >/dev/null; then
    echo "✅ 前端服务运行正常"
else
    echo "❌ 前端服务启动失败"
fi

echo ""
echo "🎉 系统启动完成！"
echo "=================="
echo "📱 前端界面: http://localhost:3000"
echo "🔌 后端API: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo ""
echo "📋 下一步操作:"
echo "1. 访问前端界面进行系统管理"
echo "2. 启动Android模拟器和Appium服务"
echo "3. 运行航班抓取任务"
echo ""
echo "⏳ 系统正在运行，按 Ctrl+C 停止..."

# 保持脚本运行
wait
