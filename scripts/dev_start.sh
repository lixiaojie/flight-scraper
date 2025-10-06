#!/bin/bash
# 快速启动开发环境

echo "🚀 启动开发环境..."

# 检查是否已设置缓存
if [ ! -d "./cache" ]; then
    echo "首次运行，设置依赖缓存..."
    ./scripts/setup_dev_cache.sh
fi

# 启动开发服务
echo "启动Docker开发服务..."
docker-compose -f docker-compose.dev.yml up -d

echo "✅ 开发环境启动完成！"
echo ""
echo "服务地址："
echo "  前端: http://localhost:3000"
echo "  后端: http://localhost:8000"
echo "  Appium: http://localhost:4723"
echo "  Android模拟器: http://localhost:6080"
echo ""
echo "查看日志: docker-compose -f docker-compose.dev.yml logs -f"
echo "停止服务: docker-compose -f docker-compose.dev.yml down"
