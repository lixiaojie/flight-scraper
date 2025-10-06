#!/bin/bash

echo "🚀 启动航班结果系统"
echo "=================="

# 检查依赖
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 🔍 检查系统依赖..."

# 检查Python环境
if ! python3 -c "import fastapi, sqlalchemy" 2>/dev/null; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] 📦 安装Python依赖..."
    pip3 install fastapi uvicorn sqlalchemy requests
fi

# 检查Node.js环境
if ! node --version >/dev/null 2>&1; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ❌ Node.js未安装，请先安装Node.js"
    exit 1
fi

# 检查Appium服务
if ! curl -s http://localhost:4723/status >/dev/null; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ❌ Appium服务未运行"
    echo "请先启动Appium服务: docker-compose up -d appium"
    exit 1
fi

# 检查Android设备
if ! adb devices | grep -q "device$"; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ❌ 未找到Android设备"
    echo "请确保Android模拟器已启动"
    exit 1
fi

echo "[$(date +'%Y-%m-%d %H:%M:%S')] ✅ 系统依赖检查完成"

# 初始化数据库
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 🗄️ 初始化数据库..."
cd backend
python3 init_database.py
if [ $? -eq 0 ]; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ✅ 数据库初始化成功"
else
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ❌ 数据库初始化失败"
    exit 1
fi
cd ..

# 启动后端服务
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 🚀 启动后端API服务..."
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# 等待后端服务启动
echo "[$(date +'%Y-%m-%d %H:%M:%S')] ⏳ 等待后端服务启动..."
sleep 5

# 检查后端服务
if curl -s http://localhost:8000/api/flights/statistics >/dev/null; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ✅ 后端API服务启动成功"
else
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ❌ 后端API服务启动失败"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# 启动前端服务
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 🎨 启动前端服务..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# 等待前端服务启动
echo "[$(date +'%Y-%m-%d %H:%M:%S')] ⏳ 等待前端服务启动..."
sleep 10

# 检查前端服务
if curl -s http://localhost:3000 >/dev/null; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ✅ 前端服务启动成功"
else
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️ 前端服务可能还在启动中..."
fi

echo ""
echo "🎉 航班结果系统启动完成！"
echo "========================"
echo "📱 前端界面: http://localhost:3000/flight-results"
echo "🔌 后端API: http://localhost:8000/api/flights"
echo "📊 API文档: http://localhost:8000/docs"
echo ""
echo "📋 下一步操作:"
echo "1. 运行数据抓取: source flight_scraper_env/bin/activate && python3 scripts/enhanced_flight_scraper.py"
echo "2. 查看前端界面: 在浏览器中打开 http://localhost:3000/flight-results"
echo "3. 停止服务: 按 Ctrl+C 或运行 ./scripts/stop_flight_system.sh"
echo ""
echo "⏳ 系统正在运行，按 Ctrl+C 停止..."

# 等待用户中断
trap 'echo "🛑 正在停止服务..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo "✅ 服务已停止"; exit 0' INT

# 保持脚本运行
wait
