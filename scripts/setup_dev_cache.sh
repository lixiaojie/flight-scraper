#!/bin/bash
# 设置开发环境依赖缓存

echo "🚀 设置开发环境依赖缓存..."

# 创建缓存目录
mkdir -p ./cache/node_modules
mkdir -p ./cache/python_venv

# 前端依赖缓存
echo "📦 设置前端依赖缓存..."
if [ ! -d "./frontend/node_modules" ]; then
    echo "安装前端依赖..."
    cd frontend
    npm install
    cd ..
fi

# 复制前端依赖到缓存
if [ -d "./frontend/node_modules" ]; then
    echo "复制前端依赖到缓存..."
    cp -r ./frontend/node_modules/* ./cache/node_modules/ 2>/dev/null || true
fi

# 后端依赖缓存
echo "🐍 设置后端依赖缓存..."
if [ ! -d "./backend/venv" ]; then
    echo "创建Python虚拟环境..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    deactivate
    cd ..
fi

# 复制后端依赖到缓存
if [ -d "./backend/venv" ]; then
    echo "复制后端依赖到缓存..."
    cp -r ./backend/venv/* ./cache/python_venv/ 2>/dev/null || true
fi

echo "✅ 依赖缓存设置完成！"
echo ""
echo "使用方法："
echo "  开发模式: docker-compose -f docker-compose.dev.yml up -d"
echo "  生产模式: docker-compose up -d"
