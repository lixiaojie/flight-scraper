FROM python:3.11-slim

WORKDIR /app

# 配置国内APT源
# 检测Debian版本并完全替换源配置，避免源冲突
RUN DEBIAN_VERSION=$(cat /etc/os-release 2>/dev/null | grep "^VERSION_CODENAME=" | cut -d= -f2 || \
                     (cat /etc/os-release 2>/dev/null | grep "^VERSION_ID=" | cut -d= -f2 | tr -d '"' | \
                      sed 's/11/bullseye/;s/12/bookworm/;s/13/trixie/' || echo "bookworm")) && \
    echo "检测到Debian版本: $DEBIAN_VERSION" && \
    # 方法1: 先尝试替换现有源中的URL
    sed -i 's|http://deb.debian.org|https://mirrors.ustc.edu.cn|g' /etc/apt/sources.list 2>/dev/null || true && \
    sed -i 's|https://deb.debian.org|https://mirrors.ustc.edu.cn|g' /etc/apt/sources.list 2>/dev/null || true && \
    sed -i 's|http://security.debian.org|https://mirrors.ustc.edu.cn/debian-security|g' /etc/apt/sources.list 2>/dev/null || true && \
    sed -i 's|https://security.debian.org|https://mirrors.ustc.edu.cn/debian-security|g' /etc/apt/sources.list 2>/dev/null || true && \
    # 方法2: 完全清空并重新配置（作为备选）
    rm -rf /etc/apt/sources.list.d 2>/dev/null || true && \
    mkdir -p /etc/apt/sources.list.d && \
    echo "deb https://mirrors.ustc.edu.cn/debian/ $DEBIAN_VERSION main" > /etc/apt/sources.list && \
    echo "deb https://mirrors.ustc.edu.cn/debian/ $DEBIAN_VERSION-updates main" >> /etc/apt/sources.list && \
    if [ "$DEBIAN_VERSION" != "trixie" ]; then \
        echo "deb https://mirrors.ustc.edu.cn/debian-security/ $DEBIAN_VERSION-security main" >> /etc/apt/sources.list; \
    fi && \
    echo "已配置APT源:" && \
    cat /etc/apt/sources.list

# 安装系统依赖（使用国内源）
RUN apt-get update && \
    apt-get install -y \
    gcc \
    g++ \
    curl \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-eng \
    android-tools-adb \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 配置pip国内源并安装Python依赖
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "docker_main:app", "--host", "0.0.0.0", "--port", "8000"]
