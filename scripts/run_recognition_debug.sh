#!/bin/bash
# 运行航班识别调试测试脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# 检查必要的服务是否运行
echo "🔍 检查服务状态..."
if ! docker-compose ps appium | grep -q "Up"; then
    echo "⚠️ Appium服务未运行，正在启动..."
    docker-compose up -d appium
    sleep 5
fi

if ! docker-compose ps web | grep -q "Up"; then
    echo "⚠️ Web服务未运行，正在启动..."
    docker-compose up -d web
    sleep 5
fi

# 设置环境变量
export UDID="${UDID:-emulator-5554}"
export APPIUM_SERVER_URL="${APPIUM_SERVER_URL:-http://appium:4723}"
export ZAI_API_KEY="${ZAI_API_KEY:-1f3dfbf15dfb41488e34c87ef478e023.Ez05JCLs9ix8GPTh}"
export LLM_API_TYPE="${LLM_API_TYPE:-zai}"

# 使用z.ai提供的免费API
# 模型版本: GLM_4.6V_Flash
# API密钥: 1f3dfbf15dfb41488e34c87ef478e023.Ez05JCLs9ix8GPTh

echo "📋 配置信息:"
echo "   UDID: $UDID"
echo "   Appium URL: $APPIUM_SERVER_URL"
echo "   LLM API Type: $LLM_API_TYPE"
echo ""

# 运行测试脚本
echo "🚀 运行航班识别调试测试..."
docker-compose --profile scraper run --rm \
    -e UDID="$UDID" \
    -e APPIUM_SERVER_URL="$APPIUM_SERVER_URL" \
    -e ZAI_API_KEY="$ZAI_API_KEY" \
    -e LLM_API_TYPE="$LLM_API_TYPE" \
    flight-scraper \
    python3 /app/scripts/test_flight_recognition_debug.py
