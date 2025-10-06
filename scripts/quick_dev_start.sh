#!/bin/bash
# 快速开发环境启动 - 简化版本

echo "🚀 快速启动开发环境..."

# 停止现有服务
echo "停止现有服务..."
docker-compose -f docker-compose.yml down 2>/dev/null || true
docker-compose -f docker-compose.dev.yml down 2>/dev/null || true

# 使用标准Docker Compose启动，但使用开发模式
echo "启动开发服务..."
docker-compose -f docker-compose.yml up -d --build

echo "✅ 开发环境启动完成！"
echo ""
echo "服务地址："
echo "  前端: http://localhost:3000"
echo "  后端: http://localhost:8000"
echo "  Appium: http://localhost:4723"
echo "  Android模拟器: http://localhost:6080"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
