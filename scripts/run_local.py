#!/usr/bin/env python3
"""
本地开发运行脚本
使用Docker容器来运行Python代码，确保环境一致性
"""

import subprocess
import sys
import os


def run_in_docker(command, description):
    """在Docker容器中运行命令"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(
            f"docker-compose -f docker-compose.yml exec web {command}",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ {description} 成功")
            if result.stdout.strip():
                print(result.stdout)
        else:
            print(f"❌ {description} 失败: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ {description} 出错: {e}")
        return False


def main():
    """主函数"""
    print("🚀 使用Docker统一环境进行本地开发")

    # 检查Docker服务是否运行
    print("🔍 检查Docker服务状态...")
    result = subprocess.run(
        "docker-compose -f docker-compose.yml ps",
        shell=True,
        capture_output=True,
        text=True
    )

    if "web" not in result.stdout:
        print("❌ Web服务未运行，请先运行: docker-compose up -d")
        return

    # 根据参数执行不同操作
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 scripts/run_local.py init_db     # 初始化数据库")
        print("  python3 scripts/run_local.py init_admin   # 创建管理员")
        print("  python3 scripts/run_local.py test_api       # 测试API")
        print("  python3 scripts/run_local.py run_script <script> # 运行脚本")
        return

    command = sys.argv[1]

    if command == "init_db":
        run_in_docker("python3 init_database.py", "初始化数据库")
    elif command == "init_admin":
        run_in_docker("python3 init_admin.py", "创建管理员账号")
    elif command == "test_api":
        run_in_docker(
            "python3 -c \"import requests; print(requests.get('http://localhost:8000/health').json())\"",
            "测试API")
    elif command == "run_script":
        if len(sys.argv) < 3:
            print("❌ 请指定要运行的脚本")
            return
        script = sys.argv[2]
        run_in_docker(f"python3 {script}", f"运行脚本 {script}")
    else:
        print(f"❌ 未知命令: {command}")


if __name__ == "__main__":
    main()
