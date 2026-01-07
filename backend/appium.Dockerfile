FROM node:20-bullseye

# 配置国内APT源
RUN echo "deb https://mirrors.ustc.edu.cn/debian/ bullseye main" > /etc/apt/sources.list && \
    echo "deb https://mirrors.ustc.edu.cn/debian/ bullseye-updates main" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.ustc.edu.cn/debian-security/ bullseye-security main" >> /etc/apt/sources.list

# 安装 Java 和其他系统依赖
# 安装 Java 与常用工具
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    openjdk-11-jre-headless \
    unzip \
    curl \
    bash \
    git \
    ca-certificates && rm -rf /var/lib/apt/lists/*

# 安装 Android platform-tools（adb）
ENV ANDROID_HOME=/opt/android-sdk \
    ANDROID_SDK_ROOT=/opt/android-sdk \
    PATH=/opt/android-sdk/platform-tools:$PATH

# 安装 adb（发行版包）以及补全 SDK 目录结构（uiautomator2需要 ANDROID_SDK_ROOT 存在）
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y android-tools-adb && rm -rf /var/lib/apt/lists/* && \
    mkdir -p "$ANDROID_SDK_ROOT/platform-tools" && \
    if [ ! -x "$ANDROID_SDK_ROOT/platform-tools/adb" ]; then ln -s /usr/bin/adb "$ANDROID_SDK_ROOT/platform-tools/adb"; fi && \
    ls -la "$ANDROID_SDK_ROOT" "$ANDROID_SDK_ROOT/platform-tools"

# 配置npm国内源并安装 Appium
RUN npm config set registry https://registry.npmmirror.com && \
    npm install -g appium@3.0.2 && \
    appium driver install uiautomator2 && \
    appium plugin install inspector

WORKDIR /app

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 4723

# 通过主机 ADB server 与 Android Studio 模拟器通信（host.docker.internal:5037）
# 或者在服务器端使用 Waydroid/远程 ADB（通过 ADB_CONNECT_TARGET=host:port 指定）
ENV ANDROID_ADB_SERVER_HOST=host.docker.internal \
    ANDROID_ADB_SERVER_PORT=5037 \
    ADB_SERVER_SOCKET=tcp:host.docker.internal:5037 \
    ADB_HOST=host.docker.internal \
    ADB_PORT=5037 \
    ADB_CONNECT_TARGET=""

# 启动命令：
# - 若设置 ADB_CONNECT_TARGET（例如 192.168.0.10:5555 或 waydroid:5555），则在容器内启动 adb 并连接目标
# - 否则，直接使用主机 ADB（macOS 开发）
CMD ["bash","-lc","if [ -n '$ADB_CONNECT_TARGET' ]; then echo Using in-container ADB; echo connecting to $ADB_CONNECT_TARGET; adb kill-server || true; adb start-server; adb connect $ADB_CONNECT_TARGET || true; adb devices; else echo Using host ADB at $ANDROID_ADB_SERVER_HOST:$ANDROID_ADB_SERVER_PORT; adb -H $ANDROID_ADB_SERVER_HOST -P $ANDROID_ADB_SERVER_PORT devices || adb devices; fi; appium --port 4723 --log-level info --use-plugins inspector --allow-cors"]
