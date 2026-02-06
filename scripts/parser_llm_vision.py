#!/usr/bin/env python3
"""
基于大模型视觉API的航班信息解析器
使用大模型（如GPT-4V、Claude等）分析截图，准确识别航班卡片信息
"""
import os
import json
import base64
import re
from typing import List, Dict, Any, Optional
from io import BytesIO

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def _load_scraper_config() -> dict:
    """读取统一配置文件，与 verify_zai_api.py 默认路径一致。"""
    cfg_path = os.getenv("SCRAPER_CONFIG_PATH")
    if not cfg_path:
        _script_dir = os.path.dirname(os.path.abspath(__file__))
        cfg_path = os.path.join(_script_dir, "config", "scraper.config.json")
    if not os.path.isfile(cfg_path):
        return {}
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg if isinstance(cfg, dict) else {}
    except Exception:
        return {}


def encode_image_to_base64(image_bytes: bytes) -> str:
    """将图片编码为base64字符串"""
    return base64.b64encode(image_bytes).decode('utf-8')


def parse_flights_with_llm_vision(image_bytes: bytes, api_type: str = 'openai', api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    使用大模型视觉API解析航班信息
    
    Args:
        image_bytes: 截图字节数据
        api_type: API类型 ('openai', 'anthropic', 'google')
        api_key: API密钥（如果为None，从环境变量读取）
    
    Returns:
        list: 航班信息列表
    """
    if not PIL_AVAILABLE:
        print("⚠️ PIL未安装，无法处理图片")
        return []
    
    flights = []
    
    try:
        # 编码图片
        base64_image = encode_image_to_base64(image_bytes)
        
        # 根据API类型选择不同的实现
        if api_type == 'openai':
            flights = _parse_with_openai(base64_image, api_key)
        elif api_type == 'anthropic':
            flights = _parse_with_anthropic(base64_image, api_key)
        elif api_type == 'google':
            flights = _parse_with_google(base64_image, api_key)
        elif api_type == 'zai' or api_type == 'glm':
            flights = _parse_with_zai(base64_image, api_key)
        else:
            print(f"⚠️ 不支持的API类型: {api_type}")
            return []
        
        return flights
        
    except Exception as e:
        print(f"❌ 大模型视觉API解析失败: {e}")
        import traceback
        traceback.print_exc()
        return []


def _parse_with_openai(base64_image: str, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """使用OpenAI GPT-4V API解析"""
    try:
        import openai
        
        if not api_key:
            api_key = os.getenv('OPENAI_API_KEY')

        if not api_key:
            config = _load_scraper_config()
            api_key = config.get('openaiApiKey') or config.get('llmApiKey')

        if not api_key:
            print("⚠️ 未设置OPENAI_API_KEY环境变量")
            return []
        
        client = openai.OpenAI(api_key=api_key)
        
        prompt = """请分析这张航班搜索结果截图，提取每个航班卡片的信息。

要求：
1. 识别每个独立的航班卡片（通常有白色背景，用灰色分隔）
2. 为每个航班卡片提取以下信息：
   - 航班号（如：MU6648, CZ3911等，只提取纯航班号，不要包含航空公司名称）
   - 出发时间（如：20:30）
   - 到达时间（如：23:15）
   - 出发机场（如：成都双流T2）
   - 到达机场（如：北京大兴）
   - 价格（如：¥450起，只提取数字）
   - 折扣信息（如：经济舱2.0折）
   - 舱位等级（经济舱/商务舱/头等舱）
   - 机型（如果有）
   - 是否经停（是/否，如果航班有经停信息则填"是"，否则填"否"）
   - 经停城市（如果有经停，填写经停城市名称，否则为空字符串）
   - 是否共享航班（是/否，如果显示"共享"、"代码共享"等字样则填"是"，否则填"否"）

3. 确保每个航班的信息都来自同一个卡片，不要跨卡片匹配

请以JSON格式返回结果，格式如下：
[
  {
    "flight_number": "MU6648",
    "departure_time": "20:30",
    "arrival_time": "23:15",
    "departure_airport": "成都双流T2",
    "arrival_airport": "北京大兴",
    "price": 450,
    "discount_rate": "2.0折",
    "cabin_class": "经济舱",
    "aircraft_type": "空客321(窄)",
    "has_stopover": "否",
    "stopover_city": "",
    "is_shared_flight": "否"
  },
  ...
]

只返回JSON数组，不要其他文字说明。"""
        
        response = client.chat.completions.create(
            model="gpt-4o",  # 或 "gpt-4-vision-preview"
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000
        )
        
        # 解析响应
        content = response.choices[0].message.content
        print(f"📝 大模型响应: {content[:200]}...")
        
        # 提取JSON
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            flights_data = json.loads(json_match.group(0))
            return _normalize_flight_data(flights_data)
        else:
            print("⚠️ 无法从响应中提取JSON")
            return []
            
    except ImportError:
        print("⚠️ openai库未安装，请运行: pip install openai")
        return []
    except Exception as e:
        print(f"❌ OpenAI API调用失败: {e}")
        return []


def _parse_with_anthropic(base64_image: str, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """使用Anthropic Claude API解析"""
    try:
        import anthropic
        
        if not api_key:
            api_key = os.getenv('ANTHROPIC_API_KEY')

        if not api_key:
            config = _load_scraper_config()
            api_key = config.get('anthropicApiKey') or config.get('llmApiKey')

        if not api_key:
            print("⚠️ 未设置ANTHROPIC_API_KEY环境变量")
            return []
        
        client = anthropic.Anthropic(api_key=api_key)
        
        print(f"🤖 调用Anthropic Claude API...")
        
        prompt = """请分析这张航班搜索结果截图，提取每个航班卡片的信息。

要求：
1. 识别每个独立的航班卡片（通常有白色背景，用灰色分隔）
2. 为每个航班卡片提取以下信息：
   - 航班号（如：MU6648, CZ3911等，只提取纯航班号，不要包含航空公司名称）
   - 出发时间（如：20:30）
   - 到达时间（如：23:15）
   - 出发机场（如：成都双流T2）
   - 到达机场（如：北京大兴）
   - 价格（如：¥450起，只提取数字）
   - 折扣信息（如：经济舱2.0折）
   - 舱位等级（经济舱/商务舱/头等舱）
   - 机型（如果有）
   - 是否经停（是/否，如果航班有经停信息则填"是"，否则填"否"）
   - 经停城市（如果有经停，填写经停城市名称，否则为空字符串）
   - 是否共享航班（是/否，如果显示"共享"、"代码共享"等字样则填"是"，否则填"否"）

3. 确保每个航班的信息都来自同一个卡片，不要跨卡片匹配

请以JSON格式返回结果，格式如下：
[
  {
    "flight_number": "MU6648",
    "departure_time": "20:30",
    "arrival_time": "23:15",
    "departure_airport": "成都双流T2",
    "arrival_airport": "北京大兴",
    "price": 450,
    "discount_rate": "2.0折",
    "cabin_class": "经济舱",
    "aircraft_type": "空客321(窄)",
    "has_stopover": "否",
    "stopover_city": "",
    "is_shared_flight": "否"
  },
  ...
]

只返回JSON数组，不要其他文字说明。"""
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # 或 "claude-3-opus-20240229"
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        
        content = message.content[0].text
        print(f"📝 大模型响应: {content[:200]}...")
        
        # 提取JSON
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            flights_data = json.loads(json_match.group(0))
            return _normalize_flight_data(flights_data)
        else:
            print("⚠️ 无法从响应中提取JSON")
            return []
            
    except ImportError:
        print("⚠️ anthropic库未安装，请运行: pip install anthropic")
        return []
    except Exception as e:
        print(f"❌ Anthropic API调用失败: {e}")
        return []


def _parse_with_google(base64_image: str, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """使用Google Gemini API解析"""
    try:
        import google.generativeai as genai
        
        if not api_key:
            api_key = os.getenv('GOOGLE_API_KEY')

        if not api_key:
            config = _load_scraper_config()
            api_key = config.get('googleApiKey') or config.get('llmApiKey')

        if not api_key:
            print("⚠️ 未设置GOOGLE_API_KEY环境变量")
            return []
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro-vision')
        
        print(f"🤖 调用Google Gemini API...")
        
        prompt = """请分析这张航班搜索结果截图，提取每个航班卡片的信息。

要求：
1. 识别每个独立的航班卡片（通常有白色背景，用灰色分隔）
2. 为每个航班卡片提取以下信息：
   - 航班号（如：MU6648, CZ3911等，只提取纯航班号，不要包含航空公司名称）
   - 出发时间（如：20:30）
   - 到达时间（如：23:15）
   - 出发机场（如：成都双流T2）
   - 到达机场（如：北京大兴）
   - 价格（如：¥450起，只提取数字）
   - 折扣信息（如：经济舱2.0折）
   - 舱位等级（经济舱/商务舱/头等舱）
   - 机型（如果有）
   - 是否经停（是/否，如果航班有经停信息则填"是"，否则填"否"）
   - 经停城市（如果有经停，填写经停城市名称，否则为空字符串）
   - 是否共享航班（是/否，如果显示"共享"、"代码共享"等字样则填"是"，否则填"否"）

3. 确保每个航班的信息都来自同一个卡片，不要跨卡片匹配

请以JSON格式返回结果，格式如下：
[
  {
    "flight_number": "MU6648",
    "departure_time": "20:30",
    "arrival_time": "23:15",
    "departure_airport": "成都双流T2",
    "arrival_airport": "北京大兴",
    "price": 450,
    "discount_rate": "2.0折",
    "cabin_class": "经济舱",
    "aircraft_type": "空客321(窄)",
    "has_stopover": "否",
    "stopover_city": "",
    "is_shared_flight": "否"
  },
  ...
]

只返回JSON数组，不要其他文字说明。"""
        
        # 将base64转换为PIL Image
        image_data = base64.b64decode(base64_image)
        image = Image.open(BytesIO(image_data))
        
        response = model.generate_content([prompt, image])
        content = response.text
        print(f"📝 大模型响应: {content[:200]}...")
        
        # 提取JSON
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            flights_data = json.loads(json_match.group(0))
            return _normalize_flight_data(flights_data)
        else:
            print("⚠️ 无法从响应中提取JSON")
            return []
            
    except ImportError:
        print("⚠️ google-generativeai库未安装，请运行: pip install google-generativeai")
        return []
    except Exception as e:
        print(f"❌ Google API调用失败: {e}")
        return []


def _parse_with_zai(base64_image: str, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """使用Z.ai GLM API解析"""
    try:
        import requests
        
        if not api_key:
            api_key = os.getenv("ZAI_API_KEY")
        if not api_key:
            config = _load_scraper_config()
            raw = config.get("zaiApiKey") or config.get("llmApiKey")
            api_key = (raw or "").strip()

        if not api_key:
            print("⚠️ 未设置 ZAI_API_KEY 或 scraper.config.json 中的 zaiApiKey/llmApiKey")
            return []

        url = "https://api.z.ai/api/paas/v4/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key,
        }
        print("🤖 调用 Z.ai GLM-4.6V-Flash API...")
        
        prompt = """请分析这张航班搜索结果截图，提取每个航班卡片的信息。

要求：
1. 识别每个独立的航班卡片（通常有白色背景，用灰色分隔）
2. 为每个航班卡片提取以下信息：
   - 航班号（如：MU6648, CZ3911等，只提取纯航班号，不要包含航空公司名称）
   - 出发时间（如：20:30）
   - 到达时间（如：23:15）
   - 出发机场（完整名称，如：昆明长水、深圳宝安T3、成都双流T2）
   - 到达机场（完整名称，如：北京大兴、深圳宝安T3）
   - 飞行时长（如果有显示，格式如：2h5m、2h30m、1h50m；如果没有显示则留空）
   - 价格（如：¥450起，只提取数字）
   - 折扣信息（如：经济舱2.0折）
   - 舱位等级（经济舱/商务舱/头等舱）
   - 机型（如果有）
   - 是否经停（是/否，如果航班有经停信息则填"是"，否则填"否"）
   - 经停城市（如果有经停，填写经停城市名称，否则为空字符串）
   - 是否共享航班（是/否，如果显示"共享"、"代码共享"等字样则填"是"，否则填"否"）

3. 确保每个航班的信息都来自同一个卡片，不要跨卡片匹配
4. 机场名称要完整提取，包括航站楼信息（如T1、T2、T3）

请以JSON格式返回结果，格式如下：
[
  {
    "flight_number": "MU6648",
    "departure_time": "20:30",
    "arrival_time": "23:15",
    "departure_airport": "成都双流T2",
    "arrival_airport": "北京大兴",
    "flight_duration": "2h5m",
    "price": 450,
    "discount_rate": "2.0折",
    "cabin_class": "经济舱",
    "aircraft_type": "空客321(窄)",
    "has_stopover": "否",
    "stopover_city": "",
    "is_shared_flight": "否"
  },
  ...
]

只返回JSON数组，不要其他文字说明。"""
        
        payload = {
            "model": "glm-4.6v-flash",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                        },
                    ],
                }
            ],
            "max_tokens": 2000,
            "stream": False,
        }
        
        # 429 限流时重试（指数退避），最多 3 次
        for attempt in range(3):
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            if response.status_code != 429:
                break
            if attempt < 2:
                wait = (2 ** attempt) * 5
                retry_after = response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    wait = min(int(retry_after), 60)
                print(f"⚠️ Z.ai 429 限流，{wait}s 后重试 ({attempt + 1}/3)...")
                import time
                time.sleep(wait)
        if response.status_code != 200:
            response.raise_for_status()

        result = response.json()
        content = (result.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
        print(f"📝 大模型响应: {content[:200]}...")
        
        # 提取JSON
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            flights_data = json.loads(json_match.group(0))
            return _normalize_flight_data(flights_data)
        else:
            print("⚠️ 无法从响应中提取JSON")
            return []
            
    except ImportError:
        print("⚠️ requests库未安装，请运行: pip install requests")
        return []
    except Exception as e:
        print(f"❌ Z.ai API调用失败: {e}")
        import traceback
        traceback.print_exc()
        return []


def _normalize_flight_data(flights_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """标准化航班数据格式"""
    import os
    
    from_city = os.getenv('SCRAPER_FROM_CITY', '')
    to_city = os.getenv('SCRAPER_TO_CITY', '')
    depart_date = os.getenv('SCRAPER_DEPART_DATE', '')
    
    normalized = []
    
    for flight in flights_data:
        # 提取并清理航班号（从"南航CZ3911"中提取"CZ3911"）
        flight_number_raw = flight.get('flight_number', '')
        # 使用正则表达式提取航班号（2-3个字母+数字）
        import re
        flight_number_match = re.search(r'([A-Z]{2,3}\d{3,4})', flight_number_raw.upper())
        if flight_number_match:
            flight_number = flight_number_match.group(1)
        else:
            # 如果正则匹配失败，尝试直接使用原始值
            flight_number = flight_number_raw.strip()
        
        # 提取机场信息（保留原始名称，同时提取代码和航站楼）
        dep_airport_raw = flight.get('departure_airport', '').strip()
        arr_airport_raw = flight.get('arrival_airport', '').strip()
        
        # 机场名称到三字码的映射
        airport_map = {
            '双流': 'CTU', '天府': 'TFU', '宝安': 'SZX', '首都': 'PEK',
            '大兴': 'PKX', '虹桥': 'SHA', '浦东': 'PVG', '白云': 'CAN',
            '长水': 'KMG', '新郑': 'CGO', '萧山': 'HGH', '禄口': 'NKG',
            '天河': 'WUH', '黄花': 'CSX', '高崎': 'XMN', '长乐': 'FOC',
            '胶东': 'TAO', '周水子': 'DLC', '地窝堡': 'URC'
        }
        
        # 提取出发机场代码和航站楼
        dep_air = ''
        dep_terminal = ''
        if dep_airport_raw:
            # 尝试提取三字码
            for name, code in airport_map.items():
                if name in dep_airport_raw:
                    dep_air = code
                    break
            # 提取航站楼（T1/T2/T3）
            terminal_match = re.search(r'[Tt](\d+)', dep_airport_raw)
            if terminal_match:
                dep_terminal = f"T{terminal_match.group(1)}"
        
        # 提取到达机场代码和航站楼
        arr_air = ''
        arr_terminal = ''
        if arr_airport_raw:
            # 尝试提取三字码
            for name, code in airport_map.items():
                if name in arr_airport_raw:
                    arr_air = code
                    break
            # 提取航站楼（T1/T2/T3）
            terminal_match = re.search(r'[Tt](\d+)', arr_airport_raw)
            if terminal_match:
                arr_terminal = f"T{terminal_match.group(1)}"
        
        # 保留原始机场名称（如果没有三字码，使用原始名称）
        dep_airport = dep_airport_raw if dep_airport_raw else (dep_air if dep_air else '')
        arr_airport = arr_airport_raw if arr_airport_raw else (arr_air if arr_air else '')
        
        # 计算飞行时长（优先使用大模型返回的，如果没有则计算）
        flight_duration = flight.get('flight_duration', '')
        dep_time = flight.get('departure_time', '')
        arr_time = flight.get('arrival_time', '')
        
        # 如果没有飞行时长，从时间计算
        if not flight_duration and dep_time and arr_time:
            try:
                dep_h, dep_m = map(int, dep_time.split(':'))
                arr_h, arr_m = map(int, arr_time.split(':'))
                dep_minutes = dep_h * 60 + dep_m
                arr_minutes = arr_h * 60 + arr_m
                if arr_minutes < dep_minutes:
                    arr_minutes += 24 * 60
                duration_minutes = arr_minutes - dep_minutes
                hours = duration_minutes // 60
                minutes = duration_minutes % 60
                # 格式化：2h5m 或 2小时5分钟
                if hours > 0:
                    flight_duration = f"{hours}h{minutes}m" if minutes > 0 else f"{hours}h"
                else:
                    flight_duration = f"{minutes}m"
            except Exception as e:
                print(f"⚠️ 计算飞行时长失败: {e}")
                flight_duration = ''
        
        # 提取航司代码（使用清理后的航班号）
        try:
            from parser import _get_airline_from_code
            airline = _get_airline_from_code(flight_number)
        except:
            airline = ''
        
        # 提取经停信息
        has_stopover = flight.get('has_stopover', '否')
        stopover_city = flight.get('stopover_city', '')
        stopover_airport = flight.get('stopover_airport', '')
        
        # 提取共享航班信息
        is_shared_flight = flight.get('is_shared_flight', '否')
        
        normalized_flight = {
            'airline': airline,
            'flight_number': flight_number,
            'is_shared_flight': is_shared_flight if is_shared_flight in ['是', '否'] else '否',
            'aircraft_type': flight.get('aircraft_type', ''),
            'departure_date': depart_date,
            'departure_time': dep_time,
            'departure_airport': dep_airport,  # 保留原始机场名称
            'departure_city': from_city,
            'arrival_time': arr_time,
            'arrival_airport': arr_airport,  # 保留原始机场名称
            'arrival_city': to_city,
            'flight_duration': flight_duration,
            'has_stopover': has_stopover if has_stopover in ['是', '否'] else '否',
            'stopover_city': stopover_city or '',
            'stopover_airport': stopover_airport or '',
            'price': float(flight.get('price', 0)),
            'currency': 'CNY',
            'cabin_class': flight.get('cabin_class', '经济舱'),
            'discount_rate': flight.get('discount_rate', ''),
            'original_price': None,
            'source': '12306',
            'status': 'active',
            'departure_airport_code': dep_air,  # 三字码（如果有）
            'arrival_airport_code': arr_air,  # 三字码（如果有）
            'departure_terminal': dep_terminal,  # 航站楼（如果有）
            'arrival_terminal': arr_terminal,  # 航站楼（如果有）
        }
        
        normalized.append(normalized_flight)
    
    return normalized


def parse_screenshot_with_llm(driver, api_type: str = 'openai', api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    从当前页面截图使用大模型解析航班信息
    
    Args:
        driver: WebDriver实例
        api_type: API类型 ('openai', 'anthropic', 'google')
        api_key: API密钥
    
    Returns:
        list: 航班信息列表
    """
    try:
        # 获取截图
        screenshot = driver.get_screenshot_as_png()
        
        # 使用大模型解析
        flights = parse_flights_with_llm_vision(screenshot, api_type, api_key)
        
        print(f"✅ 大模型解析完成，提取到 {len(flights)} 条航班信息")
        
        return flights
        
    except Exception as e:
        print(f"❌ 大模型解析失败: {e}")
        import traceback
        traceback.print_exc()
        return []
