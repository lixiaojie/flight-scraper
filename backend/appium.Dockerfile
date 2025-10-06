FROM node:20-bullseye

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

# 安装 Appium
# 使用 BuildKit 缓存 npm 依赖
RUN --mount=type=cache,target=/root/.npm \
    npm install -g appium@3.0.2 && \
    appium driver install uiautomator2

WORKDIR /app

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 4723

# 启动命令：先启动 adb 服务并连接模拟器，再启动 Appium
CMD bash -lc 'adb start-server; adb connect android-emulator:5555 || true; adb devices; appium --port 4723 --log-level info'
