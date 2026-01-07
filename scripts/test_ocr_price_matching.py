#!/usr/bin/env python3
"""
OCR价格匹配测试脚本
连接模拟设备，验证OCR解析器中价格匹配的准确性

运行方式：
1. 在Docker容器中运行（推荐）:
   docker-compose exec scraper python3 /app/scripts/test_ocr_price_matching.py

2. 或者在本地运行（需要安装依赖）:
   pip install appium-python-client Pillow pytesseract
   python3 scripts/test_ocr_price_matching.py
"""
import os
import sys
import time
from datetime import datetime

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from device_connection import connect_device
    from page_capture_ocr import smart_scroll_and_capture_ocr, extract_flights_from_screenshot
    from parser_ocr import parse_ocr_text
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("\n💡 提示:")
    print("   如果是在本地运行，请安装依赖:")
    print("   pip install appium-python-client Pillow pytesseract")
    print("\n   或者在Docker容器中运行:")
    print("   docker-compose exec scraper python3 /app/scripts/test_ocr_price_matching.py")
    sys.exit(1)

def test_ocr_price_matching():
    """测试OCR价格匹配功能"""
    print("=" * 80)
    print("OCR价格匹配测试")
    print("=" * 80)
    
    # 连接设备
    print("\n🔌 连接设备...")
    try:
        driver = connect_device()
        if not driver:
            print("❌ 设备连接失败")
            return
        print("✅ 设备连接成功")
    except Exception as e:
        print(f"❌ 设备连接失败: {e}")
        return
    
    try:
        # 等待用户确认当前页面是否为航班结果页
        print("\n" + "=" * 80)
        print("📋 请确认:")
        print("   1. 模拟设备当前是否停留在航班结果页面？")
        print("   2. 如果是，请按回车继续")
        print("   3. 如果不是，请先导航到航班结果页面，然后按回车")
        print("=" * 80)
        input("按回车继续...")
        
        # 获取当前页面截图和OCR文本
        print("\n📸 开始OCR识别...")
        print("-" * 80)
        
        # 创建输出目录
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'results', 'ocr_test')
        os.makedirs(output_dir, exist_ok=True)
        
        # 使用OCR提取航班信息
        all_flights, combined_ocr_text, screenshot_paths = smart_scroll_and_capture_ocr(
            driver, 
            output_dir,
            use_ocr=True,
            max_scrolls=5,  # 测试时只滚动5次
            min_scrolls=2
        )
        
        print(f"\n✅ OCR识别完成:")
        print(f"   - 识别到 {len(all_flights)} 个唯一航班")
        print(f"   - 航班列表: {sorted(all_flights)}")
        
        if not combined_ocr_text:
            print("⚠️ 未获取到OCR文本")
            return
        
        # 保存OCR文本用于调试
        ocr_text_file = os.path.join(output_dir, f"ocr_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(ocr_text_file, 'w', encoding='utf-8') as f:
            f.write(combined_ocr_text)
        print(f"💾 OCR文本已保存: {ocr_text_file}")
        
        # 解析OCR文本
        print("\n" + "=" * 80)
        print("🔍 解析OCR文本，提取完整航班信息...")
        print("=" * 80)
        
        # 设置环境变量（用于解析器）
        os.environ['SCRAPER_FROM_CITY'] = os.getenv('SCRAPER_FROM_CITY', '')
        os.environ['SCRAPER_TO_CITY'] = os.getenv('SCRAPER_TO_CITY', '')
        os.environ['SCRAPER_DEPART_DATE'] = os.getenv('SCRAPER_DEPART_DATE', '')
        
        flights = parse_ocr_text(combined_ocr_text)
        
        print(f"\n✅ 解析完成，提取到 {len(flights)} 条航班信息")
        
        # 详细显示每个航班的匹配结果
        print("\n" + "=" * 80)
        print("📊 航班价格匹配详情")
        print("=" * 80)
        
        # 按价格排序显示
        flights_sorted = sorted(flights, key=lambda x: x.get('price', 0))
        
        for i, flight in enumerate(flights_sorted, 1):
            flight_num = flight.get('flight_number', 'N/A')
            price = flight.get('price', 0.0)
            dep_time = flight.get('departure_time', 'N/A')
            arr_time = flight.get('arrival_time', 'N/A')
            dep_city = flight.get('departure_city', 'N/A')
            arr_city = flight.get('arrival_city', 'N/A')
            
            print(f"\n{i}. 航班号: {flight_num}")
            print(f"   价格: {price} 元")
            if flight.get('discount_rate'):
                print(f"   折扣: {flight.get('discount_rate')}")
            if flight.get('cabin_class'):
                print(f"   舱位: {flight.get('cabin_class')}")
            print(f"   时间: {dep_time} - {arr_time}")
            print(f"   路线: {dep_city} → {arr_city}")
            
            # 在OCR文本中查找该航班号附近的内容
            if flight_num in combined_ocr_text:
                flight_pos = combined_ocr_text.find(flight_num)
                # 显示航班号前后300字符的内容（扩大范围以查看完整卡片）
                context_start = max(0, flight_pos - 300)
                context_end = min(len(combined_ocr_text), flight_pos + 400)
                context = combined_ocr_text[context_start:context_end]
                
                print(f"   📄 OCR上下文（航班号位置: {flight_pos}）:")
                print(f"      {context[:100]}...")
                
                # 查找该范围内的所有价格（支持"¥XXX起"格式）
                import re
                prices_in_context = []
                for m in re.finditer(
                    r'(?:[¥￥]|CNY)\s*([0-9]+(?:\.[0-9]{1,2})?)(?:起|元)?|([0-9]+(?:\.[0-9]{1,2})?)\s*(?:起|元)',
                    context):
                    price_str = m.group(1) or m.group(2)
                    if price_str:
                        try:
                            price_val = float(price_str)
                            price_pos_in_context = m.start()
                            price_pos_absolute = context_start + price_pos_in_context
                            distance = abs(price_pos_absolute - flight_pos)
                            prices_in_context.append({
                                'price': price_val,
                                'position': price_pos_absolute,
                                'distance': distance,
                                'is_after': price_pos_absolute > flight_pos
                            })
                        except:
                            pass
                
                # 查找折扣信息
                discount_info = None
                if flight_num in combined_ocr_text:
                    flight_pos_abs = combined_ocr_text.find(flight_num)
                    discount_search_start = max(0, flight_pos_abs - 100)
                    discount_search_end = min(len(combined_ocr_text), flight_pos_abs + 500)
                    discount_search_text = combined_ocr_text[discount_search_start:discount_search_end]
                    
                    discount_match = re.search(r'(经济舱|商务舱|头等舱)\s*(\d+\.?\d*折)', discount_search_text)
                    if discount_match:
                        discount_info = {
                            'cabin_class': discount_match.group(1),
                            'discount_rate': discount_match.group(2)
                        }
                
                if prices_in_context:
                    print(f"   📍 附近找到的价格:")
                    for p in sorted(prices_in_context, key=lambda x: x['distance']):
                        direction = "之后" if p['is_after'] else "之前"
                        marker = "✅" if p['price'] == price else "  "
                        print(f"      {marker} {p['price']} 元 (距离: {p['distance']} 字符, {direction})")
                    if price > 0:
                        matched_price = next((p for p in prices_in_context if p['price'] == price), None)
                        if matched_price:
                            print(f"   ✅ 匹配的价格: {price} 元 (距离: {matched_price['distance']} 字符, {'之后' if matched_price['is_after'] else '之前'})")
                        else:
                            print(f"   ⚠️ 警告: 匹配的价格 {price} 元不在附近找到的价格列表中")
                else:
                    print(f"   ⚠️ 未在附近找到价格")
        
        # 保存详细结果
        result_file = os.path.join(output_dir, f"price_matching_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("OCR价格匹配测试结果\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"识别到的航班数: {len(all_flights)}\n")
            f.write(f"解析出的航班信息数: {len(flights)}\n\n")
            
            f.write("航班价格匹配详情:\n")
            f.write("-" * 80 + "\n")
            for i, flight in enumerate(flights_sorted, 1):
                flight_num = flight.get('flight_number', 'N/A')
                price = flight.get('price', 0.0)
                dep_time = flight.get('departure_time', 'N/A')
                arr_time = flight.get('arrival_time', 'N/A')
                f.write(f"\n{i}. {flight_num}: {price} 元 ({dep_time} - {arr_time})\n")
        
        print(f"\n💾 详细结果已保存: {result_file}")
        
        # 特别检查用户提到的航班
        print("\n" + "=" * 80)
        print("🔍 特定航班检查")
        print("=" * 80)
        print("请输入要检查的航班号（如 CZ8848），按回车跳过:")
        check_flight = input("航班号: ").strip().upper()
        
        if check_flight:
            found_flight = next((f for f in flights if f.get('flight_number') == check_flight), None)
            if found_flight:
                print(f"\n✅ 找到航班 {check_flight}:")
                print(f"   价格: {found_flight.get('price', 0.0)} 元")
                print(f"   时间: {found_flight.get('departure_time', 'N/A')} - {found_flight.get('arrival_time', 'N/A')}")
                
                # 显示该航班在OCR文本中的上下文
                if check_flight in combined_ocr_text:
                    flight_pos = combined_ocr_text.find(check_flight)
                    context_start = max(0, flight_pos - 300)
                    context_end = min(len(combined_ocr_text), flight_pos + 500)
                    context = combined_ocr_text[context_start:context_end]
                    
                    print(f"\n📄 OCR文本上下文（航班号前后）:")
                    print("-" * 80)
                    # 高亮显示航班号和价格
                    highlighted_context = context.replace(
                        check_flight, f"【{check_flight}】"
                    )
                    # 高亮显示价格（支持"¥XXX起"格式）
                    import re
                    for m in re.finditer(
                        r'(?:[¥￥]|CNY)\s*([0-9]+(?:\.[0-9]{1,2})?)(?:起|元)?|([0-9]+(?:\.[0-9]{1,2})?)\s*(?:起|元)',
                        highlighted_context):
                        price_str = m.group(1) or m.group(2)
                        if price_str:
                            highlighted_context = highlighted_context.replace(
                                m.group(0), f"【{m.group(0)}】"
                            )
                    
                    # 高亮显示折扣信息
                    for m in re.finditer(
                        r'(经济舱|商务舱|头等舱)\s*(\d+\.?\d*折)',
                        highlighted_context):
                        highlighted_context = highlighted_context.replace(
                            m.group(0), f"【{m.group(0)}】"
                        )
                    print(highlighted_context)
                    print("-" * 80)
            else:
                print(f"❌ 未找到航班 {check_flight}")
        
        print("\n" + "=" * 80)
        print("✅ 测试完成")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔚 关闭驱动...")
        try:
            driver.quit()
        except:
            pass
        print("✅ 测试结束")


if __name__ == "__main__":
    test_ocr_price_matching()
