#!/usr/bin/env python3
"""
航班识别调试脚本
使用当前识别方法识别航班结果页，打印所有识别到的字段以便核对调试

配置：
- API提供商: z.ai
- 模型版本: GLM_4.6V_Flash
- API密钥: 1f3dfbf15dfb41488e34c87ef478e023.Ez05JCLs9ix8GPTh
"""
import os
import sys
import json
from datetime import datetime

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from device_connection import connect_device
    from parser_llm_vision import parse_screenshot_with_llm
    from parser_ocr import parse_ocr_text
    from page_capture_ocr import smart_scroll_and_capture_ocr
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("\n💡 提示:")
    print("   如果是在本地运行，请安装依赖:")
    print("   pip install requests Pillow pytesseract")
    print("\n   或者在Docker容器中运行:")
    print("   docker-compose --profile scraper run --rm flight-scraper python3 /app/scripts/test_flight_recognition_debug.py")
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
    
    # 打印原始字典（用于调试）
    print(f"\n原始数据:")
    print(json.dumps(flight, ensure_ascii=False, indent=2))


def test_flight_recognition():
    """测试航班识别功能"""
    print("=" * 80)
    print("航班识别调试测试")
    print("=" * 80)
    
    # 检查API密钥
    llm_api_type = os.getenv('LLM_API_TYPE', 'zai')
    llm_api_key = None
    
    if llm_api_type in ['zai', 'glm']:
        llm_api_key = os.getenv('ZAI_API_KEY', '1f3dfbf15dfb41488e34c87ef478e023.Ez05JCLs9ix8GPTh')
        if not llm_api_key:
            print("⚠️ 未设置ZAI_API_KEY环境变量")
            print("   将使用OCR方法作为备用")
        else:
            print(f"✅ 使用Z.ai GLM-4.6V-Flash API")
            print(f"🔑 API密钥: {llm_api_key[:20]}...{llm_api_key[-10:]}")
    elif llm_api_type == 'openai':
        llm_api_key = os.getenv('OPENAI_API_KEY')
    elif llm_api_type == 'anthropic':
        llm_api_key = os.getenv('ANTHROPIC_API_KEY')
    elif llm_api_type == 'google':
        llm_api_key = os.getenv('GOOGLE_API_KEY')
    
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
        
        # 创建输出目录
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'results', 'recognition_debug')
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取截图
        print("\n📸 获取页面截图...")
        screenshot = driver.get_screenshot_as_png()
        
        # 保存截图
        screenshot_path = os.path.join(output_dir, f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        with open(screenshot_path, 'wb') as f:
            f.write(screenshot)
        print(f"💾 截图已保存: {screenshot_path}")
        
        flights = []
        method_used = None
        
        # 尝试使用LLM Vision API
        if llm_api_key and llm_api_type:
            print("\n" + "=" * 80)
            print(f"🤖 尝试使用 {llm_api_type.upper()} API解析截图...")
            print("=" * 80)
            try:
                flights = parse_screenshot_with_llm(driver, api_type=llm_api_type, api_key=llm_api_key)
                if flights:
                    method_used = f"LLM Vision ({llm_api_type})"
                    print(f"✅ {method_used}解析成功，提取到 {len(flights)} 条航班信息")
                else:
                    print(f"⚠️ {llm_api_type.upper()} API未提取到航班信息，尝试OCR方法...")
            except Exception as e:
                print(f"⚠️ {llm_api_type.upper()} API解析失败: {e}，尝试OCR方法...")
                import traceback
                traceback.print_exc()
        
        # 如果LLM失败，使用OCR方法
        if not flights:
            print("\n" + "=" * 80)
            print("🔍 使用OCR方法解析截图...")
            print("=" * 80)
            try:
                # 获取OCR文本
                from page_capture_ocr import smart_scroll_and_capture_ocr
                flights_set, ocr_text = smart_scroll_and_capture_ocr(
                    driver, output_dir, use_ocr=True, max_scrolls=3, min_scrolls=1)
                
                if ocr_text:
                    # 解析OCR文本
                    page_source = driver.page_source if hasattr(driver, 'page_source') else None
                    flights = parse_ocr_text(ocr_text, page_source_fallback=page_source)
                    method_used = "OCR"
                    print(f"✅ OCR解析成功，提取到 {len(flights)} 条航班信息")
                else:
                    print("⚠️ OCR未识别到文本")
            except Exception as e:
                print(f"⚠️ OCR解析失败: {e}")
                import traceback
                traceback.print_exc()
        
        if not flights:
            print("\n❌ 未提取到任何航班信息")
            print("\n可能的原因:")
            print("   1. API调用失败（检查网络连接和API密钥）")
            print("   2. 截图未包含航班信息")
            print("   3. 识别方法解析失败")
            return
        
        # 打印识别方法
        print("\n" + "=" * 80)
        print(f"📊 识别方法: {method_used}")
        print(f"📊 识别到的航班总数: {len(flights)}")
        print("=" * 80)
        
        # 详细显示每个航班的解析结果
        for i, flight in enumerate(flights, 1):
            print_flight_details(flight, i)
        
        # 保存结果
        result_file = os.path.join(output_dir, f"recognition_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
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
            print(f"   - {flight_num}: {dep_time}-{arr_time}, ¥{price}")
        
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
    test_flight_recognition()
