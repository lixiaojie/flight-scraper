import os
import re
import json
import requests
from datetime import datetime


def _load_airport_config():
    cfg_path = os.path.join(
        os.path.dirname(__file__),
        'config',
        'airports.json')
    try:
        with open(cfg_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('airportNames', {}), data.get('airportCities', {})
    except Exception:
        return {}, {}


AIRPORT_NAMES, AIRPORT_CITIES = _load_airport_config()


def _get_airport_name(code: str) -> str:
    if not code:
        return ''
    return AIRPORT_NAMES.get(code, f"{code}机场")


def _get_city_from_airport(code: str) -> str:
    return AIRPORT_CITIES.get(code, '')


def _get_airline_from_code(flight_number: str) -> str:
    airline_codes = {
        'CA': '中国国际航空', 'MU': '中国东方航空', 'CZ': '中国南方航空', 'HU': '海南航空',
        '3U': '四川航空', '9C': '春秋航空', 'JD': '首都航空', 'HO': '吉祥航空', 'ZH': '深圳航空',
    }
    if len(flight_number) >= 2:
        return airline_codes.get(flight_number[:2], f"{flight_number[:2]}航空")
    return '未知航空公司'


def _detect_shared_flight(flight_number: str) -> str:
    return '是' if (
        '共享' in flight_number or 'SHARE' in flight_number.upper()) else '否'


def _extract_aircraft_type(context: str) -> str:
    if not context:
        return ''
    patterns = [
        r'(空客\s*\d{3}(?:\([^)]+\))?)',
        r'(波音\s*[A-Za-z0-9]{2,6}(?:\([^)]+\))?)',
        r'\b(A\d{3})\b',
        r'\b(B\d{3})\b',
    ]
    for p in patterns:
        m = re.search(p, context)
        if m:
            return m.group(1)
    return ''


def _extract_terminals_from_page(
        page_source: str,
        dep_airport_name: str,
        arr_airport_name: str):
    try:
        text = page_source or ''
        cand = re.findall(r'([\u4e00-\u9fa5]{2,10}?(?:机场)?T\d)', text)
        seen, candidates = set(), []
        for c in cand:
            if c not in seen:
                seen.add(c)
                candidates.append(c)

        def norm(n: str) -> str:
            return (n or '').replace('国际', '').replace('机场', '')
        n_dep, n_arr = norm(dep_airport_name), norm(arr_airport_name)
        dep_t = next((c for c in candidates if n_dep and (
            n_dep in c or n_dep[:2] in c)), '')
        arr_t = next((c for c in candidates if n_arr and (
            n_arr in c or n_arr[:2] in c)), '')
        if (not dep_t or not arr_t) and len(candidates) >= 2:
            dep_t = dep_t or candidates[0]
            arr_t = arr_t or candidates[1]
        if not dep_t and not arr_t:
            pure = [
                f"T{x}" for x in re.findall(
                    r'(?<![A-Z])T(\d)(?![A-Za-z])',
                    text)]
            if len(pure) >= 2:
                dep_t, arr_t = pure[0], pure[1]
            elif len(pure) == 1:
                dep_t = pure[0]
        return dep_t, arr_t
    except Exception:
        return '', ''


def parse_page_source(page_source: str):
    flights = []
    try:
        # 优先使用环境变量中的城市和日期信息
        from_city = os.getenv('SCRAPER_FROM_CITY', '')
        to_city = os.getenv('SCRAPER_TO_CITY', '')
        depart_date = os.getenv('SCRAPER_DEPART_DATE', '')
        
        flight_numbers = re.findall(
            r'(?:[\u4e00-\u9fa5]{2,6})?\s*([A-Z]{2}\d{3,4})', page_source)
        times = re.findall(r'(\d{1,2}:\d{2})', page_source)
        prices = [
            m.group(1) or m.group(2) for m in re.finditer(
                r'(?:[¥￥]|CNY)\s*([0-9]+(?:\.[0-9]{1,2})?)|([0-9]+(?:\.[0-9]{1,2})?)\s*元',
                page_source)]
        airports = re.findall(r'([A-Z]{3})', page_source)
        dates = re.findall(
            r'(\d{1,2}月\d{1,2}日|\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}/\d{1,2}|\d{4}-\d{1,2}-\d{1,2})',
            page_source)
        time_pairs = [(times[i], times[i + 1])
                      for i in range(0, len(times) - 1, 2)]
        # 移除20个航班的限制，处理所有找到的航班
        max_flights = len(time_pairs)
        print(
            f"📊 找到 {len(flight_numbers)} 个航班号，{len(time_pairs)} 个时间对，{len(prices)} 个价格")
        for i, (dep_time, arr_time) in enumerate(time_pairs[:max_flights]):
            if i >= len(flight_numbers):
                continue
            flight_num = flight_numbers[i]
            if not re.match(r'^[A-Z]{2}\d{3,4}$', flight_num):
                continue
            price = prices[i] if i < len(prices) else ''
            dep_air = airports[i * 2] if i * 2 < len(airports) else ''
            arr_air = airports[i * 2 + 1] if i * 2 + 1 < len(airports) else ''
            dep_name = _get_airport_name(dep_air) if dep_air else ''
            arr_name = _get_airport_name(arr_air) if arr_air else ''
            dep_t, arr_t = _extract_terminals_from_page(
                page_source, dep_name, arr_name)
            
            # 优先使用环境变量中的城市信息，如果环境变量为空则从机场代码提取
            dep_city = from_city if from_city else (
                _get_city_from_airport(dep_air) if dep_air else '')
            arr_city = to_city if to_city else (
                _get_city_from_airport(arr_air) if arr_air else '')
            
            # 优先使用环境变量中的出发日期，如果没有则从页面提取
            final_departure_date = depart_date if depart_date else (dates[0] if dates else '')
            
            info = {
                'airline': _get_airline_from_code(flight_num),
                'flight_number': flight_num,
                'is_shared_flight': _detect_shared_flight(flight_num),
                'aircraft_type': _extract_aircraft_type(page_source[max(0, page_source.find(flight_num) - 300): page_source.find(flight_num) + 400]),
                'departure_date': final_departure_date,
                'departure_time': dep_time,
                'departure_airport': dep_air,
                'departure_city': dep_city,
                'arrival_time': arr_time,
                'arrival_airport': arr_air,
                'arrival_city': arr_city,
                'flight_duration': '',
                'has_stopover': '否',
                'stopover_city': '',
                'stopover_airport': '',
                'price': price,
                'currency': 'CNY',
                'cabin_class': '经济舱',
                'discount_rate': '',
                'original_price': None,
                'source': '12306',
                'status': 'active',
                'departure_airport_name': dep_name,
                'arrival_airport_name': arr_name,
                'departure_terminal': dep_t,
                'arrival_terminal': arr_t,
            }
            flights.append(info)
    except Exception as e:
        print(f"解析失败: {e}")
    return flights


def parse_and_save(page_source: str, task_id=None):
    flights = parse_page_source(page_source)

    api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
    api_url = f"{api_base}/api/flights/batch-save"
    
    # 如果没有提供task_id，尝试从环境变量获取
    if task_id is None:
        task_id = os.getenv("TASK_ID")
    
    # 确保task_id是整数类型
    if task_id:
        try:
            task_id = int(task_id)
        except (ValueError, TypeError):
            print(f"⚠️ task_id 格式错误: {task_id}，将设置为 None")
            task_id = None
    
    payload = {"flights": flights, "source": "12306", "task_id": task_id}
    try:
        resp = requests.post(api_url, json=payload, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"保存到数据库失败: {e}")

    out_dir = os.getenv(
        "SCRAPER_OUTPUT_DIR",
        os.path.join(
            os.getcwd(),
            "results"))
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(os.path.join(out_dir, f"parsed_flights_{ts}.json"), 'w', encoding='utf-8') as f:
        json.dump({"count": len(flights), "flights": flights},
                  f, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, "parsed_flights_latest.json"), 'w', encoding='utf-8') as f:
        json.dump({"count": len(flights), "flights": flights},
                  f, ensure_ascii=False, indent=2)

    return flights
