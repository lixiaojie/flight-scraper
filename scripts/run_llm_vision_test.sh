#!/bin/bash
# 大模型视觉API测试脚本运行器
# 在Docker容器中运行测试脚本

set -e

echo "=================================================================================="
echo "大模型视觉API测试 - Docker运行"
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
LLM_API_TYPE=${LLM_API_TYPE:-openai}
echo "🔍 检查${LLM_API_TYPE} API密钥..."

if [ "$LLM_API_TYPE" = "openai" ]; then
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "⚠️  未设置OPENAI_API_KEY环境变量"
        echo "   请设置: export OPENAI_API_KEY='your-api-key'"
        echo "   或在docker-compose.yml中配置"
        exit 1
    fi
elif [ "$LLM_API_TYPE" = "anthropic" ]; then
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo "⚠️  未设置ANTHROPIC_API_KEY环境变量"
        echo "   请设置: export ANTHROPIC_API_KEY='your-api-key'"
        exit 1
    fi
elif [ "$LLM_API_TYPE" = "google" ]; then
    if [ -z "$GOOGLE_API_KEY" ]; then
        echo "⚠️  未设置GOOGLE_API_KEY环境变量"
        echo "   请设置: export GOOGLE_API_KEY='your-api-key'"
        exit 1
    fi
elif [ "$LLM_API_TYPE" = "zai" ] || [ "$LLM_API_TYPE" = "glm" ]; then
    if [ -z "$ZAI_API_KEY" ]; then
        echo "⚠️  未设置ZAI_API_KEY环境变量"
        echo "   请设置: export ZAI_API_KEY='your-api-key'"
        exit 1
    fi
fi

echo "✅ 在Docker容器中运行大模型视觉API测试脚本..."
echo ""

# 使用run命令运行一次性容器执行测试脚本
# --rm: 运行后自动删除容器
# --profile scraper: 使用scraper profile
# 传递环境变量
docker-compose --profile scraper run --rm \
    -e OPENAI_API_KEY="$OPENAI_API_KEY" \
    -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
    -e GOOGLE_API_KEY="$GOOGLE_API_KEY" \
    -e ZAI_API_KEY="$ZAI_API_KEY" \
    -e LLM_API_TYPE="$LLM_API_TYPE" \
    flight-scraper python3 /app/scripts/test_llm_vision_parser.py

echo ""
echo "=================================================================================="
echo "✅ 测试完成"
echo "=================================================================================="
