#!/usr/bin/env python3
"""
12306航班信息抓取自动化脚本
使用Appium自动化Android应用，抓取航班信息
"""

import time
import re
import os
import sys
import requests
import json
from datetime import datetime
import argparse
from lxml import etree
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 添加带时间戳的打印函数


def tprint(*args, **kwargs):
    """带时间戳的打印函数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}]", *args, **kwargs)


def _load_scraper_config() -> dict:
    """读取统一配置文件（可选），用于补充环境变量。"""
    cfg_path = os.getenv("SCRAPER_CONFIG_PATH")
    if not cfg_path:
        return {}
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg if isinstance(cfg, dict) else {}
    except Exception:
        return {}


# 新增：编排入口所需模块
try:
    from .device_connection import connect_device
    from .page_capture import navigate_and_search, smart_scroll_and_capture
    from .parser import parse_and_save, parse_page_source
except Exception:
    # 兼容脚本直接运行
    from device_connection import connect_device
    from page_capture import navigate_and_search, smart_scroll_and_capture
    from parser import parse_and_save, parse_page_source, _get_airline_from_code


class FlightScraper12306:
    def __init__(self):
        """模块化编排入口：读取配置，连接设备，导航抓取，解析保存。"""
        self.driver = None
        # 输出与配置
        self.output_dir = os.getenv(
            "SCRAPER_OUTPUT_DIR", os.path.join(
                os.getcwd(), "results"))
        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except Exception:
            self.output_dir = os.getcwd()
        self.from_city = os.getenv("SCRAPER_FROM_CITY", "")
        self.to_city = os.getenv("SCRAPER_TO_CITY", "")
        self.depart_date = os.getenv("SCRAPER_DEPART_DATE", "")
        self.api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        self.task_id = None
        
    def setup_driver(self):
        """设置Appium驱动"""
        print("🚀 初始化Appium驱动...")
        
        # 连接配置
        desired_caps = {
            'platformName': 'Android',
            'appium:automationName': 'UiAutomator2',
            "appium:remoteAdbHost": "host.docker.internal",
            "appium:remoteAdbPort": "5037",
            'appium:deviceName': 'Android Emulator',
            'appium:platformVersion': '16',
            'appium:noReset': True,
            'appium:fullReset': False,
            'appium:autoGrantPermissions': True,
            'appium:newCommandTimeout': 300
        }
        
        try:
            # 创建驱动（Appium Python Client 3.x 推荐写法）
            from appium.options.android import UiAutomator2Options

            target_udid = os.getenv("SCRAPER_DEVICE_UDID")
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
            if target_udid:
                caps['appium:udid'] = target_udid
            options = UiAutomator2Options().load_capabilities(caps)

            server_url = os.getenv(
                "APPIUM_SERVER_URL",
                "http://localhost:4723")
            self.driver = webdriver.Remote(server_url, options=options)
            # 可选：等待器如有需要可在各模块内部创建
            print("✅ Appium驱动初始化成功")
            return True
        except Exception as e:
            print(f"❌ 驱动初始化失败: {e}")
            return False
    
    def wait_step(self, seconds=2):
        """步骤间等待"""
        print(f"⏳ 等待 {seconds} 秒...")
        time.sleep(seconds)
    
    def update_task_status(self, step_name, status="running"):
        """更新任务状态"""
        if not self.task_id:
            return
        
        try:
            url = f"{self.api_base_url}/api/tasks/{self.task_id}/status"
            data = {
                "current_step": step_name,
                "status": status
            }
            response = requests.patch(url, json=data, timeout=5)
            if response.status_code == 200:
                tprint(f"✅ 任务状态已更新: {step_name}")
            else:
                tprint(f"⚠️ 状态更新失败: {response.status_code}")
        except Exception as e:
            tprint(f"⚠️ 更新任务状态时出错: {e}")
    
    def set_task_id(self, task_id):
        """设置任务ID"""
        self.task_id = task_id
        tprint(f"📋 任务ID已设置: {task_id}")
    
    def take_screenshot_and_exit(self, reason):
        """截图并退出"""
        print(f"\n📸 截图并退出 - 原因: {reason}")
        
        try:
            # 截图
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_filename = os.path.join(
                self.output_dir, f"flight_scraper_error_{timestamp}.png")
            self.driver.save_screenshot(screenshot_filename)
            print(f"📸 截图已保存: {screenshot_filename}")
            
            # 保存页面源码
            page_source = self.driver.page_source
            source_filename = os.path.join(
                self.output_dir, f"flight_scraper_error_{timestamp}.xml")
            with open(source_filename, 'w', encoding='utf-8') as f:
                f.write(page_source)
            print(f"📄 页面源码已保存: {source_filename}")
            
        except Exception as e:
            print(f"⚠️ 截图保存失败: {e}")
        
        print("🔚 脚本结束")
        if self.driver:
            self.driver.quit()
    
    # 旧版步骤方法已迁移至 page_capture 模块
    
    def parse_flight_info(self, page_source):
        """解析航班信息"""
        print("\n🔍 解析航班信息...")
        
        try:
            # 首先尝试使用高级方法解析
            print("🔄 使用高级方法解析航班信息...")
            flights = self.extract_flight_info_advanced(page_source)
            
            if flights:
                print(f"✅ 高级方法找到 {len(flights)} 个航班信息")
                return flights
            
            # 如果高级方法失败，尝试使用备用方法（正则表达式）直接解析
            print("🔄 使用正则表达式方法解析航班信息...")
            flights = self.extract_flight_info_alternative(page_source)
            
            if flights:
                print(f"✅ 正则表达式方法找到 {len(flights)} 个航班信息")
                return flights
            
            # 如果正则表达式方法失败，尝试XPath方法
            print("🔄 尝试XPath方法解析航班信息...")
            root = etree.fromstring(page_source.encode(
                'utf-8') if isinstance(page_source, str) else page_source)
            
            # 更广泛的XPath选择器
            xpath_selectors = [
                '//*[contains(@class, "flight")]',
                '//*[contains(@text, "航班")]',
                '//*[contains(@text, "出发")]',
                '//*[contains(@text, "到达")]',
                '//*[contains(@text, "时间")]',
                '//*[contains(@text, "价格")]',
                '//*[contains(@text, "元")]',
                '//*[contains(@text, "￥")]',
                '//*[contains(@text, "¥")]'
            ]
            
            flight_elements = []
            for selector in xpath_selectors:
                elements = root.xpath(selector)
                flight_elements.extend(elements)
                if elements:
                    print(f"✅ XPath选择器 '{selector}' 找到 {len(elements)} 个元素")
            
            # 去重
            flight_elements = list(set(flight_elements))
            print(f"📊 总共找到 {len(flight_elements)} 个候选元素")
            
            for element in flight_elements:
                flight_info = self.extract_flight_data(element)
                if flight_info:
                    flights.append(flight_info)
            
            print(f"✅ 解析完成，找到 {len(flights)} 个航班信息")
            return flights
            
        except Exception as e:
            print(f"❌ 解析航班信息失败: {e}")
            return []
    
    def extract_flight_data(self, element):
        """从元素中提取航班数据"""
        try:
            flight_info = {
                'airline': '',
                'flight_number': '',
                'departure_date': '',
                'departure_time': '',
                'departure_airport': '',
                'arrival_time': '',
                'arrival_airport': '',
                'flight_duration': '',
                'price': ''
            }
            
            # 提取文本内容（兼容 @text 与节点文本）
            text = (
                element.get(
                    'text',
                    '') or (
                    ''.join(
                        element.itertext()) if hasattr(
                        element,
                        'itertext') else '')).strip()
            
            # 使用正则表达式提取航班信息
            # 航班号模式: 如 CA1234, MU5678，支持前置中文航空公司名
            flight_pattern = r'(?:[\u4e00-\u9fa5]{2,6})?\s*([A-Z]{2}\d{3,4})'
            flight_match = re.search(flight_pattern, text)
            if flight_match:
                flight_info['flight_number'] = flight_match.group(1)
            
            # 时间模式: 如 08:30, 14:25
            time_pattern = r'(\d{1,2}:\d{2})'
            times = re.findall(time_pattern, text)
            if len(times) >= 2:
                flight_info['departure_time'] = times[0]
                flight_info['arrival_time'] = times[1]
                
                # 计算飞行时长
                try:
                    dep_hour, dep_min = map(int, times[0].split(':'))
                    arr_hour, arr_min = map(int, times[1].split(':'))
                    
                    dep_minutes = dep_hour * 60 + dep_min
                    arr_minutes = arr_hour * 60 + arr_min
                    
                    # 处理跨天情况
                    if arr_minutes < dep_minutes:
                        arr_minutes += 24 * 60
                    
                    duration_minutes = arr_minutes - dep_minutes
                    hours = duration_minutes // 60
                    minutes = duration_minutes % 60
                    
                    flight_info['flight_duration'] = f"{hours}h{minutes}m"
                except BaseException:
                    pass
            
            # 价格模式: 支持 ￥/¥/CNY 与 元，整数或小数
            price_pattern = r'(?:[¥￥]|CNY)\s*([0-9]+(?:\.[0-9]{1,2})?)|([0-9]+(?:\.[0-9]{1,2})?)\s*元'
            price_match = re.search(price_pattern, text)
            if price_match:
                flight_info['price'] = price_match.group(
                    1) or price_match.group(2)
            
            # 出发日期提取
            date_patterns = [
                r'(\d{1,2}月\d{1,2}日)',
                r'(\d{4}年\d{1,2}月\d{1,2}日)',
                r'(\d{1,2}/\d{1,2})',
                r'(\d{4}-\d{1,2}-\d{1,2})'
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, text)
                if date_match:
                    flight_info['departure_date'] = date_match.group(1)
                    break
            
            # 如果没有找到日期，使用环境变量中的日期
            if not flight_info['departure_date']:
                depart_date = os.getenv('SCRAPER_DEPART_DATE', '')
                if depart_date:
                    flight_info['departure_date'] = depart_date

            # 机场与航站楼信息（需要根据实际页面结构调整）
            airport_pattern_iata = r'([A-Z]{3})'
            airports = re.findall(airport_pattern_iata, text)
            if len(airports) >= 2:
                flight_info['departure_airport'] = airports[0]
                flight_info['arrival_airport'] = airports[1]
                flight_info['departure_airport_name'] = self.get_airport_name(
                    airports[0])
                flight_info['arrival_airport_name'] = self.get_airport_name(
                    airports[1])
                # 航站楼：优先从整页源码匹配（依赖机场中文名）
                dep_name = flight_info['departure_airport_name']
                arr_name = flight_info['arrival_airport_name']
                dep_t, arr_t = self.extract_terminals_from_page(
                    page_source, dep_name, arr_name)
                flight_info['departure_terminal'] = dep_t
                flight_info['arrival_terminal'] = arr_t
            else:
                # 简单中文提取（例如 “上海 虹桥 出发” / “北京 首都 到达”）
                dep_match = re.search(
                    r'(出发|始发)[\s\S]{0,6}([\u4e00-\u9fa5]{2,8})', text)
                arr_match = re.search(
                    r'(到达|抵达)[\s\S]{0,6}([\u4e00-\u9fa5]{2,8})', text)
                if dep_match:
                    flight_info['departure_airport'] = dep_match.group(2)
                if arr_match:
                    flight_info['arrival_airport'] = arr_match.group(2)
                flight_info['departure_airport_name'] = flight_info['departure_airport']
                flight_info['arrival_airport_name'] = flight_info['arrival_airport']
                # 航站楼：优先从整页源码匹配（依赖机场中文名）
                dep_name = flight_info.get('departure_airport_name', '')
                arr_name = flight_info.get('arrival_airport_name', '')
                dep_t, arr_t = self.extract_terminals_from_page(
                    page_source, dep_name, arr_name)
                flight_info['departure_terminal'] = dep_t
                flight_info['arrival_terminal'] = arr_t

            # 航空公司中文别名到代码映射
            airline_alias = {
                '国航': 'CA', '中国国际航空': 'CA',
                '东航': 'MU', '中国东方航空': 'MU',
                '南航': 'CZ', '中国南方航空': 'CZ',
                '海航': 'HU', '海南航空': 'HU',
                '川航': '3U', '四川航空': '3U',
                '春秋': '9C', '春秋航空': '9C',
                '首都航空': 'JD',
                '吉祥': 'HO', '吉祥航空': 'HO',
            }
            if not flight_info['flight_number']:
                # 尝试仅凭中文别名推断
                for name, code in airline_alias.items():
                    if name in text:
                        flight_info['airline'] = name
                        break
            else:
                # 根据航司代码反推中文名
                code = flight_info['flight_number'][:2]
                for name, c in airline_alias.items():
                    if c == code:
                        flight_info['airline'] = name
                        break
            
            return flight_info if any(flight_info.values()) else None
            
        except Exception as e:
            print(f"⚠️ 提取航班数据失败: {e}")
            return None
    
    def extract_flight_info_alternative(self, page_source):
        """备用方法提取航班信息"""
        print("🔄 使用备用方法提取航班信息...")
        
        flights = []
        
        try:
            # 使用正则表达式直接从页面源码中提取
            # 航班号（带中文别名也可）
            flight_numbers = re.findall(
                r'(?:[\u4e00-\u9fa5]{2,6})?\s*([A-Z]{2}\d{3,4})', page_source)
            print(f"📊 找到 {len(flight_numbers)} 个航班号")
            
            # 时间
            times = re.findall(r'(\d{1,2}:\d{2})', page_source)
            print(f"📊 找到 {len(times)} 个时间")
            
            # 价格（￥/元/CNY，整数或小数）
            prices = []
            for m in re.finditer(
                r'(?:[¥￥]|CNY)\s*([0-9]+(?:\.[0-9]{1,2})?)|([0-9]+(?:\.[0-9]{1,2})?)\s*元',
                    page_source):
                prices.append(m.group(1) or m.group(2))
            print(f"📊 找到 {len(prices)} 个价格")
            
            # 机场代码
            airports = re.findall(r'([A-Z]{3})', page_source)
            print(f"📊 找到 {len(airports)} 个机场代码")
            
            # 出发日期
            dates = re.findall(
                r'(\d{1,2}月\d{1,2}日|\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}/\d{1,2}|\d{4}-\d{1,2}-\d{1,2})',
                page_source)
            print(f"📊 找到 {len(dates)} 个日期")
            
            # 组合航班信息 - 处理所有找到的时间对，即使没有航班号
            time_pairs = []
            for i in range(0, len(times), 2):
                if i + 1 < len(times):
                    time_pairs.append((times[i], times[i + 1]))
            
            max_flights = min(len(time_pairs), 20)  # 最多处理20个航班
            print(f"🔄 找到 {len(time_pairs)} 个时间对，处理前 {max_flights} 个航班...")
            
            for i, (dep_time, arr_time) in enumerate(time_pairs[:max_flights]):
                # 尝试获取对应的航班号，如果没有则跳过不规范的航班
                if i < len(flight_numbers):
                    flight_num = flight_numbers[i]
                else:
                    # 跳过没有航班号的不规范航班（通常是第5个及以后的航班）
                    print(
                        f"⚠️ 跳过第{i + 1}个航班：无标准航班号，时间 {dep_time} -> {arr_time}")
                    continue
                
                # 验证航班号格式
                if not re.match(r'^[A-Z]{2}\d{3,4}$', flight_num):
                    print(f"⚠️ 跳过不规范航班号：{flight_num}")
                    continue
                
                # 创建一个简单的上下文用于解析
                simple_context = f"{flight_num} {dep_time} {arr_time} {prices[i] if i < len(prices) else ''}"
                
                flight_info = {
                    'airline': self.get_airline_from_code(flight_num),
                    'flight_number': flight_num,
                    'is_shared_flight': self.detect_shared_flight(flight_num),
                    'aircraft_type': self.extract_aircraft_type_from_page(page_source, flight_num),
                    # 优先使用环境变量中的出发日期，如果环境变量为空则从页面提取
                    'departure_date': self.depart_date if self.depart_date else (dates[0] if dates else ''),
                    'departure_time': dep_time,
                    'departure_airport': airports[i * 2] if i * 2 < len(airports) else '',
                    # 优先使用环境变量中的出发城市，如果环境变量为空则从机场代码提取
                    'departure_city': self.from_city if self.from_city else (self.get_city_from_airport(airports[i * 2] if i * 2 < len(airports) else '')),
                    'arrival_time': arr_time,
                    'arrival_airport': airports[i * 2 + 1] if i * 2 + 1 < len(airports) else '',
                    # 优先使用环境变量中的到达城市，如果环境变量为空则从机场代码提取
                    'arrival_city': self.to_city if self.to_city else (self.get_city_from_airport(airports[i * 2 + 1] if i * 2 + 1 < len(airports) else '')),
                    'flight_duration': '',
                    'has_stopover': self.detect_stopover(simple_context),
                    'stopover_city': self.extract_stopover_city(simple_context),
                    'stopover_airport': self.extract_stopover_airport(simple_context),
                    'price': prices[i] if i < len(prices) else '',
                    'currency': 'CNY',
                    'cabin_class': self.extract_cabin_class(simple_context),
                    'discount_rate': self.extract_discount_rate(simple_context),
                    'original_price': self.extract_original_price(simple_context),
                    'source': '12306',
                    'status': 'active'
                }

                # 中文机场名
                if flight_info['departure_airport']:
                    flight_info['departure_airport_name'] = self.get_airport_name(
                        flight_info['departure_airport'])
                else:
                    flight_info['departure_airport_name'] = ''
                if flight_info['arrival_airport']:
                    flight_info['arrival_airport_name'] = self.get_airport_name(
                        flight_info['arrival_airport'])
                else:
                    flight_info['arrival_airport_name'] = ''

                # 航站楼：优先从整页源码匹配（依赖机场中文名）
                dep_name = flight_info.get('departure_airport_name', '')
                arr_name = flight_info.get('arrival_airport_name', '')
                dep_t, arr_t = self.extract_terminals_from_page(
                    page_source, dep_name, arr_name)
                flight_info['departure_terminal'] = dep_t
                flight_info['arrival_terminal'] = arr_t
                
                # 计算飞行时长
                if flight_info['departure_time'] and flight_info['arrival_time']:
                    try:
                        dep_hour, dep_min = map(
                            int, flight_info['departure_time'].split(':'))
                        arr_hour, arr_min = map(
                            int, flight_info['arrival_time'].split(':'))
                        
                        dep_minutes = dep_hour * 60 + dep_min
                        arr_minutes = arr_hour * 60 + arr_min
                        
                        # 处理跨天情况
                        if arr_minutes < dep_minutes:
                            arr_minutes += 24 * 60
                        
                        duration_minutes = arr_minutes - dep_minutes
                        hours = duration_minutes // 60
                        minutes = duration_minutes % 60
                        
                        flight_info['flight_duration'] = f"{hours}h{minutes}m"
                    except BaseException:
                        pass
                
                # 设置航空公司
                flight_info['airline'] = self.get_airline_from_code(flight_num)
                
                flights.append(flight_info)
                print(
                    f"✅ 航班 {i + 1}: {flight_info['flight_number']} - {flight_info['departure_time']} -> {flight_info['arrival_time']} - {flight_info['price']}元")
            
        except Exception as e:
            print(f"❌ 备用方法提取失败: {e}")
        
        return flights
    
    def get_airline_from_code(self, flight_number):
        """根据航班号获取航空公司"""
        airline_codes = {
            # 主要航空公司
            'CA': '中国国际航空',
            'MU': '中国东方航空', 
            'CZ': '中国南方航空',
            'HU': '海南航空',
            '3U': '四川航空',
            '9C': '春秋航空',
            'JD': '首都航空',
            'HO': '吉祥航空',
            'ZH': '深圳航空',
            'G5': '华夏航空',
            'KN': '联合航空',
            '8L': '祥鹏航空',
            'TV': '西藏航空',
            'SC': '山东航空',
            'PN': '西部航空',
            'GJ': '长龙航空',
            'Y8': '扬子江航空',
            'QW': '青岛航空',
            'UQ': '乌鲁木齐航空',
            'GT': '桂林航空',
            'DZ': '东海航空',
            'A6': '长龙航空',
            'EU': '成都航空',
            'RY': '瑞丽航空',
            'DR': '瑞丽航空',
            'GX': '北部湾航空',
            'FU': '福州航空',
            'KY': '昆明航空',
            'LT': '龙江航空',
            'OQ': '重庆航空',
            'QW': '青岛航空',
            'UQ': '乌鲁木齐航空',
            'GT': '桂林航空',
            'DZ': '东海航空',
            'A6': '长龙航空',
            'EU': '成都航空',
            'RY': '瑞丽航空',
            'DR': '瑞丽航空',
            'GX': '北部湾航空',
            'FU': '福州航空',
            'KY': '昆明航空',
            'LT': '龙江航空',
            'OQ': '重庆航空'
        }
        
        if len(flight_number) >= 2:
            code = flight_number[:2]
            return airline_codes.get(code, f'{code}航空')
        return '未知航空公司'
    
    def detect_shared_flight(self, flight_number):
        """检测是否为共享航班"""
        # 共享航班通常有特定的标识，这里简化处理
        if '共享' in flight_number or 'SHARE' in flight_number.upper():
            return '是'
        return '否'
    
    def extract_aircraft_type(self, context):
        """提取飞机型号（更严格，避免把航班号片段误识别为机型）"""
        if not context:
            return ''
        patterns = [
            r'(空客\s*\d{3}(?:\([^)]+\))?)',      # 空客321(窄) / 空客321(中)
            r'(波音\s*[A-Za-z0-9]{2,6}(?:\([^)]+\))?)',  # 波音7MA 等
            r'\b(A\d{3})\b',                        # A320/A321
            r'\b(B\d{3})\b',                        # B737/B738
        ]
        for pattern in patterns:
            m = re.search(pattern, context)
            if m:
                return m.group(1).strip()
        return ''

    def extract_aircraft_type_from_page(self, page_source, flight_number=None):
        """从整页源码中提取机型，优先在航班号附近窗口中搜索。"""
        try:
            text = page_source or ''
            window = text
            if flight_number and flight_number in text:
                idx = text.find(flight_number)
                start = max(0, idx - 300)
                end = min(len(text), idx + 400)
                window = text[start:end]
            # 先在窗口内找
            t = self.extract_aircraft_type(window)
            if t:
                return t
            # 全局兜底
            return self.extract_aircraft_type(text)
        except Exception:
            return ''
    
    def _load_airport_config(self):
        """加载机场配置文件"""
        cfg_path = os.path.join(
            os.path.dirname(__file__),
            'config',
            'airports.json')
        try:
            with open(cfg_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._airport_names = data.get('airportNames', {})
                self._airport_cities = data.get('airportCities', {})
        except Exception:
            self._airport_names = {}
            self._airport_cities = {}

    def get_city_from_airport(self, airport_code):
        """根据机场代码获取城市名称（配置驱动）"""
        if not hasattr(self, '_airport_cities'):
            self._load_airport_config()
        return self._airport_cities.get(airport_code, '')

    def get_airport_name(self, code):
        """根据机场代码获取中文机场名称（尽量覆盖常见与页面中出现的别名代码）"""
        if not hasattr(self, '_airport_names'):
            self._load_airport_config()
        if not code:
            return ''
        return self._airport_names.get(code, f"{code}机场")

    def extract_terminals_from_page(
            self,
            page_source,
            dep_airport_name,
            arr_airport_name):
        """从整页源码中提取航站楼信息，并尽量与出发/到达机场名称匹配。

        形态示例："上海浦东T2"、"上海虹桥T2"、"北京首都T3"、"T1"、"1号航站楼"
        返回: (dep_terminal, arr_terminal)，若无法识别则为空字符串
        """
        try:
            text = page_source
            # 中文+T数字候选
            cand = re.findall(r'([\u4e00-\u9fa5]{2,10}?(?:机场)?T\d)', text)
            # 去重保持顺序
            seen = set()
            candidates = []
            for c in cand:
                if c not in seen:
                    seen.add(c)
                    candidates.append(c)

            dep_terminal = ''
            arr_terminal = ''

            def norm(name: str) -> str:
                return (name or '').replace('国际', '').replace('机场', '')

            n_dep = norm(dep_airport_name)
            n_arr = norm(arr_airport_name)

            # 优先按机场中文名匹配
            for c in candidates:
                if n_dep and any(k in c for k in (n_dep, n_dep[:2])):
                    dep_terminal = c
                    break
            for c in candidates:
                if n_arr and any(k in c for k in (n_arr, n_arr[:2])):
                    arr_terminal = c
                    break

            # 若仍为空，回退：若有两个以上候选，按顺序分配
            if (not dep_terminal or not arr_terminal) and len(candidates) >= 2:
                if not dep_terminal:
                    dep_terminal = candidates[0]
                if not arr_terminal:
                    arr_terminal = candidates[1]

            # 若仅一个候选，分配给出发端
            if not dep_terminal and not arr_terminal and len(candidates) == 1:
                dep_terminal = candidates[0]

            # 兜底：纯 T\d 形式（不带中文），取前两个
            if (not dep_terminal or not arr_terminal):
                pure = re.findall(r'(?<![A-Z])T(\d)(?![A-Za-z])', text)
                pure = [f'T{x}' for x in pure]
                if len(pure) >= 2:
                    if not dep_terminal:
                        dep_terminal = pure[0]
                    if not arr_terminal:
                        arr_terminal = pure[1]
                elif len(pure) == 1 and not dep_terminal and not arr_terminal:
                    dep_terminal = pure[0]

            return dep_terminal, arr_terminal
        except Exception:
            return '', ''
    
    def detect_stopover(self, context):
        """检测是否经停"""
        stopover_keywords = ['经停', '中转', 'STOP', 'STOPOVER']
        for keyword in stopover_keywords:
            if keyword in context:
                return '是'
        return '否'
    
    def extract_stopover_city(self, context):
        """提取经停城市"""
        # 查找经停相关的城市信息
        stopover_patterns = [
            r'经停[：:]\s*([\u4e00-\u9fa5]+)',
            r'中转[：:]\s*([\u4e00-\u9fa5]+)',
            r'STOP[：:]\s*([\u4e00-\u9fa5]+)',
        ]
        
        for pattern in stopover_patterns:
            match = re.search(pattern, context)
            if match:
                return match.group(1)
        return ''
    
    def extract_stopover_airport(self, context):
        """提取经停机场"""
        # 查找经停机场代码
        airport_pattern = r'经停.*?([A-Z]{3})'
        match = re.search(airport_pattern, context)
        if match:
            return match.group(1)
        return ''
    
    def extract_cabin_class(self, context):
        """提取舱位等级"""
        cabin_patterns = [
            r'(经济舱|商务舱|头等舱|经济|商务|头等)',
            r'(Y|C|F|经济|商务|头等)',
        ]
        
        for pattern in cabin_patterns:
            match = re.search(pattern, context)
            if match:
                return match.group(1)
        return '经济舱'
    
    def extract_discount_rate(self, context):
        """提取折扣率"""
        discount_patterns = [
            r'(\d+折)',
            r'(\d+%)',
            r'折扣[：:]\s*(\d+[折%])',
        ]
        
        for pattern in discount_patterns:
            match = re.search(pattern, context)
            if match:
                return match.group(1)
        return ''
    
    def extract_original_price(self, context):
        """提取原价"""
        original_price_patterns = [
            r'原价[：:]\s*(\d+(?:\.\d+)?)',
            r'原价\s*(\d+(?:\.\d+)?)',
            r'原\s*(\d+(?:\.\d+)?)',
        ]
        
        for pattern in original_price_patterns:
            match = re.search(pattern, context)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass
        return None
    
    def save_flight_data(self, flights):
        """保存航班数据到数据库和本地文件"""
        if not flights:
            print("❌ 没有航班数据可保存")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(
            self.output_dir,
            f"flight_data_{timestamp}.txt")
        
        # 1. 保存到本地文件
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("12306航班信息抓取结果\n")
                f.write("=" * 50 + "\n")
                f.write(
                    f"抓取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"航班数量: {len(flights)}\n\n")
                
                for i, flight in enumerate(flights, 1):
                    f.write(f"航班 {i}:\n")
                    f.write(f"  航空公司: {flight.get('airline', 'N/A')}\n")
                    f.write(f"  航班号: {flight.get('flight_number', 'N/A')}\n")
                    f.write(
                        f"  是否共享航班: {flight.get('is_shared_flight', 'N/A')}\n")
                    f.write(f"  飞机型号: {flight.get('aircraft_type', 'N/A')}\n")
                    f.write(f"  出发日期: {flight.get('departure_date', 'N/A')}\n")
                    f.write(f"  出发城市: {flight.get('departure_city', 'N/A')}\n")
                    f.write(
                        f"  起飞机场: {flight.get('departure_airport', 'N/A')}\n")
                    f.write(f"  起飞时间: {flight.get('departure_time', 'N/A')}\n")
                    f.write(f"  到达城市: {flight.get('arrival_city', 'N/A')}\n")
                    f.write(
                        f"  落地机场: {flight.get('arrival_airport', 'N/A')}\n")
                    f.write(f"  落地时间: {flight.get('arrival_time', 'N/A')}\n")
                    f.write(
                        f"  飞行时长: {flight.get('flight_duration', 'N/A')}\n")
                    f.write(f"  是否经停: {flight.get('has_stopover', 'N/A')}\n")
                    f.write(f"  经停城市: {flight.get('stopover_city', 'N/A')}\n")
                    f.write(
                        f"  经停机场: {flight.get('stopover_airport', 'N/A')}\n")
                    f.write(f"  最低价格: {flight.get('price', 'N/A')}\n")
                    f.write(f"  舱位等级: {flight.get('cabin_class', 'N/A')}\n")
                    f.write(f"  折扣率: {flight.get('discount_rate', 'N/A')}\n")
                    f.write(f"  原价: {flight.get('original_price', 'N/A')}\n")
                    f.write("-" * 30 + "\n")
            
            print(f"💾 航班数据已保存到: {filename}")
            
        except Exception as e:
            print(f"❌ 保存本地文件失败: {e}")
        
        # 2. 保存到数据库
        try:
            # 获取后端API地址
            api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
            api_url = f"{api_base}/api/flights/batch-save"
            
            # 准备数据
            task_id = self.task_id or os.getenv("TASK_ID")
            # 确保task_id是整数类型
            if task_id:
                try:
                    task_id = int(task_id)
                except (ValueError, TypeError):
                    print(f"⚠️ task_id 格式错误: {task_id}，将设置为 None")
                    task_id = None
            payload = {
                "flights": flights,
                "source": "12306",
                "task_id": task_id
            }
            tprint(
                f"📤 保存航班数据（save_to_database），task_id={task_id} (type: {type(task_id).__name__})")
            
            print(f"📤 正在保存 {len(flights)} 条航班数据到数据库...")
            response = requests.post(
                api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 数据库保存成功: {result.get('message', 'OK')}")
            else:
                print(f"❌ 数据库保存失败: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {e}")
        except Exception as e:
            print(f"❌ 保存到数据库失败: {e}")
    
    def extract_flight_info_advanced(self, page_source):
        """高级方法提取航班信息 - 使用更智能的解析逻辑"""
        print("🔄 使用高级方法提取航班信息...")
        
        flights = []
        
        try:
            # 首先尝试从整个页面源码中提取所有航班号
            all_flight_numbers = re.findall(r'([A-Z]{2}\d{3,4})', page_source)
            print(
                f"📊 页面中找到 {len(all_flight_numbers)} 个航班号: {all_flight_numbers}")
            
            if not all_flight_numbers:
                print("❌ 高级方法：未找到任何航班号")
                return flights
            
            # 为每个航班号尝试构建航班信息
            for flight_number in all_flight_numbers:
                print(f"🔄 处理航班号: {flight_number}")
                
                # 在页面中查找包含这个航班号的上下文
                flight_context = self.find_flight_context(
                    page_source, flight_number)
                
                if flight_context:
                    flight_info = self.parse_flight_context(
                        flight_context, flight_number)
                    if flight_info:
                        # 机型补强：若缺失则从整页提取
                        if not flight_info.get('aircraft_type'):
                            flight_info['aircraft_type'] = self.extract_aircraft_type_from_page(
                                page_source, flight_number)
                        flights.append(flight_info)
                        print(
                            f"✅ 高级方法找到航班: {flight_info['flight_number']} - {flight_info['departure_time']} -> {flight_info['arrival_time']} - {flight_info['price']}元")
                else:
                    print(f"⚠️ 未找到航班 {flight_number} 的上下文信息")
            
        except Exception as e:
            print(f"❌ 高级方法提取失败: {e}")
        
        return flights
    
    def find_flight_context(self, page_source, flight_number):
        """查找航班号的上下文信息"""
        try:
            # 在页面中查找包含航班号的段落或区域
            lines = page_source.split('\n')
            
            for i, line in enumerate(lines):
                if flight_number in line:
                    # 找到包含航班号的行，收集前后几行作为上下文
                    context_lines = []
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    
                    for j in range(start, end):
                        if j < len(lines):
                            context_lines.append(lines[j].strip())
                    
                    context = '\n'.join(context_lines)
                    print(f"📄 航班 {flight_number} 的上下文:\n{context[:200]}...")
                    return context
            
            return None
        except Exception as e:
            print(f"❌ 查找航班上下文失败: {e}")
            return None
    
    def parse_flight_context(self, context, flight_number):
        """解析航班上下文信息"""
        try:
            # 从上下文中提取时间
            times = re.findall(r'(\d{1,2}:\d{2})', context)
            if len(times) < 2:
                print(f"⚠️ 航班 {flight_number} 上下文中的时间不足: {times}")
                return None
            
            # 从上下文中提取价格
            price_match = re.search(
                r'(?:[¥￥]|CNY)\s*([0-9]+(?:\.[0-9]{1,2})?)|([0-9]+(?:\.[0-9]{1,2})?)\s*元',
                context)
            price = price_match.group(1) or price_match.group(
                2) if price_match else ''
            
            if not price:
                print(f"⚠️ 航班 {flight_number} 上下文中未找到价格")
                return None
            
            # 从上下文中提取机场代码
            airports = re.findall(r'([A-Z]{3})', context)
            if len(airports) < 2:
                print(f"⚠️ 航班 {flight_number} 上下文中的机场代码不足: {airports}")
                return None
            
            # 优先使用环境变量中的出发日期，如果环境变量为空则从上下文提取
            if self.depart_date:
                departure_date = self.depart_date
            else:
                date_match = re.search(
                    r'(\d{1,2}月\d{1,2}日|\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}/\d{1,2}|\d{4}-\d{1,2}-\d{1,2})',
                    context)
            departure_date = date_match.group(1) if date_match else ''
            
            flight_info = {
                'airline': self.get_airline_from_code(flight_number),
                'flight_number': flight_number,
                'departure_date': departure_date,
                'departure_time': times[0],
                'departure_airport': airports[0],
                # 优先使用环境变量中的出发城市，如果环境变量为空则从机场代码提取
                'departure_city': self.from_city if self.from_city else (self.get_city_from_airport(airports[0]) if airports[0] else ''),
                'arrival_time': times[1],
                'arrival_airport': airports[1],
                # 优先使用环境变量中的到达城市，如果环境变量为空则从机场代码提取
                'arrival_city': self.to_city if self.to_city else (self.get_city_from_airport(airports[1]) if airports[1] else ''),
                'flight_duration': '',
                'price': price,
                'currency': 'CNY',
                'source': '12306',
                'status': 'active'
            }
            
            # 计算飞行时长
            if flight_info['departure_time'] and flight_info['arrival_time']:
                try:
                    dep_hour, dep_min = map(
                        int, flight_info['departure_time'].split(':'))
                    arr_hour, arr_min = map(
                        int, flight_info['arrival_time'].split(':'))
                    
                    dep_minutes = dep_hour * 60 + dep_min
                    arr_minutes = arr_hour * 60 + arr_min
                    
                    # 处理跨天情况
                    if arr_minutes < dep_minutes:
                        arr_minutes += 24 * 60
                    
                    duration_minutes = arr_minutes - dep_minutes
                    hours = duration_minutes // 60
                    minutes = duration_minutes % 60
                    
                    flight_info['flight_duration'] = f"{hours}h{minutes}m"
                except BaseException:
                    pass
            
            return flight_info
            
        except Exception as e:
            print(f"❌ 解析航班上下文失败: {e}")
            return None
    
    def run_scraping(self, task_id=None):
        """运行完整的抓取流程"""
        tprint("🚀 开始12306航班信息抓取")
        tprint("=" * 50)
        
        # 设置任务ID
        if task_id:
            self.set_task_id(task_id)
        
        try:
            # 步骤1: 检查并安装12306应用（在连接设备之前，因为需要adb命令）
            try:
                from utils import check_and_install_12306_app
                if not check_and_install_12306_app():
                    tprint("❌ 12306应用检查/安装失败，无法继续")
                    return False
            except Exception as e:
                tprint(f"⚠️ 检查/安装12306应用时出错: {e}")
                tprint("⚠️ 继续执行，假设应用已安装...")
            
            # 初始化驱动（使用拆分后的连接模块）
            print("🔌 使用模块化设备连接...")
            self.driver = connect_device()
            self.wait = WebDriverWait(self.driver, 10)
            
            # 导航并查询（模块化）
            tprint(
                f"🔍 准备导航: 出发城市={self.from_city}, 到达城市={self.to_city}, 出发日期={self.depart_date}")
            navigate_and_search(
                self.driver,
                self.from_city,
                self.to_city,
                self.depart_date)

            # 提取页面源码（优先使用OCR模式，适用于H5/WebView页面）
            try:
                from page_capture_ocr import smart_scroll_and_capture_hybrid
                from parser_ocr import parse_ocr_text
                print("🔍 使用混合模式提取航班信息（优先OCR）...")
                flights, ocr_text, method_used = smart_scroll_and_capture_hybrid(
                    self.driver, self.output_dir, prefer_ocr=True)
                print(f"✅ 使用{method_used.upper()}模式识别到 {len(flights)} 个航班")

                if method_used == 'ocr' and ocr_text:
                    # OCR模式：优先尝试大模型视觉API，失败时使用OCR补充并标记字段来源
                    try:
                        llm_flights = []
                        ocr_flights = []
                        
                        # 步骤1: 优先尝试大模型视觉API（默认使用Z.ai GLM-4.6V-Flash）
                        config = _load_scraper_config()
                        llm_api_type = (
                            os.getenv('LLM_API_TYPE')
                            or config.get('llmApiType')
                            or 'zai'
                        ).lower()
                        llm_api_key = None
                        llm_success = False

                        if llm_api_type in ['openai', 'anthropic', 'google', 'zai', 'glm']:
                            if llm_api_type == 'openai':
                                llm_api_key = (
                                    os.getenv('OPENAI_API_KEY')
                                    or config.get('openaiApiKey')
                                    or config.get('llmApiKey')
                                )
                            elif llm_api_type == 'anthropic':
                                llm_api_key = (
                                    os.getenv('ANTHROPIC_API_KEY')
                                    or config.get('anthropicApiKey')
                                    or config.get('llmApiKey')
                                )
                            elif llm_api_type == 'google':
                                llm_api_key = (
                                    os.getenv('GOOGLE_API_KEY')
                                    or config.get('googleApiKey')
                                    or config.get('llmApiKey')
                                )
                            elif llm_api_type in ['zai', 'glm']:
                                llm_api_key = (
                                    os.getenv('ZAI_API_KEY')
                                    or config.get('zaiApiKey')
                                    or config.get('llmApiKey')
                                )
                            
                            if llm_api_key:
                                print(f"🤖 优先使用{llm_api_type.upper()}大模型视觉API解析...")
                                try:
                                    from parser_llm_vision import parse_screenshot_with_llm
                                    llm_flights = parse_screenshot_with_llm(
                                        self.driver, api_type=llm_api_type, api_key=llm_api_key)
                                    if llm_flights:
                                        print(f"✅ 大模型视觉API解析成功，提取到 {len(llm_flights)} 条航班信息")
                                        llm_success = True
                                        # 大模型成功时，直接使用大模型结果，不再调用OCR
                                        parsed_flights = llm_flights
                                        print(f"✅ 使用大模型识别结果：{len(llm_flights)} 个航班")
                                    else:
                                        print(f"⚠️ 大模型视觉API未提取到航班信息，将使用OCR补充")
                                        llm_success = False
                                except Exception as e:
                                    print(f"⚠️ 大模型视觉API解析异常: {e}，将使用OCR补充")
                                    import traceback
                                    traceback.print_exc()
                                    llm_success = False
                            else:
                                print(f"⚠️ 未配置{llm_api_type.upper()} API密钥，将使用OCR识别")
                                llm_success = False
                        else:
                            print(f"⚠️ 未配置LLM_API_TYPE或类型不支持，将使用OCR识别")
                            llm_success = False
                        
                        # 步骤2: 如果大模型未成功，使用OCR解析器
                        if not llm_success:
                            print("🔍 使用OCR解析器提取航班信息...")
                            try:
                                # 获取页面源码作为备用（用于提取额外信息）
                                try:
                                    page_source_fallback = self.driver.page_source
                                except BaseException:
                                    page_source_fallback = None

                                # 使用OCR解析器解析
                                ocr_flights = parse_ocr_text(ocr_text, page_source_fallback)
                                if ocr_flights:
                                    print(f"✅ OCR解析器提取到 {len(ocr_flights)} 条航班信息")
                                    # OCR结果标记所有字段来源为OCR
                                    from merge_llm_ocr_results import merge_llm_ocr_results
                                    parsed_flights = merge_llm_ocr_results([], ocr_flights)
                                    print(f"✅ 使用OCR识别：{len(ocr_flights)} 个航班（已标记字段来源）")
                                else:
                                    parsed_flights = []
                            except Exception as e:
                                print(f"⚠️ OCR解析失败: {e}")
                                parsed_flights = []
                        else:
                            # 大模型已成功，无需OCR
                            ocr_flights = []

                        if parsed_flights:
                            print(f"✅ OCR解析器提取到 {len(parsed_flights)} 条完整航班信息")
                            # 直接保存解析后的航班数据
                            try:
                                # 将解析后的航班数据转换为页面源码格式以便保存
                                import json
                                flights_json = json.dumps(
                                    parsed_flights, ensure_ascii=False)
                                # 创建一个包含完整信息的页面源码
                                page_source = f"<root><flights_json>{flights_json}</flights_json></root>"

                                # 直接调用API保存（绕过parser的解析步骤）
                                api_base = os.getenv(
                                    "API_BASE_URL", "http://localhost:8000")
                                task_id = self.task_id or os.getenv("TASK_ID")
                                # 确保task_id是整数类型
                                if task_id:
                                    try:
                                        task_id = int(task_id)
                                    except (ValueError, TypeError):
                                        print(
                                            f"⚠️ task_id 格式错误: {task_id}，将设置为 None")
                                        task_id = None
                                api_url = f"{api_base}/api/flights/batch-save"
                                payload = {
                                    "flights": parsed_flights,
                                    "source": "12306",
                                    "task_id": task_id
                                }
                                tprint(
                                    f"📤 保存航班数据，task_id={task_id} (type: {type(task_id).__name__})")

                                print(
                                    f"📤 正在保存 {len(parsed_flights)} 条航班数据到数据库...")
                                print(
                                    f"🔍 API请求详情: url={api_url}, task_id={task_id}, flights_count={len(parsed_flights)}")
                                import requests
                                response = requests.post(
                                    api_url, json=payload, timeout=30)

                                if response.status_code == 200:
                                    result = response.json()
                                    print(
                                        f"✅ 数据库保存成功: {result.get('message', 'OK')}")
                                    # 检查返回结果中是否有航班数量更新信息
                                    if 'saved_count' in result:
                                        print(
                                            f"📊 API返回: 保存了 {result.get('saved_count')} 条航班")
                                else:
                                    print(
                                        f"❌ 数据库保存失败: {response.status_code} - {response.text}")
                                    # 回退到parser保存
                                    task_id_for_parser = self.task_id or os.getenv("TASK_ID")
                                    if task_id_for_parser:
                                        try:
                                            task_id_for_parser = int(task_id_for_parser)
                                        except (ValueError, TypeError):
                                            task_id_for_parser = None
                                    parse_and_save(page_source, task_id_for_parser)
                            except Exception as e:
                                print(f"⚠️ 直接保存失败: {e}，使用parser保存")
                                try:
                                    task_id_for_parser = self.task_id or os.getenv("TASK_ID")
                                    if task_id_for_parser:
                                        try:
                                            task_id_for_parser = int(task_id_for_parser)
                                        except (ValueError, TypeError):
                                            task_id_for_parser = None
                                    parse_and_save(page_source, task_id_for_parser)
                                except NameError:
                                    # 如果 parse_and_save 未导入，尝试导入
                                    try:
                                        from parser import parse_and_save
                                        task_id_for_parser = self.task_id or os.getenv("TASK_ID")
                                        if task_id_for_parser:
                                            try:
                                                task_id_for_parser = int(task_id_for_parser)
                                            except (ValueError, TypeError):
                                                task_id_for_parser = None
                                        parse_and_save(page_source, task_id_for_parser)
                                    except Exception as parse_error:
                                        print(f"❌ parser保存也失败: {parse_error}")
                        else:
                            print("⚠️ OCR解析器未提取到完整信息，创建基本航班记录...")
                            # 备用方案：创建基本航班记录
                            if flights:
                                basic_flights = []
                                for flight_num in sorted(flights):
                                    basic_flights.append({
                                        'airline': _get_airline_from_code(flight_num),
                                        'flight_number': flight_num,
                                        'departure_time': '',
                                        'departure_airport': '',
                                        'arrival_time': '',
                                        'arrival_airport': '',
                                        'price': 0.0,
                                        'currency': 'CNY',
                                        'source': '12306',
                                        'status': 'active'
                                    })

                                # 直接保存基本记录
                                api_base = os.getenv(
                                    "API_BASE_URL", "http://localhost:8000")
                                task_id = self.task_id or os.getenv("TASK_ID")
                                # 确保task_id是整数类型
                                if task_id:
                                    try:
                                        task_id = int(task_id)
                                    except (ValueError, TypeError):
                                        print(
                                            f"⚠️ task_id 格式错误: {task_id}，将设置为 None")
                                        task_id = None
                                api_url = f"{api_base}/api/flights/batch-save"
                                payload = {
                                    "flights": basic_flights,
                                    "source": "12306",
                                    "task_id": task_id
                                }
                                tprint(
                                    f"📤 保存基本航班记录，task_id={task_id} (type: {type(task_id).__name__})")

                                import requests
                                response = requests.post(
                                    api_url, json=payload, timeout=30)
                                if response.status_code == 200:
                                    print(
                                        f"✅ 保存了 {len(basic_flights)} 条基本航班记录")
                                else:
                                    print(f"❌ 保存失败: {response.status_code}")
                    except Exception as e:
                        print(f"⚠️ OCR解析失败: {e}，创建基本航班记录...")
                        import traceback
                        traceback.print_exc()
                        # 备用方案：创建基本航班记录
                        if flights:
                            basic_flights = []
                            for flight_num in sorted(flights):
                                basic_flights.append({
                                    'airline': _get_airline_from_code(flight_num),
                                    'flight_number': flight_num,
                                    'departure_time': '',
                                    'departure_airport': '',
                                    'arrival_time': '',
                                    'arrival_airport': '',
                                    'price': 0.0,
                                    'currency': 'CNY',
                                    'source': '12306',
                                    'status': 'active'
                                })

                            # 直接保存基本记录
                            api_base = os.getenv(
                                "API_BASE_URL", "http://localhost:8000")
                            task_id = self.task_id or os.getenv("TASK_ID")
                            # 确保task_id是整数类型
                            if task_id:
                                try:
                                    task_id = int(task_id)
                                except (ValueError, TypeError):
                                    print(
                                        f"⚠️ task_id 格式错误: {task_id}，将设置为 None")
                                    task_id = None
                            api_url = f"{api_base}/api/flights/batch-save"
                            payload = {
                                "flights": basic_flights,
                                "source": "12306",
                                "task_id": task_id
                            }
                            tprint(
                                f"📤 保存基本航班记录（异常处理），task_id={task_id} (type: {type(task_id).__name__})")

                            import requests
                            try:
                                response = requests.post(
                                    api_url, json=payload, timeout=30)
                                if response.status_code == 200:
                                    print(
                                        f"✅ 保存了 {len(basic_flights)} 条基本航班记录")
                                else:
                                    print(
                                        f"❌ 保存失败: {response.status_code} - {response.text}")
                            except Exception as save_e:
                                print(f"❌ 保存请求失败: {save_e}")
                elif method_used == 'ocr':
                    # OCR模式但没有OCR文本，使用航班号创建基本记录
                    print("⚠️ OCR模式但无OCR文本，创建基本航班记录...")
                    if flights:
                        # 创建基本航班记录（只有航班号）
                        basic_flights = []
                        for flight_num in sorted(flights):
                            basic_flights.append({
                                'airline': _get_airline_from_code(flight_num),
                                'flight_number': flight_num,
                                'departure_time': '',
                                'departure_airport': '',
                                'arrival_time': '',
                                'arrival_airport': '',
                                'price': 0.0,
                                'currency': 'CNY',
                                'source': '12306',
                                'status': 'active'
                            })

                        # 直接保存
                        api_base = os.getenv(
                            "API_BASE_URL", "http://localhost:8000")
                        task_id = self.task_id or os.getenv("TASK_ID")
                        # 确保task_id是整数类型
                        if task_id:
                            try:
                                task_id = int(task_id)
                            except (ValueError, TypeError):
                                print(f"⚠️ task_id 格式错误: {task_id}，将设置为 None")
                                task_id = None
                        api_url = f"{api_base}/api/flights/batch-save"
                        payload = {
                            "flights": basic_flights,
                            "source": "12306",
                            "task_id": task_id
                        }
                        tprint(
                            f"📤 保存基本航班记录（OCR无文本），task_id={task_id} (type: {type(task_id).__name__})")

                        import requests
                        response = requests.post(
                            api_url, json=payload, timeout=30)
                        if response.status_code == 200:
                            print(f"✅ 保存了 {len(basic_flights)} 条基本航班记录")
                        else:
                            print(f"❌ 保存失败: {response.status_code}")
                else:
                    # XML模式：使用原有流程
                    from page_capture import smart_scroll_and_capture
                    page_source, _ = smart_scroll_and_capture(
                        self.driver, self.output_dir)
                    if not page_source:
                        tprint("❌ 页面源码提取失败")
                        return False
                    try:
                        task_id_for_parser = self.task_id or os.getenv("TASK_ID")
                        if task_id_for_parser:
                            try:
                                task_id_for_parser = int(task_id_for_parser)
                            except (ValueError, TypeError):
                                task_id_for_parser = None
                        parse_and_save(page_source, task_id_for_parser)
                    except NameError:
                        # 如果 parse_and_save 未导入，尝试导入
                        try:
                            from parser import parse_and_save
                            task_id_for_parser = self.task_id or os.getenv("TASK_ID")
                            if task_id_for_parser:
                                try:
                                    task_id_for_parser = int(task_id_for_parser)
                                except (ValueError, TypeError):
                                    task_id_for_parser = None
                            parse_and_save(page_source, task_id_for_parser)
                        except Exception as parse_error:
                            tprint(f"❌ parser保存失败: {parse_error}")
            except ImportError as e:
                # 如果OCR模块不可用，回退到原有方法
                tprint(f"⚠️ OCR模块不可用: {e}，使用传统XML提取...")
                from page_capture import smart_scroll_and_capture
                page_source, _ = smart_scroll_and_capture(
                    self.driver, self.output_dir)
                if not page_source:
                    tprint("❌ 页面源码提取失败")
                    return False
                try:
                    task_id_for_parser = self.task_id or os.getenv("TASK_ID")
                    if task_id_for_parser:
                        try:
                            task_id_for_parser = int(task_id_for_parser)
                        except (ValueError, TypeError):
                            task_id_for_parser = None
                    parse_and_save(page_source, task_id_for_parser)
                except NameError:
                    # 如果 parse_and_save 未导入，尝试导入
                    try:
                        from parser import parse_and_save
                        task_id_for_parser = self.task_id or os.getenv("TASK_ID")
                        if task_id_for_parser:
                            try:
                                task_id_for_parser = int(task_id_for_parser)
                            except (ValueError, TypeError):
                                task_id_for_parser = None
                        parse_and_save(page_source, task_id_for_parser)
                    except Exception as parse_error:
                        tprint(f"❌ parser保存失败: {parse_error}")
            except Exception as e:
                tprint(f"⚠️ 提取过程出错: {e}，尝试使用XML提取...")
                from page_capture import smart_scroll_and_capture
                page_source, _ = smart_scroll_and_capture(
                    self.driver, self.output_dir)
                if page_source:
                    try:
                        task_id_for_parser = self.task_id or os.getenv("TASK_ID")
                        if task_id_for_parser:
                            try:
                                task_id_for_parser = int(task_id_for_parser)
                            except (ValueError, TypeError):
                                task_id_for_parser = None
                        parse_and_save(page_source, task_id_for_parser)
                    except NameError:
                        # 如果 parse_and_save 未导入，尝试导入
                        try:
                            from parser import parse_and_save
                            task_id_for_parser = self.task_id or os.getenv("TASK_ID")
                            if task_id_for_parser:
                                try:
                                    task_id_for_parser = int(task_id_for_parser)
                                except (ValueError, TypeError):
                                    task_id_for_parser = None
                            parse_and_save(page_source, task_id_for_parser)
                        except Exception as parse_error:
                            tprint(f"❌ parser保存失败: {parse_error}")
            
            print("\n🎉 航班信息抓取完成！")
            return True
            
        except Exception as e:
            print(f"❌ 抓取过程出错: {e}")
            return False
        
        finally:
            # 无论成功还是异常，尽力在结束前再留一张最终截图
            try:
                if self.driver:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    final_shot = os.path.join(
                        self.output_dir, f"flight_scraper_final_{timestamp}.png")
                    self.driver.save_screenshot(final_shot)
                    print(f"📸 最终截图已保存: {final_shot}")
            except Exception as e:
                print(f"⚠️ 最终截图失败: {e}")

            if self.driver:
                self.driver.quit()
                print("🔚 驱动已关闭")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="12306 航班抓取/解析工具")
    parser.add_argument(
        "--parse-only",
        action="store_true",
        help="仅解析给定页面源码文件，不运行Appium")
    parser.add_argument("--input", type=str, help="页面源码文件路径（.xml/.txt）")
    parser.add_argument(
        "--output",
        type=str,
        help="输出JSON文件路径（可选，不填则写入results目录）")
    args = parser.parse_args()

    # 仅解析模式：直接读取文件并调用统一解析方法
    if args.parse_only:
        if not args.input or not os.path.exists(args.input):
            print("❌ 需要提供有效的 --input 文件路径用于解析")
            sys.exit(2)
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                page_source = f.read()
            flights = parse_page_source(page_source)
            print("\n🧾 解析结果(JSON):")
            print(json.dumps(
                {"count": len(flights), "flights": flights}, ensure_ascii=False, indent=2))
            # 写入文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_dir = os.getenv(
                "SCRAPER_OUTPUT_DIR", os.path.join(
                    os.getcwd(), "results"))
            try:
                os.makedirs(default_dir, exist_ok=True)
            except Exception:
                pass
            out_path = args.output or os.path.join(
                default_dir, f"parsed_flights_{timestamp}.json")
            with open(out_path, "w", encoding="utf-8") as wf:
                json.dump({"count": len(flights), "flights": flights},
                          wf, ensure_ascii=False, indent=2)
            latest_path = os.path.join(
                default_dir, "parsed_flights_latest.json")
            try:
                with open(latest_path, "w", encoding="utf-8") as lf:
                    json.dump({"count": len(flights), "flights": flights},
                              lf, ensure_ascii=False, indent=2)
            except Exception:
                pass
            print(f"\n💾 已写入: {out_path}\n💾 最新文件: {latest_path}")
            sys.exit(0)
        except Exception as e:
            print(f"❌ 解析失败: {e}")
            sys.exit(3)

    # 正常抓取模式
    scraper = FlightScraper12306()
    
    # 从环境变量获取任务ID
    task_id = os.getenv("TASK_ID")
    if task_id:
        try:
            task_id = int(task_id)
        except ValueError:
            task_id = None
    
    success = scraper.run_scraping(task_id)
    
    if success:
        print("\n✅ 抓取任务完成！")
        sys.exit(0)
    else:
        print("\n❌ 抓取任务失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()
