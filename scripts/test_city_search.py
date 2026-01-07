#!/usr/bin/env python3
"""
测试城市搜索功能
用于调试城市选择页面的搜索方法
"""
import os
import sys
import time

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

try:
    from appium import webdriver
    from appium.options.android import UiAutomator2Options
    from appium.webdriver.common.appiumby import AppiumBy
    from selenium.common.exceptions import NoSuchElementException
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保已安装appium和selenium")
    sys.exit(1)

from city_selection import input_city_search, find_city_search_box, select_city_from_results
from utils import wait_step


def test_city_search():
    """测试城市搜索功能"""
    print("=" * 80)
    print("城市搜索功能测试")
    print("=" * 80)
    
    # 使用与主脚本相同的配置方式
    import os
    
    # 从环境变量或配置文件获取配置
    target_udid = os.getenv("SCRAPER_DEVICE_UDID", "emulator-5554")
    appium_server_url = os.getenv("APPIUM_SERVER_URL", "http://appium:4723")
    
    # 配置Appium选项（与主脚本保持一致）
    caps = {
        'platformName': 'Android',
        'appium:automationName': 'UiAutomator2',
        "appium:remoteAdbHost": "host.docker.internal",
        "appium:remoteAdbPort": "5037",
        'appium:deviceName': 'Android Emulator',
        'appium:platformVersion': '16',
        'appium:noReset': True,
        'appium:fullReset': False,
        'appium:autoGrantPermissions': True,
        'appium:newCommandTimeout': 300,
        'appium:adbExecTimeout': 120000,
    }
    
    # 设置UDID
    if target_udid:
        caps['appium:udid'] = target_udid
    
    options = UiAutomator2Options().load_capabilities(caps)
    
    print(f"\n🔗 连接到Appium服务器: {appium_server_url}")
    print(f"📱 目标设备UDID: {target_udid}")
    print(f"🔧 远程ADB主机: host.docker.internal:5037")
    
    try:
        driver = webdriver.Remote(appium_server_url, options=options)
        print("✅ 已连接到设备")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("\n请确保:")
        print("1. Appium服务器正在运行")
        print("2. 模拟器已启动并连接")
        print("3. ADB服务器在host.docker.internal:5037可访问")
        print("4. 12306应用已安装")
        print("\n提示:")
        print("- 如果使用Docker，确保ADB端口已映射")
        print("- 检查设备是否在ADB设备列表中: adb devices")
        return
    
    try:
        # 等待应用启动
        print("\n⏳ 等待应用启动...")
        time.sleep(3)
        
        # 检查当前页面
        print("\n🔍 检查当前页面...")
        try:
            page_source = driver.page_source
            if "搜索" in page_source or "请输入" in page_source:
                print("✅ 当前在城市选择页面")
            else:
                print("⚠️ 当前不在城市选择页面，请手动进入城市选择页面")
                print("按Enter键继续...")
                input()
        except Exception as e:
            print(f"⚠️ 检查页面失败: {e}")
        
        # 测试搜索功能
        test_city = "西安"
        print(f"\n🧪 测试搜索城市: {test_city}")
        print("-" * 80)
        
        # 步骤1: 查找搜索框
        print("\n步骤1: 查找搜索框")
        search_box = find_city_search_box(driver)
        if not search_box:
            print("❌ 未找到搜索框")
            return
        print("✅ 搜索框已找到")
        
        # 步骤2: 测试输入和搜索
        print(f"\n步骤2: 输入城市名称 '{test_city}' 并触发搜索")
        result = input_city_search(driver, test_city)
        if not result:
            print("❌ 搜索失败")
            return
        print("✅ 搜索已触发")
        
        # 步骤3: 等待搜索结果
        print("\n步骤3: 等待搜索结果出现...")
        time.sleep(3)
        
        # 步骤4: 检查搜索结果
        print("\n步骤4: 检查搜索结果")
        try:
            # 尝试查找包含城市名称的结果
            result_element = driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().textContains("{test_city}")')
            print(f"✅ 找到搜索结果: {result_element.text}")
        except NoSuchElementException:
            print("⚠️ 未找到搜索结果")
            print("\n当前页面内容:")
            try:
                page_source = driver.page_source
                # 打印部分页面内容用于调试
                print(page_source[:500])
            except Exception as e:
                print(f"⚠️ 获取页面内容失败: {e}")
        
        # 步骤5: 测试选择城市
        print(f"\n步骤5: 测试选择城市 '{test_city}'")
        select_result = select_city_from_results(driver, test_city)
        if select_result:
            print("✅ 城市选择成功")
        else:
            print("❌ 城市选择失败")
        
        print("\n" + "=" * 80)
        print("测试完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n按Enter键关闭连接...")
        input()
        try:
            driver.quit()
            print("✅ 连接已关闭")
        except:
            pass


if __name__ == "__main__":
    test_city_search()

