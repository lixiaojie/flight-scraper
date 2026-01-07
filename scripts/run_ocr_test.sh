#!/bin/bash
# OCR价格匹配测试脚本运行器
# 在Docker容器中运行测试脚本

set -e

echo "=================================================================================="
echo "OCR价格匹配测试 - Docker运行"
echo "=================================================================================="
echo ""

# 检查Docker是否运行
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 检查必要的服务是否运行
echo "🔍 检查依赖服务..."
if ! docker-compose ps appium | grep -q "Up"; then
    echo "⚠️  Appium服务未运行，尝试启动..."
    docker-compose up -d appium
    echo "⏳ 等待Appium启动..."
    sleep 5
fi

if ! docker-compose ps web | grep -q "Up"; then
    echo "⚠️  Web服务未运行，尝试启动..."
    docker-compose up -d web
    echo "⏳ 等待Web服务启动..."
    sleep 3
fi

echo "✅ 在Docker容器中运行OCR测试脚本..."
echo ""

# 使用run命令运行一次性容器执行测试脚本
# --rm: 运行后自动删除容器
# --profile scraper: 使用scraper profile
docker-compose --profile scraper run --rm flight-scraper python3 /app/scripts/test_ocr_price_matching.py

echo ""
echo "=================================================================================="
echo "✅ 测试完成"
echo "=================================================================================="
