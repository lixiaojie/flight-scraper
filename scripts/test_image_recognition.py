#!/usr/bin/env python3
"""
从图片文件识别航班信息
使用z.ai GLM-4.6V-Flash API识别图片中的航班信息
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from parser_llm_vision import parse_flights_with_llm_vision
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("\n💡 提示:")
    print("   如果是在本地运行，请安装依赖:")
    print("   pip install requests Pillow")
    print("\n   或者在Docker容器中运行:")
    print("   docker-compose --profile scraper run --rm flight-scraper python3 /app/scripts/test_image_recognition.py <图片路径>")
    sys.exit(1)


def print_flight_details(flight, index):
    """打印航班详细信息"""
    print(f"\n{'='*80}")
    print(f"航班 #{index}")
    print(f"{'='*80}")
    
    # 基本信息
    print(f"航班号: {flight.get('flight_number', 'N/A')}")
    print(f"航空公司: {flight.get('airline', 'N/A')}")
    
    # 时间信息
    print(f"\n时间信息:")
    print(f"  出发时间: {flight.get('departure_time', 'N/A')}")
    print(f"  到达时间: {flight.get('arrival_time', 'N/A')}")
    print(f"  飞行时长: {flight.get('flight_duration', 'N/A')}")
    
    # 机场信息
    print(f"\n机场信息:")
    print(f"  出发机场: {flight.get('departure_airport', 'N/A')}")
    print(f"  出发城市: {flight.get('departure_city', 'N/A')}")
    print(f"  出发航站楼: {flight.get('departure_terminal', 'N/A')}")
    print(f"  到达机场: {flight.get('arrival_airport', 'N/A')}")
    print(f"  到达城市: {flight.get('arrival_city', 'N/A')}")
    print(f"  到达航站楼: {flight.get('arrival_terminal', 'N/A')}")
    
    # 价格信息
    print(f"\n价格信息:")
    print(f"  价格: ¥{flight.get('price', 0.0)}")
    print(f"  货币: {flight.get('currency', 'CNY')}")
    print(f"  折扣率: {flight.get('discount_rate', 'N/A')}")
    print(f"  舱位等级: {flight.get('cabin_class', 'N/A')}")
    print(f"  原价: {flight.get('original_price', 'N/A')}")
    
    # 航班详情
    print(f"\n航班详情:")
    print(f"  机型: {flight.get('aircraft_type', 'N/A')}")
    print(f"  是否经停: {flight.get('has_stopover', 'N/A')}")
    print(f"  经停城市: {flight.get('stopover_city', 'N/A')}")
    print(f"  经停机场: {flight.get('stopover_airport', 'N/A')}")
    print(f"  是否共享航班: {flight.get('is_shared_flight', 'N/A')}")
    
    # 其他信息
    print(f"\n其他信息:")
    print(f"  出发日期: {flight.get('departure_date', 'N/A')}")
    print(f"  数据源: {flight.get('source', 'N/A')}")
    print(f"  状态: {flight.get('status', 'N/A')}")
    print(f"  备注: {flight.get('notes', 'N/A')}")


def recognize_flights_from_image(image_path):
    """从图片文件识别航班信息"""
    print("=" * 80)
    print("从图片文件识别航班信息")
    print("=" * 80)
    
    # 检查图片文件是否存在
    if not os.path.exists(image_path):
        print(f"❌ 图片文件不存在: {image_path}")
        return
    
    print(f"\n📸 读取图片: {image_path}")
    
    # 读取图片
    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        print(f"✅ 图片读取成功，大小: {len(image_bytes)} 字节")
    except Exception as e:
        print(f"❌ 读取图片失败: {e}")
        return
    
    # 检查API密钥
    api_key = os.getenv('ZAI_API_KEY', '1f3dfbf15dfb41488e34c87ef478e023.Ez05JCLs9ix8GPTh')
    api_type = os.getenv('LLM_API_TYPE', 'zai')
    
    print(f"\n🔧 API配置:")
    print(f"   API类型: {api_type}")
    print(f"   API密钥: {api_key[:20]}...{api_key[-10:]}")
    
    # 使用LLM Vision API识别
    print("\n" + "=" * 80)
    print(f"🤖 使用 {api_type.upper()} API识别图片...")
    print("=" * 80)
    
    try:
        flights = parse_flights_with_llm_vision(image_bytes, api_type=api_type, api_key=api_key)
        
        if not flights:
            print("⚠️ 未提取到航班信息")
            return
        
        print(f"\n✅ 识别成功，提取到 {len(flights)} 条航班信息")
        
        # 详细显示每个航班的解析结果
        print("\n" + "=" * 80)
        print("📊 航班信息详情")
        print("=" * 80)
        
        for i, flight in enumerate(flights, 1):
            print_flight_details(flight, i)
        
        # 保存结果
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'results', 'image_recognition')
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        image_name = Path(image_path).stem
        result_file = os.path.join(output_dir, f"{image_name}_result_{timestamp}.json")
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(flights, f, ensure_ascii=False, indent=2)
        print(f"\n💾 结果已保存: {result_file}")
        
        # 统计信息
        print("\n" + "=" * 80)
        print("📈 识别统计")
        print("=" * 80)
        print(f"   总航班数: {len(flights)}")
        print(f"   有价格的航班: {sum(1 for f in flights if f.get('price', 0) > 0)}")
        print(f"   有折扣信息的航班: {sum(1 for f in flights if f.get('discount_rate'))}")
        print(f"   有时间的航班: {sum(1 for f in flights if f.get('departure_time') and f.get('arrival_time'))}")
        if flights:
            avg_price = sum(f.get('price', 0) for f in flights) / len(flights)
            print(f"   平均价格: ¥{avg_price:.2f}")
        
        # 航班号列表
        print(f"\n识别到的航班号列表:")
        for f in flights:
            flight_num = f.get('flight_number', 'N/A')
            price = f.get('price', 0)
            dep_time = f.get('departure_time', 'N/A')
            arr_time = f.get('arrival_time', 'N/A')
            discount = f.get('discount_rate', 'N/A')
            print(f"   - {flight_num}: {dep_time}-{arr_time}, ¥{price}, {discount}")
        
        # 对比实际数据（根据图片描述）
        print("\n" + "=" * 80)
        print("🔍 与图片实际数据对比")
        print("=" * 80)
        print("图片中的实际航班数据:")
        print("   1. 3U8231: 06:55-08:45, ¥360, 经济舱1.6折")
        print("   2. HU7768: 10:45-12:50, ¥440, 经济舱2.4折")
        print("   3. CZ5258: 10:55-13:00, ¥440, 经济舱2.4折")
        print("   4. CZ3460: 13:50-15:55, ¥560, 经济舱3.0折")
        print("\n识别结果:")
        for f in flights:
            flight_num = f.get('flight_number', 'N/A')
            price = f.get('price', 0)
            dep_time = f.get('departure_time', 'N/A')
            arr_time = f.get('arrival_time', 'N/A')
            discount = f.get('discount_rate', 'N/A')
            print(f"   - {flight_num}: {dep_time}-{arr_time}, ¥{price}, {discount}")
        
        print("\n" + "=" * 80)
        print("✅ 识别完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 识别失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python3 test_image_recognition.py <图片路径>")
        print("\n示例:")
        print("  python3 test_image_recognition.py /path/to/screenshot.png")
        print("  python3 test_image_recognition.py results/screenshots/flight_results.png")
        sys.exit(1)
    
    image_path = sys.argv[1]
    recognize_flights_from_image(image_path)
