#!/bin/bash
# 运行识别方法对比测试

if [ $# -lt 1 ]; then
    echo "使用方法: $0 <图片路径>"
    echo ""
    echo "示例:"
    echo "  $0 assets/ScreenShot_2026-01-06_172101_024.png"
    echo "  $0 /path/to/screenshot.png"
    exit 1
fi

IMAGE_PATH="$1"

# 设置默认API配置（优先环境变量，其次配置文件）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
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

echo "=================================================================================="
echo "🔬 航班识别方法对比测试"
echo "=================================================================================="
echo ""
echo "📸 图片路径: $IMAGE_PATH"
echo "🔧 API配置:"
echo "   API类型: $LLM_API_TYPE"
echo "   API密钥: ${ZAI_API_KEY:0:20}...${ZAI_API_KEY: -10}"
echo ""

# 检查是否在Docker环境中
if [ -f "/.dockerenv" ] || [ -n "$DOCKER_CONTAINER" ]; then
    # 在Docker容器中运行
    python3 /app/scripts/test_recognition_comparison.py "$IMAGE_PATH"
else
    # 在本地运行（使用Docker）
    if [ ! -f "docker-compose.yml" ]; then
        echo "❌ 未找到 docker-compose.yml，请确保在项目根目录运行"
        exit 1
    fi
    
    # 将图片路径转换为容器内路径
    if [[ "$IMAGE_PATH" == /* ]]; then
        # 绝对路径，需要挂载
        IMAGE_DIR=$(dirname "$IMAGE_PATH")
        IMAGE_FILE=$(basename "$IMAGE_PATH")
        docker-compose --profile scraper run --rm \
            -e ZAI_API_KEY="$ZAI_API_KEY" \
            -e LLM_API_TYPE="$LLM_API_TYPE" \
            -v "$(pwd)/results:/app/results" \
            -v "$IMAGE_DIR:/app/input_images" \
            flight-scraper \
            python3 /app/scripts/test_recognition_comparison.py "/app/input_images/$IMAGE_FILE"
    else
        # 相对路径，假设在项目目录中
        docker-compose --profile scraper run --rm \
            -e ZAI_API_KEY="$ZAI_API_KEY" \
            -e LLM_API_TYPE="$LLM_API_TYPE" \
            -v "$(pwd):/app" \
            flight-scraper \
            python3 /app/scripts/test_recognition_comparison.py "/app/$IMAGE_PATH"
    fi
fi
