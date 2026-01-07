#!/bin/bash
echo "=== API 可访问性检查 ==="
echo ""

echo "1. 检查容器状态..."
docker-compose -f docker-compose.unified.yml ps web

echo ""
echo "2. 从容器内部测试API..."
docker exec flight-scraper-web-1 curl -s http://localhost:8000/health 2>&1

echo ""
echo "3. 从主机测试API..."
curl -v --max-time 5 http://localhost:8000/health 2>&1 | head -15

echo ""
echo "4. 测试API端点..."
echo "  - /health:"
docker exec flight-scraper-web-1 curl -s http://localhost:8000/health 2>&1

echo ""
echo "  - /api/tasks/stats:"
docker exec flight-scraper-web-1 curl -s http://localhost:8000/api/tasks/stats 2>&1

echo ""
echo "5. 检查端口监听..."
docker exec flight-scraper-web-1 netstat -tuln 2>/dev/null | grep 8000 || docker exec flight-scraper-web-1 ss -tuln | grep 8000

echo ""
echo "=== 检查完成 ==="
