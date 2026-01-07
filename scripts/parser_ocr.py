#!/usr/bin/env python3
"""
OCR结果解析器：从OCR识别的文本中提取完整的航班信息
"""
import re
from datetime import datetime

try:
    from .parser import (
        _get_airport_name,
        _get_city_from_airport,
        _get_airline_from_code,
        _detect_shared_flight,
        _extract_aircraft_type,
        _extract_terminals_from_page
    )
except ImportError:
    from parser import (
        _get_airport_name,
        _get_city_from_airport,
        _get_airline_from_code,
        _detect_shared_flight,
        _extract_aircraft_type,
        _extract_terminals_from_page
    )


def parse_ocr_text(ocr_text, page_source_fallback=None):
    """
    从OCR识别的文本中解析航班信息

    Args:
        ocr_text: OCR识别的文本
        page_source_fallback: 备用页面源码（用于提取额外信息）

    Returns:
        list: 航班信息列表
    """
    import os

    flights = []

    if not ocr_text:
        return flights

    # 从环境变量获取任务配置信息
    from_city = os.getenv('SCRAPER_FROM_CITY', '')
    to_city = os.getenv('SCRAPER_TO_CITY', '')
    depart_date = os.getenv('SCRAPER_DEPART_DATE', '')

    try:
        # 提取航班号
        flight_numbers = re.findall(r'[A-Z]{2,4}\d{3,5}', ocr_text)
        # 验证航班号格式
        valid_flight_numbers = [
            f for f in flight_numbers if len(f) >= 5 and re.match(
                r'^[A-Z]{2,4}\d{3,5}$', f)]

        # 提取时间（格式：HH:MM）
        times = re.findall(r'(\d{1,2}:\d{2})', ocr_text)

        # 提取价格（支持"¥XXX起"格式）
        prices = []
        price_positions = []  # 保存价格位置，用于匹配
        for m in re.finditer(
            r'(?:[¥￥]|CNY)\s*([0-9]+(?:\.[0-9]{1,2})?)(?:起|元)?|([0-9]+(?:\.[0-9]{1,2})?)\s*(?:起|元)',
                ocr_text):
            price_str = m.group(1) or m.group(2)
            if price_str:
                prices.append(price_str)
                price_positions.append(m.start())  # 保存价格在文本中的位置

        # 提取机场代码（3个大写字母）
        airports = re.findall(r'\b([A-Z]{3})\b', ocr_text)

        # 提取日期
        dates = re.findall(
            r'(\d{1,2}月\d{1,2}日|\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}/\d{1,2}|\d{4}-\d{1,2}-\d{1,2})',
            ocr_text)

        # 组合航班信息
        # 由于OCR识别的文本可能不完整，我们尽量匹配
        time_pairs = [(times[i], times[i + 1]) if i + 1 < len(times)
                      else (times[i], '') for i in range(0, len(times), 2)]

        # 去重：只保留唯一的航班号
        unique_flight_numbers = []
        seen_flight_numbers = set()
        for flight_num in valid_flight_numbers:
            if flight_num not in seen_flight_numbers:
                unique_flight_numbers.append(flight_num)
                seen_flight_numbers.add(flight_num)
        
        print(f"📊 去重前: {len(valid_flight_numbers)} 个航班号, 去重后: {len(unique_flight_numbers)} 个唯一航班号")
        
        # 智能匹配：基于位置匹配航班号、时间、价格、折扣
        # 为每个航班号找到最接近的时间和价格，避免跨卡片匹配
        def find_nearest_info(flight_num, text, all_times, all_prices, all_flight_numbers, current_index):
            """找到与航班号最接近的时间、价格和折扣信息，避免跨卡片匹配"""
            flight_pos = text.find(flight_num)
            if flight_pos == -1:
                return '', '', 0.0, '', ''
            
            # 确定当前航班卡片的边界
            # 查找下一个航班号的位置作为边界
            card_end = len(text)  # 默认边界为文本末尾
            if current_index + 1 < len(all_flight_numbers):
                next_flight = all_flight_numbers[current_index + 1]
                next_flight_pos = text.find(next_flight, flight_pos + len(flight_num))
                if next_flight_pos != -1:
                    card_end = next_flight_pos  # 下一个航班号之前
            
            # 在航班号附近（前后300字符）查找时间和价格
            search_start = max(0, flight_pos - 300)
            search_end = min(card_end, flight_pos + 600)  # 限制在当前卡片内
            search_text = text[search_start:search_end]
            
            # 查找时间对（在航班号前后查找，但限制在卡片内）
            dep_time = ''
            arr_time = ''
            
            # 确定卡片开始位置（上一个航班号之后，或文本开始）
            card_start = 0
            if current_index > 0:
                prev_flight = all_flight_numbers[current_index - 1]
                prev_flight_pos = text.rfind(prev_flight, 0, flight_pos)
                if prev_flight_pos != -1:
                    card_start = prev_flight_pos + len(prev_flight)
            
            # 在当前卡片内查找时间（航班号前后都可以）
            time_search_text = text[card_start:card_end]
            times_in_range = []
            for m in re.finditer(r'(\d{1,2}:\d{2})', time_search_text):
                time_pos = card_start + m.start()
                time_val = m.group(1)
                times_in_range.append({
                    'time': time_val,
                    'position': time_pos
                })
            
            # 按位置排序，选择最接近航班号的两个时间
            if len(times_in_range) >= 2:
                # 计算每个时间到航班号的距离
                for t in times_in_range:
                    t['distance'] = abs(t['position'] - flight_pos)
                # 按距离排序，选择最近的两个
                times_sorted = sorted(times_in_range, key=lambda x: x['distance'])
                dep_time = times_sorted[0]['time']
                arr_time = times_sorted[1]['time']
            elif len(times_in_range) == 1:
                dep_time = times_in_range[0]['time']
            
            # 改进的价格匹配：在当前航班卡片内查找价格（支持"¥XXX起"格式）
            price = 0.0
            discount_rate = ''
            cabin_class = '经济舱'
            
            # 价格应该在当前卡片内（卡片开始到下一个航班号之前）
            price_search_start = card_start  # 从卡片开始
            price_search_end = card_end  # 到下一个航班号之前
            price_search_text = text[price_search_start:price_search_end]
            
            # 找到所有价格及其位置
            price_candidates = []
            for m in re.finditer(
                r'(?:[¥￥]|CNY)\s*([0-9]+(?:\.[0-9]{1,2})?)(?:起|元)?|([0-9]+(?:\.[0-9]{1,2})?)\s*(?:起|元)',
                price_search_text):
                price_pos = price_search_start + m.start()  # 在原始文本中的位置
                try:
                    price_str = m.group(1) or m.group(2)
                    price_val = float(price_str) if price_str else 0.0
                    if price_val > 0 and price_val < 10000:  # 过滤明显错误的价格
                        # 计算到航班号的距离
                        distance = abs(price_pos - flight_pos)
                        # 优先选择在航班号之后的价格
                        is_after = price_pos > flight_pos
                        price_candidates.append({
                            'price': price_val,
                            'position': price_pos,
                            'distance': distance,
                            'is_after': is_after
                        })
                except (ValueError, TypeError):
                    continue
            
            if price_candidates:
                # 优先选择在航班号之后且距离最近的价格
                after_prices = [p for p in price_candidates if p['is_after']]
                if after_prices:
                    best_price = min(after_prices, key=lambda x: x['distance'])
                else:
                    # 如果都在之前，选择距离最近的
                    best_price = min(price_candidates, key=lambda x: x['distance'])
                
                price = best_price['price']
                
                # 在价格附近查找折扣信息（价格前后100字符内）
                discount_search_start = max(card_start, best_price['position'] - 50)
                discount_search_end = min(card_end, best_price['position'] + 150)
                discount_search_text = text[discount_search_start:discount_search_end]
                
                # 提取折扣信息：经济舱X.X折
                discount_match = re.search(r'(经济舱|商务舱|头等舱)\s*(\d+\.?\d*折)', discount_search_text)
                if discount_match:
                    cabin_class = discount_match.group(1)
                    discount_rate = discount_match.group(2)
                else:
                    # 尝试其他格式
                    discount_match = re.search(r'(\d+\.?\d*折)', discount_search_text)
                    if discount_match:
                        discount_rate = discount_match.group(1)
            
            return dep_time, arr_time, price, discount_rate, cabin_class
        
        # 为每个唯一航班号创建记录（即使没有完整信息也创建基本记录）
        for i, flight_num in enumerate(unique_flight_numbers):
            # 使用智能匹配找到最接近的时间、价格和折扣，传入所有航班号列表和当前索引
            dep_time, arr_time, price, discount_rate, cabin_class = find_nearest_info(
                flight_num, ocr_text, times, prices, unique_flight_numbers, i)
            
            # 如果智能匹配失败，回退到索引匹配
            if not dep_time and i < len(time_pairs):
                dep_time = time_pairs[i][0]
                arr_time = time_pairs[i][1]
            
            if price == 0.0 and i < len(prices):
                try:
                    price = float(prices[i]) if prices[i] else 0.0
                except (ValueError, TypeError):
                    price = 0.0

            # 尝试匹配机场
            dep_air = airports[i * 2] if i * 2 < len(airports) else ''
            arr_air = airports[i * 2 + 1] if i * 2 + 1 < len(airports) else ''
            
            # 调试信息
            if price > 0 or dep_time:
                discount_info = f", 折扣={discount_rate}" if discount_rate else ""
                cabin_info = f", 舱位={cabin_class}" if cabin_class != '经济舱' else ""
                price_info = f", 价格={price}" if price > 0 else ", 价格=未找到"
                print(f"🔍 航班 {flight_num}: 时间={dep_time}-{arr_time}{price_info}{discount_info}{cabin_info}")

            # 优先使用环境变量中的城市信息，如果环境变量为空则从机场代码提取
            dep_city = from_city if from_city else (
                _get_city_from_airport(dep_air) if dep_air else '')
            arr_city = to_city if to_city else (
                _get_city_from_airport(arr_air) if arr_air else '')

            # 优先使用环境变量中的出发日期，如果环境变量为空则从OCR文本提取
            final_departure_date = depart_date if depart_date else (
                dates[0] if dates else '')

            # 计算飞行时长
            flight_duration = ''
            if dep_time and arr_time:
                try:
                    dep_h, dep_m = map(int, dep_time.split(':'))
                    arr_h, arr_m = map(int, arr_time.split(':'))
                    dep_minutes = dep_h * 60 + dep_m
                    arr_minutes = arr_h * 60 + arr_m
                    # 处理跨天情况
                    if arr_minutes < dep_minutes:
                        arr_minutes += 24 * 60
                    duration_minutes = arr_minutes - dep_minutes
                    hours = duration_minutes // 60
                    minutes = duration_minutes % 60
                    flight_duration = f"{hours}小时{minutes}分钟" if hours > 0 else f"{minutes}分钟"
                except BaseException:
                    pass

            # 从备用页面源码中提取更多信息
            dep_name = ''
            arr_name = ''
            dep_t = ''
            arr_t = ''
            if page_source_fallback:
                dep_name = _get_airport_name(dep_air) if dep_air else ''
                arr_name = _get_airport_name(arr_air) if arr_air else ''
                dep_t, arr_t = _extract_terminals_from_page(
                    page_source_fallback, dep_name, arr_name)

            info = {
                'airline': _get_airline_from_code(flight_num),
                'flight_number': flight_num,
                'is_shared_flight': _detect_shared_flight(flight_num),
                'aircraft_type': _extract_aircraft_type(ocr_text[max(0, ocr_text.find(flight_num) - 300): ocr_text.find(flight_num) + 400]) if flight_num in ocr_text else '',
                'departure_date': final_departure_date,
                'departure_time': dep_time,
                'departure_airport': dep_air,
                'departure_city': dep_city,
                'arrival_time': arr_time,
                'arrival_airport': arr_air,
                'arrival_city': arr_city,
                'flight_duration': flight_duration,
                'has_stopover': '否',
                'stopover_city': '',
                'stopover_airport': '',
                'price': float(price) if price else 0.0,
                'currency': 'CNY',
                'cabin_class': cabin_class,  # 使用提取的舱位信息
                'discount_rate': discount_rate,  # 使用提取的折扣信息
                'original_price': None,
                'source': '12306',
                'status': 'active',
                'departure_airport_name': dep_name,
                'arrival_airport_name': arr_name,
                'departure_terminal': dep_t,
                'arrival_terminal': arr_t,
            }
            flights.append(info)

        print(f"📊 OCR解析完成，找到 {len(flights)} 个航班信息")
        return flights

    except Exception as e:
        print(f"❌ OCR解析失败: {e}")
        import traceback
        traceback.print_exc()
        return flights
