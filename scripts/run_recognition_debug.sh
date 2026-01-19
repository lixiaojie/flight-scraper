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
export CONFIG_PATH="${SCRAPER_CONFIG_PATH:-$PROJECT_DIR/scripts/config/scraper.config.json}"

CONFIG_LLM_API_TYPE=""
CONFIG_LLM_API_KEY=""
if [ -f "$CONFIG_PATH" ]; then
    CONFIG_LLM_API_TYPE=$(python3 - <<'PY'
import json, os
path = os.environ.get("CONFIG_PATH")
try:
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    print(cfg.get("llmApiType", ""))
except Exception:
    print("")
PY
)
    CONFIG_LLM_API_KEY=$(python3 - <<'PY'
import json, os
path = os.environ.get("CONFIG_PATH")
try:
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    print(cfg.get("llmApiKey", ""))
except Exception:
    print("")
PY
)
fi

export LLM_API_TYPE="${LLM_API_TYPE:-${CONFIG_LLM_API_TYPE:-zai}}"
export ZAI_API_KEY="${ZAI_API_KEY:-$CONFIG_LLM_API_KEY}"

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
