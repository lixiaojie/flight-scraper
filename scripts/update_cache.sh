#!/bin/bash
# 更新依赖缓存

echo "🔄 更新依赖缓存..."

# 停止开发服务
echo "停止开发服务..."
docker-compose -f docker-compose.dev.yml down

# 清理旧缓存
echo "清理旧缓存..."
rm -rf ./cache/node_modules
rm -rf ./cache/python_venv

# 重新设置缓存
echo "重新设置缓存..."
./scripts/setup_dev_cache.sh

# 重新启动开发服务
echo "重新启动开发服务..."
docker-compose -f docker-compose.dev.yml up -d

echo "✅ 依赖缓存更新完成！"
