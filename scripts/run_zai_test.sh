#!/bin/bash
# Z.ai航班识别测试脚本运行器
# 在Docker容器中运行测试脚本

set -e

echo "=================================================================================="
echo "Z.ai GLM-4.6V-Flash 航班识别测试 - Docker运行"
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

# 检查API密钥
ZAI_API_KEY=${ZAI_API_KEY:-"1f3dfbf15dfb41488e34c87ef478e023.Ez05JCLs9ix8GPTh"}
echo "🔍 使用Z.ai API密钥: ${ZAI_API_KEY:0:20}...${ZAI_API_KEY: -10}"

if [ -z "$ZAI_API_KEY" ]; then
    echo "⚠️  未设置ZAI_API_KEY环境变量"
    echo "   请设置: export ZAI_API_KEY='your-api-key'"
    echo "   或使用默认密钥（已在脚本中配置）"
    exit 1
fi

echo "✅ 在Docker容器中运行Z.ai航班识别测试脚本..."
echo ""

# 使用run命令运行一次性容器执行测试脚本
# --rm: 运行后自动删除容器
# --profile scraper: 使用scraper profile
# 传递环境变量
docker-compose --profile scraper run --rm \
    -e ZAI_API_KEY="$ZAI_API_KEY" \
    -e LLM_API_TYPE="zai" \
    flight-scraper python3 /app/scripts/test_zai_flight_recognition.py

echo ""
echo "=================================================================================="
echo "✅ 测试完成"
echo "=================================================================================="
