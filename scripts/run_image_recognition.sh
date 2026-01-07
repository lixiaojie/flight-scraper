#!/bin/bash
# 运行图片识别脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# 检查参数
if [ $# -lt 1 ]; then
    echo "使用方法: $0 <图片路径>"
    echo ""
    echo "示例:"
    echo "  $0 /path/to/screenshot.png"
    echo "  $0 results/screenshots/flight_results.png"
    echo ""
    echo "如果图片在本地，会先复制到容器中"
    exit 1
fi

IMAGE_PATH="$1"

# 检查图片文件是否存在
if [ ! -f "$IMAGE_PATH" ]; then
    echo "❌ 图片文件不存在: $IMAGE_PATH"
    exit 1
fi

# 获取图片文件名
IMAGE_NAME=$(basename "$IMAGE_PATH")
IMAGE_DIR=$(dirname "$IMAGE_PATH")

# 设置环境变量
export ZAI_API_KEY="${ZAI_API_KEY:-1f3dfbf15dfb41488e34c87ef478e023.Ez05JCLs9ix8GPTh}"
export LLM_API_TYPE="${LLM_API_TYPE:-zai}"

echo "📋 配置信息:"
echo "   图片路径: $IMAGE_PATH"
echo "   图片名称: $IMAGE_NAME"
echo "   LLM API Type: $LLM_API_TYPE"
echo ""

# 如果图片在项目目录外，需要复制到容器可访问的位置
if [[ "$IMAGE_PATH" != "$PROJECT_DIR"* ]]; then
    echo "📋 图片在项目目录外，复制到容器可访问的位置..."
    CONTAINER_IMAGE_PATH="/app/results/temp_$IMAGE_NAME"
    docker cp "$IMAGE_PATH" "$(docker-compose ps -q flight-scraper 2>/dev/null || echo '')":/app/results/ 2>/dev/null || {
        # 如果容器不存在，先创建临时目录
        mkdir -p "$PROJECT_DIR/results/temp"
        cp "$IMAGE_PATH" "$PROJECT_DIR/results/temp/$IMAGE_NAME"
        CONTAINER_IMAGE_PATH="/app/results/temp/$IMAGE_NAME"
    }
else
    # 图片在项目目录内，直接使用相对路径
    RELATIVE_PATH=$(realpath --relative-to="$PROJECT_DIR" "$IMAGE_PATH")
    CONTAINER_IMAGE_PATH="/app/$RELATIVE_PATH"
fi

echo "🚀 运行图片识别..."
docker-compose --profile scraper run --rm \
    -e ZAI_API_KEY="$ZAI_API_KEY" \
    -e LLM_API_TYPE="$LLM_API_TYPE" \
    -v "$PROJECT_DIR/results:/app/results" \
    flight-scraper \
    python3 /app/scripts/test_image_recognition.py "$CONTAINER_IMAGE_PATH"
