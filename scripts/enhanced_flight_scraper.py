#!/usr/bin/env python3
"""
增强版12306航班信息抓取脚本
包含数据库存储和API调用功能
"""

import time
import re
import requests
import json
from datetime import datetime
from lxml import etree
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class EnhancedFlightScraper:
    def __init__(self, api_base_url="http://localhost:8000"):
        """初始化增强版航班抓取器"""
        self.driver = None
        self.wait = None
        self.api_base_url = api_base_url
        
    def setup_driver(self):
        """设置Appium驱动"""
        print("🚀 初始化Appium驱动...")
        
        try:
            from appium.options.android import UiAutomator2Options
            
            options = UiAutomator2Options()
            options.platform_name = 'Android'
            options.automation_name = 'UiAutomator2'
            options.device_name = 'Android Emulator'
            options.platform_version = '16'
            options.no_reset = True
            options.full_reset = False
            options.auto_grant_permissions = True
            options.new_command_timeout = 300
            
            self.driver = webdriver.Remote('http://localhost:4723', options=options)
            self.wait = WebDriverWait(self.driver, 10)
            print("✅ Appium驱动初始化成功")
            return True
        except Exception as e:
            print(f"❌ 驱动初始化失败: {e}")
            return False
    
    def wait_step(self, seconds=2):
        """步骤间等待"""
        print(f"⏳ 等待 {seconds} 秒...")
        time.sleep(seconds)
    
    def take_screenshot_and_exit(self, reason):
        """截图并退出"""
        print(f"\n📸 截图并退出 - 原因: {reason}")
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_filename = f"enhanced_flight_scraper_error_{timestamp}.png"
            self.driver.save_screenshot(screenshot_filename)
            print(f"📸 截图已保存: {screenshot_filename}")
            
            page_source = self.driver.page_source
            source_filename = f"enhanced_flight_scraper_error_{timestamp}.xml"
            with open(source_filename, 'w', encoding='utf-8') as f:
                f.write(page_source)
            print(f"📄 页面源码已保存: {source_filename}")
            
        except Exception as e:
            print(f"⚠️ 截图保存失败: {e}")
        
        print("🔚 脚本结束")
        if self.driver:
            self.driver.quit()
    
    def step1_launch_12306(self):
        """步骤1: 重启12306应用，确保从首页开始"""
        print("\n📱 步骤1: 重启12306应用")
        
        try:
            print("🔄 终止12306应用...")
            try:
                self.driver.terminate_app("com.MobileTicket")
                print("✅ 应用已终止")
            except Exception as e:
                print(f"⚠️ 终止应用时出错: {e}")
            
            self.wait_step(2)
            
            # 检查是否回到主屏幕
            print("🔍 检查是否回到主屏幕...")
            try:
                # 检查Android主屏幕标识
                home_screen_indicators = [
                    "com.android.launcher3",
                    "com.android.launcher",
                    "com.google.android.apps.nexuslauncher",
                    "com.miui.home"
                ]
                
                current_activity = self.driver.current_activity
                print(f"📱 当前Activity: {current_activity}")
                
                is_home_screen = any(indicator in current_activity for indicator in home_screen_indicators)
                
                if is_home_screen:
                    print("✅ 已回到主屏幕")
                else:
                    print("⚠️ 未检测到主屏幕，尝试按Home键...")
                    self.driver.press_keycode(3)  # Home键
                    self.wait_step(1)
                    
                    # 再次检查
                    current_activity = self.driver.current_activity
                    is_home_screen = any(indicator in current_activity for indicator in home_screen_indicators)
                    if is_home_screen:
                        print("✅ 按Home键后已回到主屏幕")
                    else:
                        print("⚠️ 仍无法确认主屏幕状态，继续执行...")
                
            except Exception as e:
                print(f"⚠️ 检查主屏幕状态时出错: {e}")
                print("⚠️ 继续执行...")
            
            print("🚀 重新启动12306应用...")
            self.driver.activate_app("com.MobileTicket")
            print("✅ 12306应用已重启")
            
            self.wait_step()
            return True
            
        except Exception as e:
            print(f"❌ 重启12306失败: {e}")
            return False
    
    def step2_check_homepage(self):
        """步骤2: 检查主页面"""
        print("\n🏠 步骤2: 检查主页面")
        
        try:
            home_container = self.driver.find_element(AppiumBy.ID, "com.MobileTicket:id/ticket_home_content_container")
            print("✅ 主页面容器已找到")
            
            self.wait_step()
            return True
            
        except NoSuchElementException:
            print("❌ 主页面容器未找到")
            return False
        except Exception as e:
            print(f"❌ 检查主页面失败: {e}")
            return False
    
    def step3_click_air_rail_transfer(self):
        """步骤3: 点击空铁联运按钮（带循环重试）"""
        print("\n🚄 步骤3: 点击空铁联运按钮")
        
        max_attempts = 5
        for attempt in range(1, max_attempts + 1):
            print(f"🔄 尝试 {attempt}/{max_attempts}")
            
            try:
                air_rail_button = self.driver.find_element(AppiumBy.ACCESSIBILITY_ID, "空铁联运")
                air_rail_button.click()
                print("✅ 空铁联运按钮已点击")
                
                self.wait_step()
                return True
                
            except NoSuchElementException:
                print(f"⚠️ 第{attempt}次尝试：空铁联运按钮未找到")
                
                if attempt < max_attempts:
                    print("🔄 退回到步骤2，重新检查主页面...")
                    if not self.step2_check_homepage():
                        print("❌ 主页面检查失败")
                        return False
                    self.wait_step(2)
                else:
                    print("❌ 5次尝试后仍未找到空铁联运按钮")
                    self.take_screenshot_and_exit("空铁联运按钮未找到")
                    return False
                    
            except Exception as e:
                print(f"❌ 第{attempt}次尝试失败: {e}")
                if attempt >= max_attempts:
                    self.take_screenshot_and_exit(f"点击空铁联运失败: {e}")
                    return False
                self.wait_step(2)
        
        return False
    
    def step4_check_air_rail_page(self):
        """步骤4: 检查空铁联运页面"""
        print("\n✈️ 步骤4: 检查空铁联运页面")
        
        try:
            air_rail_page = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 
                                                   'new UiSelector().text("空铁联运首页")')
            print("✅ 空铁联运首页已找到")
            
            self.wait_step()
            return True
            
        except NoSuchElementException:
            print("❌ 空铁联运首页未找到")
            return False
        except Exception as e:
            print(f"❌ 检查空铁联运页面失败: {e}")
            return False
    
    def step5_click_search(self):
        """步骤5: 点击查询按钮（带页面刷新）"""
        print("\n🔍 步骤5: 点击查询按钮")
        
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            print(f"🔄 尝试 {attempt}/{max_attempts}")
            
            try:
                search_button = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 
                                                      'new UiSelector().text("查询")')
                search_button.click()
                print("✅ 查询按钮已点击")
                
                self.wait_step()
                return True
                
            except NoSuchElementException:
                print(f"⚠️ 第{attempt}次尝试：查询按钮未找到")
                
                if attempt < max_attempts:
                    print("🔄 刷新当前页面...")
                    try:
                        self.driver.refresh()
                        print("✅ 页面已刷新")
                        self.wait_step(2)
                    except Exception as e:
                        print(f"⚠️ 页面刷新失败: {e}")
                        try:
                            self.driver.back()
                            self.wait_step(1)
                            self.driver.forward()
                            print("✅ 使用前进后退刷新页面")
                        except Exception as e2:
                            print(f"⚠️ 前进后退刷新也失败: {e2}")
                else:
                    print("❌ 3次尝试后仍未找到查询按钮")
                    self.take_screenshot_and_exit("查询按钮未找到")
                    return False
                    
            except Exception as e:
                print(f"❌ 第{attempt}次尝试失败: {e}")
                if attempt >= max_attempts:
                    self.take_screenshot_and_exit(f"点击查询失败: {e}")
                    return False
                self.wait_step(2)
        
        return False
    
    def step6_check_flight_list(self):
        """步骤6: 检查航班列表页面"""
        print("\n📋 步骤6: 检查航班列表页面")
        
        try:
            flight_list = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 
                                                'new UiSelector().text("航班列表")')
            print("✅ 航班列表页面已找到")
            
            self.wait_step()
            return True
            
        except NoSuchElementException:
            print("❌ 航班列表页面未找到")
            return False
        except Exception as e:
            print(f"❌ 检查航班列表失败: {e}")
            return False
    
    def step7_extract_page_source(self):
        """步骤7: 提取页面源码"""
        print("\n📄 步骤7: 提取页面源码")
        
        try:
            page_source = self.driver.page_source
            print(f"✅ 页面源码已提取，长度: {len(page_source)} 字符")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"enhanced_flight_page_source_{timestamp}.xml"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(page_source)
            print(f"💾 页面源码已保存到: {filename}")
            
            return page_source
            
        except Exception as e:
            print(f"❌ 提取页面源码失败: {e}")
            return None
    
    def parse_flight_info(self, page_source):
        """解析航班信息（增强中文支持）"""
        print("\n🔍 解析航班信息...")
        
        try:
            root = etree.fromstring(page_source)
            flights = []
            
            # 增强的中文正则表达式模式
            # 航班号模式：支持中文+数字组合
            flight_number_patterns = [
                r'([A-Z]{2}\d{3,4})',  # 标准格式：CA1234
                r'([A-Z]\d{3,4})',     # 简化格式：A1234
                r'(\d{3,4})',           # 纯数字：1234
                r'([A-Z]{2,3}\d{2,4})'  # 扩展格式：ABC1234
            ]
            
            # 时间模式：支持多种时间格式
            time_patterns = [
                r'(\d{1,2}:\d{2})',           # 标准格式：08:30
                r'(\d{1,2}时\d{2}分)',         # 中文格式：8时30分
                r'(\d{1,2}点\d{2}分)',         # 中文格式：8点30分
                r'(\d{1,2}:\d{2}:\d{2})'      # 带秒格式：08:30:00
            ]
            
            # 价格模式：支持多种货币符号和中文
            price_patterns = [
                r'[¥￥]?(\d+(?:\.\d+)?)元?',    # 人民币：¥580元
                r'(\d+(?:\.\d+)?)元',          # 纯数字+元：580元
                r'[¥￥](\d+(?:\.\d+)?)',       # 符号+数字：¥580
                r'(\d+(?:\.\d+)?)块',         # 口语化：580块
                r'(\d+(?:\.\d+)?)块钱'         # 口语化：580块钱
            ]
            
            # 机场代码模式：支持中文机场名
            airport_patterns = [
                r'([A-Z]{3})',                 # 标准三字码：PEK
                r'([A-Z]{4})',                 # 四字码：ZSPD
                r'(北京|上海|广州|深圳|成都|重庆|西安|杭州|南京|武汉|长沙|郑州|济南|青岛|大连|沈阳|哈尔滨|长春|石家庄|太原|呼和浩特|银川|兰州|西宁|乌鲁木齐|拉萨|昆明|贵阳|南宁|海口|三亚|福州|厦门|南昌|合肥|苏州|无锡|常州|镇江|扬州|泰州|南通|盐城|淮安|连云港|徐州|宿迁|温州|台州|金华|衢州|丽水|舟山|嘉兴|湖州|绍兴|宁波|杭州)',  # 中文城市名
            ]
            
            # 航空公司模式：支持中文名称
            airline_patterns = [
                r'(中国国际航空|国航|CA)',
                r'(中国东方航空|东航|MU)',
                r'(中国南方航空|南航|CZ)',
                r'(海南航空|海航|HU)',
                r'(四川航空|川航|3U)',
                r'(春秋航空|春秋|9C)',
                r'(首都航空|首航|JD)',
                r'(吉祥航空|吉祥|HO)',
                r'(厦门航空|厦航|MF)',
                r'(深圳航空|深航|ZH)',
                r'(山东航空|山航|SC)',
                r'(天津航空|天航|GS)',
                r'(华夏航空|华夏|G5)',
                r'(长龙航空|长龙|GJ)',
                r'(九元航空|九元|AQ)',
                r'(东海航空|东海|DZ)',
                r'(青岛航空|青岛|QW)',
                r'(瑞丽航空|瑞丽|DR)',
                r'(红土航空|红土|A6)',
                r'(长安航空|长安|9H)'
            ]
            
            # 提取航班信息
            flight_numbers = []
            for pattern in flight_number_patterns:
                matches = re.findall(pattern, page_source)
                flight_numbers.extend(matches)
            
            times = []
            for pattern in time_patterns:
                matches = re.findall(pattern, page_source)
                times.extend(matches)
            
            prices = []
            for pattern in price_patterns:
                matches = re.findall(pattern, page_source)
                prices.extend(matches)
            
            airports = []
            for pattern in airport_patterns:
                matches = re.findall(pattern, page_source)
                airports.extend(matches)
            
            airlines = []
            for pattern in airline_patterns:
                matches = re.findall(pattern, page_source)
                airlines.extend(matches)
            
            print(f"📊 解析统计:")
            print(f"  - 航班号: {len(flight_numbers)} 个")
            print(f"  - 时间: {len(times)} 个")
            print(f"  - 价格: {len(prices)} 个")
            print(f"  - 机场: {len(airports)} 个")
            print(f"  - 航空公司: {len(airlines)} 个")
            
            # 组合航班信息
            max_flights = min(10, len(flight_numbers), len(times) // 2, len(prices))
            
            for i in range(max_flights):
                # 智能匹配航空公司
                airline = self.get_airline_from_code(flight_numbers[i]) if i < len(flight_numbers) else "未知航空公司"
                if i < len(airlines):
                    airline = airlines[i]
                
                # 智能匹配机场
                departure_airport = airports[i*2] if i*2 < len(airports) else "未知机场"
                arrival_airport = airports[i*2+1] if i*2+1 < len(airports) else "未知机场"
                
                # 处理中文机场名
                departure_airport = self.translate_airport_name(departure_airport)
                arrival_airport = self.translate_airport_name(arrival_airport)
                
                flight_info = {
                    'airline': airline,
                    'flight_number': flight_numbers[i] if i < len(flight_numbers) else '',
                    'departure_time': times[i*2] if i*2 < len(times) else '',
                    'departure_airport': departure_airport,
                    'arrival_time': times[i*2+1] if i*2+1 < len(times) else '',
                    'arrival_airport': arrival_airport,
                    'price': float(prices[i]) if i < len(prices) and prices[i] else 0.0,
                    'currency': 'CNY',
                    'source': '12306',
                    'scrape_time': datetime.now().isoformat(),
                    'notes': f'抓取时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                }
                flights.append(flight_info)
            
            print(f"✅ 解析完成，找到 {len(flights)} 个航班信息")
            return flights
            
        except Exception as e:
            print(f"❌ 解析航班信息失败: {e}")
            return []
    
    def get_airline_from_code(self, flight_number):
        """根据航班号获取航空公司"""
        airline_codes = {
            'CA': '中国国际航空',
            'MU': '中国东方航空',
            'CZ': '中国南方航空',
            'HU': '海南航空',
            '3U': '四川航空',
            '9C': '春秋航空',
            'JD': '首都航空',
            'HO': '吉祥航空'
        }
        
        if len(flight_number) >= 2:
            code = flight_number[:2]
            return airline_codes.get(code, '未知航空公司')
        return '未知航空公司'
    
    def translate_airport_name(self, airport_name):
        """翻译机场名称"""
        airport_translations = {
            # 主要城市机场
            '北京': 'PEK',
            '上海': 'SHA',
            '广州': 'CAN',
            '深圳': 'SZX',
            '成都': 'CTU',
            '重庆': 'CKG',
            '西安': 'XIY',
            '杭州': 'HGH',
            '南京': 'NKG',
            '武汉': 'WUH',
            '长沙': 'CSX',
            '郑州': 'CGO',
            '济南': 'TNA',
            '青岛': 'TAO',
            '大连': 'DLC',
            '沈阳': 'SHE',
            '哈尔滨': 'HRB',
            '长春': 'CGQ',
            '石家庄': 'SJW',
            '太原': 'TYN',
            '呼和浩特': 'HET',
            '银川': 'INC',
            '兰州': 'LHW',
            '西宁': 'XNN',
            '乌鲁木齐': 'URC',
            '拉萨': 'LXA',
            '昆明': 'KMG',
            '贵阳': 'KWE',
            '南宁': 'NNG',
            '海口': 'HAK',
            '三亚': 'SYX',
            '福州': 'FOC',
            '厦门': 'XMN',
            '南昌': 'KHN',
            '合肥': 'HFE',
            '苏州': 'SZV',
            '无锡': 'WUX',
            '常州': 'CZX',
            '镇江': 'ZJS',
            '扬州': 'YTY',
            '泰州': 'YTY',
            '南通': 'NTG',
            '盐城': 'YNZ',
            '淮安': 'HIA',
            '连云港': 'LYG',
            '徐州': 'XUZ',
            '宿迁': 'XUZ',
            '温州': 'WNZ',
            '台州': 'HYN',
            '金华': 'YIW',
            '衢州': 'JUZ',
            '丽水': 'LZY',
            '舟山': 'HSN',
            '嘉兴': 'JIA',
            '湖州': 'HZH',
            '绍兴': 'SXZ',
            '宁波': 'NGB',
            '杭州': 'HGH'
        }
        
        # 如果是中文城市名，转换为机场代码
        if airport_name in airport_translations:
            return airport_translations[airport_name]
        
        # 如果已经是机场代码，直接返回
        if len(airport_name) == 3 and airport_name.isupper():
            return airport_name
        
        # 其他情况返回原名称
        return airport_name
    
    def save_to_database(self, flights):
        """保存航班数据到数据库"""
        print("\n💾 保存航班数据到数据库...")
        
        try:
            # 调用API保存数据
            url = f"{self.api_base_url}/api/flights/batch-save"
            data = {
                "flights": flights,
                "source": "12306"
            }
            
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 成功保存 {result['saved_count']} 条航班数据到数据库")
                return True
            else:
                print(f"❌ 保存到数据库失败: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
        except Exception as e:
            print(f"❌ 保存数据失败: {e}")
            return False
    
    def save_flight_data(self, flights):
        """保存航班数据到文件"""
        if not flights:
            print("❌ 没有航班数据可保存")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_flight_data_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(flights, f, ensure_ascii=False, indent=2)
            
            print(f"💾 航班数据已保存到: {filename}")
            
        except Exception as e:
            print(f"❌ 保存航班数据失败: {e}")
    
    def run_scraping(self):
        """运行完整的抓取流程"""
        print("🚀 开始增强版12306航班信息抓取")
        print("=" * 50)
        
        # 创建任务记录
        task_id = None
        try:
            # 创建任务记录
            task_response = requests.post(
                f"{self.api_base_url}/api/tasks",
                json={
                    "task_name": f"12306航班抓取_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "task_type": "flight_scraper",
                    "source": "12306",
                    "config": {
                        "app_restart": True,
                        "chinese_parsing": True,
                        "retry_mechanism": True
                    }
                },
                timeout=10
            )
            
            if task_response.status_code == 200:
                task_data = task_response.json()
                task_id = task_data['id']
                print(f"📝 任务记录已创建: {task_id}")
            else:
                print(f"⚠️ 创建任务记录失败: {task_response.status_code}")
        
        except Exception as e:
            print(f"⚠️ 创建任务记录时出错: {e}")
        
        try:
            # 初始化驱动
            if not self.setup_driver():
                if task_id:
                    self.update_task_result(task_id, False, 0, "驱动初始化失败")
                return False
            
            # 执行抓取步骤
            steps = [
                self.step1_launch_12306,
                self.step2_check_homepage,
                self.step3_click_air_rail_transfer,
                self.step4_check_air_rail_page,
                self.step5_click_search,
                self.step6_check_flight_list
            ]
            
            for i, step in enumerate(steps):
                if not step():
                    error_msg = f"步骤{i+1}执行失败"
                    print(f"❌ {error_msg}")
                    if task_id:
                        self.update_task_result(task_id, False, 0, error_msg)
                    return False
            
            # 提取页面源码
            page_source = self.step7_extract_page_source()
            if not page_source:
                print("❌ 页面源码提取失败")
                if task_id:
                    self.update_task_result(task_id, False, 0, "页面源码提取失败")
                return False
            
            # 解析航班信息
            flights = self.parse_flight_info(page_source)
            
            if flights:
                # 按价格排序
                flights.sort(key=lambda x: x['price'])
                print(f"📊 航班数据已按价格排序，最低价格: {flights[0]['price']} 元")
                
                # 保存到文件
                self.save_flight_data(flights)
                
                # 保存到数据库
                db_success = self.save_to_database(flights)
                
                # 更新任务结果
                if task_id:
                    self.update_task_result(task_id, db_success, len(flights), None if db_success else "数据库保存失败")
                
                print("\n🎉 增强版航班信息抓取完成！")
                print(f"📈 统计信息:")
                print(f"   - 航班数量: {len(flights)}")
                print(f"   - 价格范围: {min(f['price'] for f in flights)} - {max(f['price'] for f in flights)} 元")
                print(f"   - 平均价格: {sum(f['price'] for f in flights) / len(flights):.2f} 元")
                
                return True
            else:
                print("❌ 未找到航班信息")
                if task_id:
                    self.update_task_result(task_id, False, 0, "未找到航班信息")
                return False
            
        except Exception as e:
            print(f"❌ 抓取过程出错: {e}")
            if task_id:
                self.update_task_result(task_id, False, 0, str(e))
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
                print("🔚 驱动已关闭")
    
    def update_task_result(self, task_id: int, success: bool, flights_count: int, error_message: str = None):
        """更新任务结果"""
        try:
            response = requests.put(
                f"{self.api_base_url}/api/tasks/{task_id}/result",
                json={
                    "success": success,
                    "flights_count": flights_count,
                    "error_message": error_message
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ 任务结果已更新: {task_id}")
            else:
                print(f"⚠️ 更新任务结果失败: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ 更新任务结果时出错: {e}")

def main():
    """主函数"""
    scraper = EnhancedFlightScraper()
    success = scraper.run_scraping()
    
    if success:
        print("\n✅ 增强版抓取任务完成！")
        print("🌐 请访问前端页面查看结果: http://localhost:3000/flight-results")
    else:
        print("\n❌ 增强版抓取任务失败！")

if __name__ == "__main__":
    main()
