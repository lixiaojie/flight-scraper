#!/bin/bash
"""
开发环境设置脚本
统一本地和Docker环境
"""

echo "🚀 设置统一开发环境..."

# 停止现有服务
echo "📦 停止现有Docker服务..."
docker-compose -f docker-compose.yml down

# 重新构建服务
echo "🔨 重新构建Docker服务..."
docker-compose -f docker-compose.yml build --no-cache

# 启动服务
echo "▶️ 启动服务..."
docker-compose -f docker-compose.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose -f docker-compose.yml ps

# 初始化数据库和管理员
echo "🗄️ 初始化数据库..."
docker-compose -f docker-compose.yml exec web python3 init_database.py

echo "👤 创建管理员账号..."
docker-compose -f docker-compose.yml exec web python3 init_admin.py

# 测试服务
echo "🧪 测试服务..."
echo "测试Web服务:"
curl -s http://localhost:8000/health

echo -e "\n测试登录:"
curl -X POST http://localhost:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

echo -e "\n✅ 开发环境设置完成！"
echo "🌐 前端: http://localhost:3000"
echo "🔧 后端API: http://localhost:8000"
echo "📱 Appium: http://localhost:4723"
echo "🤖 Android模拟器: http://localhost:6080"
