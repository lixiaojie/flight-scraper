#!/bin/bash

# 配置Docker国内镜像源脚本 - 更新版本
# 包含清华大学、腾讯云、阿里云等国内镜像源

set -e

echo "🐳 配置Docker国内镜像源 (更新版本)"
echo "=================================="

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

# 2. 创建daemon.json配置文件 - 包含最新的国内镜像源
log "📝 创建Docker daemon.json配置..."
cat > ~/.docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://ccr.ccs.tencentyun.com",
    "https://registry.docker-cn.com",
    "https://dockerproxy.com",
    "https://mirror.ccs.tencentyun.com",
    "https://registry.cn-hangzhou.aliyuncs.com"
  ],
  "insecure-registries": [],
  "debug": false,
  "experimental": false,
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "dns": ["8.8.8.8", "114.114.114.114"]
}
EOF

log "✅ Docker配置文件已创建: ~/.docker/daemon.json"

# 3. 显示配置内容
log "📋 当前Docker配置："
cat ~/.docker/daemon.json

# 4. 提示用户手动配置系统级Docker配置
log "📋 请手动执行以下命令配置系统级Docker镜像源："
echo ""
echo "sudo mkdir -p /etc/docker"
echo "sudo cp ~/.docker/daemon.json /etc/docker/daemon.json"
echo "sudo systemctl restart docker"
echo ""

# 5. 验证Docker配置
log "🔍 验证Docker配置..."
if [ -f ~/.docker/daemon.json ]; then
    log "✅ 用户级Docker配置已创建"
else
    error "❌ Docker配置文件创建失败"
fi

echo ""
echo "🎉 Docker镜像源配置完成！"
echo "========================"
echo "包含的镜像源："
echo "- 中科大镜像: https://docker.mirrors.ustc.edu.cn"
echo "- 网易镜像: https://hub-mirror.c.163.com"
echo "- 百度镜像: https://mirror.baidubce.com"
echo "- 腾讯云镜像: https://ccr.ccs.tencentyun.com"
echo "- Docker中国镜像: https://registry.docker-cn.com"
echo "- Docker代理: https://dockerproxy.com"
echo "- 腾讯云镜像2: https://mirror.ccs.tencentyun.com"
echo "- 阿里云镜像: https://registry.cn-hangzhou.aliyuncs.com"
echo ""
echo "请执行以下命令完成配置："
echo "1. sudo mkdir -p /etc/docker"
echo "2. sudo cp ~/.docker/daemon.json /etc/docker/daemon.json"
echo "3. sudo systemctl restart docker"
echo "4. docker info | grep -A 10 'Registry Mirrors'"
