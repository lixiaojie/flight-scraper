# Appium 安装指南

## 系统要求检查

在安装 Appium 之前，需要确保以下依赖已安装：

### 1. 安装 Homebrew（如果未安装）

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

安装完成后，根据提示将 Homebrew 添加到 PATH：
```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### 2. 安装 Node.js（推荐版本 16+）

```bash
brew install node
```

验证安装：
```bash
node --version
npm --version
```

### 3. 安装 Java 11+ 

```bash
brew install openjdk@11
```

设置 JAVA_HOME 环境变量：
```bash
echo 'export JAVA_HOME=$(/usr/libexec/java_home -v 11)' >> ~/.zshrc
echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.zshrc
source ~/.zshrc
```

验证安装：
```bash
java -version
```

### 4. 安装 Android SDK（可选，如果使用 Android 模拟器）

如果使用 Android Studio 的模拟器，需要设置 ANDROID_HOME：

```bash
# Android SDK 通常位于：
# ~/Library/Android/sdk

export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/platform-tools
export PATH=$PATH:$ANDROID_HOME/tools
echo 'export ANDROID_HOME=$HOME/Library/Android/sdk' >> ~/.zshrc
echo 'export PATH=$PATH:$ANDROID_HOME/platform-tools' >> ~/.zshrc
echo 'export PATH=$PATH:$ANDROID_HOME/tools' >> ~/.zshrc
```

### 5. 安装 Appium

安装完上述依赖后，运行项目中的安装脚本：

```bash
cd /Users/admin/Downloads/flight-scraper
chmod +x scripts/install_appium.sh
./scripts/install_appium.sh
```

或者手动安装：

```bash
# 全局安装 Appium
npm install -g appium@2.0.0

# 安装 UiAutomator2 驱动（Android）
appium driver install uiautomator2

# 安装 XCUITest 驱动（iOS，仅 macOS）
appium driver install xcuitest
```

### 6. 验证安装

```bash
appium --version
appium driver list
```

### 7. 启动 Appium 服务器

使用项目提供的启动脚本：

```bash
chmod +x scripts/start_appium.sh
./scripts/start_appium.sh
```

或者直接启动：

```bash
appium --log-level info --relaxed-security
```

## 快速安装命令（一键执行）

如果所有依赖都已安装，可以直接运行：

```bash
cd /Users/admin/Downloads/flight-scraper
chmod +x scripts/install_appium.sh
./scripts/install_appium.sh
```

## 常见问题

### 端口 4723 被占用

```bash
# 查找占用端口的进程
lsof -iTCP:4723 -sTCP:LISTEN

# 停止 Appium 进程
pkill -f appium
```

### 权限问题

如果遇到权限问题，可能需要使用 sudo（不推荐）或修复 npm 权限：

```bash
# 修复 npm 全局安装权限
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.zshrc
source ~/.zshrc
```

## 使用 Docker（替代方案）

如果不想在本地安装，可以使用 Docker 运行 Appium：

```bash
# 查看 docker-compose.yml 中的 appium 服务配置
docker-compose up appium
```
