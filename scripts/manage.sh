#!/bin/bash

# 项目管理脚本

case "$1" in
    start)
        echo "🚀 启动所有服务..."
        docker-compose up -d
        ;;
    stop)
        echo "🛑 停止所有服务..."
        docker-compose down
        ;;
    restart)
        echo "🔄 重启所有服务..."
        docker-compose restart
        ;;
    logs)
        echo "📋 查看服务日志..."
        docker-compose logs -f
        ;;
    status)
        echo "📊 服务状态..."
        docker-compose ps
        ;;
    build)
        echo "🔨 重新构建服务..."
        docker-compose up --build -d
        ;;
    clean)
        echo "🧹 清理 Docker 资源..."
        docker-compose down -v
        docker system prune -f
        ;;
    *)
        echo "用法: $0 {start|stop|restart|logs|status|build|clean}"
        echo ""
        echo "命令说明："
        echo "  start   - 启动所有服务"
        echo "  stop    - 停止所有服务"
        echo "  restart - 重启所有服务"
        echo "  logs    - 查看服务日志"
        echo "  status  - 查看服务状态"
        echo "  build   - 重新构建服务"
        echo "  clean   - 清理 Docker 资源"
        exit 1
        ;;
esac
