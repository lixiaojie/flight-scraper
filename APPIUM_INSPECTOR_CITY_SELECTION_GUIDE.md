# Appium Inspector 连接配置 - 城市选择调试指南

## 📋 连接信息

### Appium Server 配置

在 Appium Inspector 中配置以下服务器信息：

- **Remote Host**: `localhost` 或 `127.0.0.1`
- **Remote Port**: `4723`
- **Remote Path**: `/` (Appium 3.x 不需要 `/wd/hub`)

> **注意**: 如果 Appium 在 Docker 中运行，端口已经映射到主机，所以使用 `localhost:4723` 即可。

---

## 📋 Desired Capabilities 配置

### 方法1：直接复制 JSON（推荐）

在 Appium Inspector 的 **Desired Capabilities** 标签页中，选择 **JSON** 格式，然后粘贴以下配置：

```json
{
  "platformName": "Android",
  "appium:automationName": "UiAutomator2",
  "appium:udid": "emulator-5554",
  "appium:deviceName": "Android Emulator",
  "appium:platformVersion": "16",
  "appium:noReset": true,
  "appium:fullReset": false,
  "appium:autoGrantPermissions": true,
  "appium:newCommandTimeout": 300,
  "appium:adbExecTimeout": 120000,
  "appium:uiautomator2ServerInstallTimeout": 120000,
  "appium:uiautomator2ServerLaunchTimeout": 120000,
  "appium:remoteAdbHost": "host.docker.internal",
  "appium:remoteAdbPort": 5037
}
```

### 方法2：从配置文件导入

项目根目录已包含 `appium_inspector_config.json` 文件，可以直接导入。

---

## 🔍 城市选择元素识别指南

### 步骤1：启动 12306 应用并进入空铁联运页面

1. 连接设备后，在 Appium Inspector 中启动 12306 应用
2. 导航到空铁联运页面（应该能看到出发城市和到达城市的输入框）

### 步骤2：识别出发城市元素

在 Appium Inspector 中查找出发城市元素时，关注以下属性：

#### 关键识别属性（按优先级）：

1. **resource-id**（最可靠）
   - 可能包含：`from_city`, `departure_city`, `fromCity`, `出发城市`, `city_from` 等关键词
   - 示例：`com.MobileTicket:id/from_city`

2. **content-desc**（次可靠）
   - 可能包含：`出发城市`, `from city`, `出发` 等关键词
   - 示例：`出发城市`

3. **text**（城市名称）
   - 显示当前选择的城市名称（如：`北京`, `上海`, `西安` 等）
   - 注意：这个值会变化，不能作为唯一标识

4. **bounds**（位置信息）
   - 出发城市通常在**左侧**（x 坐标较小）
   - 示例：`[91,551][472,756]` 表示 x 从 91 到 472

5. **class**（元素类型）
   - 通常是：`android.widget.TextView` 或 `android.widget.EditText`

#### 查找方法：

在 Appium Inspector 的 **Search** 功能中，尝试以下 XPath：

```xpath
//*[contains(@resource-id, 'from') or contains(@resource-id, '出发')]
//*[contains(@content-desc, '出发') or contains(@content-desc, 'from')]
//*[@text='北京' or @text='上海' or @text='西安'][1]  // 选择第一个（左侧）
```

### 步骤3：识别到达城市元素

到达城市元素的识别方法与出发城市类似，但有以下区别：

#### 关键识别属性（按优先级）：

1. **resource-id**
   - 可能包含：`to_city`, `arrival_city`, `toCity`, `到达城市`, `city_to` 等关键词
   - 示例：`com.MobileTicket:id/to_city`

2. **content-desc**
   - 可能包含：`到达城市`, `to city`, `到达` 等关键词
   - 示例：`到达城市`

3. **bounds**（位置信息）
   - 到达城市通常在**右侧**（x 坐标较大）
   - 示例：`[611,551][992,756]` 表示 x 从 611 到 992

#### 查找方法：

```xpath
//*[contains(@resource-id, 'to') or contains(@resource-id, '到达')]
//*[contains(@content-desc, '到达') or contains(@content-desc, 'to')]
//*[@text='北京' or @text='上海' or @text='深圳'][last()]  // 选择最后一个（右侧）
```

---

## 📝 记录元素信息

在 Appium Inspector 中找到元素后，请记录以下信息：

### 出发城市元素

```json
{
  "resource-id": "记录实际的 resource-id",
  "content-desc": "记录实际的 content-desc",
  "class": "记录实际的 class",
  "text": "记录当前显示的城市名",
  "bounds": "记录实际的 bounds",
  "x坐标范围": "例如: 91-472",
  "y坐标范围": "例如: 551-756"
}
```

### 到达城市元素

```json
{
  "resource-id": "记录实际的 resource-id",
  "content-desc": "记录实际的 content-desc",
  "class": "记录实际的 class",
  "text": "记录当前显示的城市名",
  "bounds": "记录实际的 bounds",
  "x坐标范围": "例如: 611-992",
  "y坐标范围": "例如: 551-756"
}
```

---

## 🎯 调试建议

### 1. 使用 Appium Inspector 的 Selector 功能

- 点击元素后，查看右侧的 **Attributes** 面板
- 记录所有可用的属性值
- 特别关注 `resource-id` 和 `content-desc`，这些是最稳定的标识符

### 2. 使用 XPath 验证

在 Appium Inspector 的 **Search** 中测试以下 XPath：

```xpath
# 查找所有城市相关的元素
//*[contains(@resource-id, 'city') or contains(@content-desc, '城市')]

# 查找所有可点击的城市元素
//*[@clickable='true' and (contains(@resource-id, 'city') or contains(@content-desc, '城市'))]

# 根据位置筛选（左侧 = 出发，右侧 = 到达）
//*[@text='北京'][@bounds='[91,551][472,756]']  // 出发城市（左侧）
//*[@text='北京'][@bounds='[611,551][992,756]']  // 到达城市（右侧）
```

### 3. 截图对比

- 在空铁联运页面截图
- 标注出发城市和到达城市的位置
- 记录它们的坐标范围

---

## 🔧 修复脚本的建议

根据 Appium Inspector 的发现，可以优化 `scripts/city_selection.py` 中的 `find_city_element` 函数：

1. **优先使用 resource-id**：如果元素有稳定的 resource-id，优先使用
2. **使用 content-desc 作为备选**：如果没有 resource-id，使用 content-desc
3. **位置筛选作为最后手段**：只有当以上方法都失败时，才使用 x 坐标筛选

---

## 📞 反馈信息

请将 Appium Inspector 中发现的元素信息反馈，包括：

1. 出发城市和到达城市的 `resource-id`
2. 出发城市和到达城市的 `content-desc`
3. 元素的实际 `bounds` 坐标
4. 是否有其他可用的标识属性

这些信息将用于改进 `find_city_element` 函数的识别逻辑。

