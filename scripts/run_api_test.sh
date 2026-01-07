#!/bin/bash
# Z.ai API连接测试脚本运行器

set -e

echo "=================================================================================="
echo "Z.ai API连接测试"
echo "=================================================================================="
echo ""

# 检查Docker是否运行
if ! docker ps > /dev/null 2>&1; then
    echo "⚠️  Docker未运行，尝试在本地运行..."
    # 在本地运行
    export ZAI_API_KEY=${ZAI_API_KEY:-"1f3dfbf15dfb41488e34c87ef478e023.Ez05JCLs9ix8GPTh"}
    python3 scripts/test_zai_api_connection.py
    exit $?
fi

# 检查API密钥
ZAI_API_KEY=${ZAI_API_KEY:-"1f3dfbf15dfb41488e34c87ef478e023.Ez05JCLs9ix8GPTh"}
echo "🔑 使用API密钥: ${ZAI_API_KEY:0:20}...${ZAI_API_KEY: -10}"

echo "✅ 在Docker容器中运行API连接测试..."
echo ""

# 使用run命令运行一次性容器执行测试脚本
docker-compose --profile scraper run --rm \
    -e ZAI_API_KEY="$ZAI_API_KEY" \
    flight-scraper python3 /app/scripts/test_zai_api_connection.py

echo ""
echo "=================================================================================="
echo "✅ 测试完成"
echo "=================================================================================="
