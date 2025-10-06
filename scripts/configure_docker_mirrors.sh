#!/bin/bash

# 配置Docker国内镜像源脚本

set -e

echo "🐳 配置Docker国内镜像源"
echo "======================="

log() {
    echo -e "\033[0;32m[$(date +'%Y-%m-%d %H:%M:%S')] $1\033[0m"
}

warning() {
    echo -e "\033[1;33m[WARNING] $1\033[0m"
}

error() {
    echo -e "\033[0;31m[ERROR] $1\033[0m"
}

# 1. 创建Docker配置目录
log "📁 创建Docker配置目录..."
mkdir -p ~/.docker

# 2. 创建daemon.json配置文件
log "📝 创建Docker daemon.json配置..."
cat > ~/.docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://ccr.ccs.tencentyun.com",
    "https://registry.docker-cn.com"
  ],
  "insecure-registries": [],
  "debug": false,
  "experimental": false,
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  }
}
EOF

log "✅ Docker配置文件已创建: ~/.docker/daemon.json"

# 3. 提示用户手动配置系统级Docker配置
log "📋 请手动执行以下命令配置系统级Docker镜像源："
echo ""
echo "sudo cp ~/.docker/daemon.json /etc/docker/daemon.json"
echo "sudo systemctl restart docker"
echo ""

# 4. 验证Docker配置
log "🔍 验证Docker配置..."
if [ -f ~/.docker/daemon.json ]; then
    log "✅ 用户级Docker配置已创建"
    cat ~/.docker/daemon.json
else
    error "❌ Docker配置文件创建失败"
fi

echo ""
echo "🎉 Docker镜像源配置完成！"
echo "========================"
echo "请执行以下命令完成配置："
echo "1. sudo cp ~/.docker/daemon.json /etc/docker/daemon.json"
echo "2. sudo systemctl restart docker"
echo "3. docker info | grep -A 10 'Registry Mirrors'"
