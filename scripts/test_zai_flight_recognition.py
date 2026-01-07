#!/usr/bin/env python3
"""
Z.ai航班识别测试脚本
快速测试Z.ai GLM-4.6V-Flash API的航班识别效果
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
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("\n💡 提示:")
    print("   如果是在本地运行，请安装依赖:")
    print("   pip install requests Pillow")
    print("\n   或者在Docker容器中运行:")
    print("   docker-compose --profile scraper run --rm flight-scraper python3 /app/scripts/test_zai_flight_recognition.py")
    sys.exit(1)


def test_zai_flight_recognition():
    """测试Z.ai航班识别功能"""
    print("=" * 80)
    print("Z.ai GLM-4.6V-Flash 航班识别测试")
    print("=" * 80)
    
    # 检查API密钥
    api_key = os.getenv('ZAI_API_KEY')
    if not api_key:
        print("⚠️ 未设置ZAI_API_KEY环境变量")
        print("   请设置: export ZAI_API_KEY='your-api-key'")
        print("\n   或使用提供的API密钥:")
        print("   export ZAI_API_KEY='1f3dfbf15dfb41488e34c87ef478e023.Ez05JCLs9ix8GPTh'")
        return
    
    print(f"\n🔌 使用Z.ai GLM-4.6V-Flash API")
    print(f"🔑 API密钥: {api_key[:20]}...{api_key[-10:]}")
    
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
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'results', 'zai_test')
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取截图
        print("\n📸 获取页面截图...")
        screenshot = driver.get_screenshot_as_png()
        
        # 保存截图
        screenshot_path = os.path.join(output_dir, f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        with open(screenshot_path, 'wb') as f:
            f.write(screenshot)
        print(f"💾 截图已保存: {screenshot_path}")
        
        # 使用Z.ai API解析
        print("\n" + "=" * 80)
        print("🤖 使用Z.ai GLM-4.6V-Flash解析截图...")
        print("=" * 80)
        
        flights = parse_screenshot_with_llm(driver, api_type='zai', api_key=api_key)
        
        if not flights:
            print("⚠️ 未提取到航班信息")
            print("\n可能的原因:")
            print("   1. API调用失败（检查网络连接和API密钥）")
            print("   2. 截图未包含航班信息")
            print("   3. 大模型解析失败")
            return
        
        print(f"\n✅ 解析完成，提取到 {len(flights)} 条航班信息")
        
        # 详细显示每个航班的解析结果
        print("\n" + "=" * 80)
        print("📊 航班信息详情")
        print("=" * 80)
        
        for i, flight in enumerate(flights, 1):
            print(f"\n{i}. 航班号: {flight.get('flight_number', 'N/A')}")
            print(f"   航空公司: {flight.get('airline', 'N/A')}")
            print(f"   出发时间: {flight.get('departure_time', 'N/A')}")
            print(f"   到达时间: {flight.get('arrival_time', 'N/A')}")
            print(f"   出发机场: {flight.get('departure_airport_name', flight.get('departure_airport', 'N/A'))}")
            print(f"   到达机场: {flight.get('arrival_airport_name', flight.get('arrival_airport', 'N/A'))}")
            print(f"   飞行时长: {flight.get('flight_duration', 'N/A')}")
            print(f"   价格: ¥{flight.get('price', 0.0)}")
            if flight.get('discount_rate'):
                print(f"   折扣: {flight.get('discount_rate')}")
            if flight.get('cabin_class'):
                print(f"   舱位: {flight.get('cabin_class')}")
            if flight.get('aircraft_type'):
                print(f"   机型: {flight.get('aircraft_type')}")
        
        # 保存结果
        result_file = os.path.join(output_dir, f"zai_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
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
        print(f"   平均价格: ¥{sum(f.get('price', 0) for f in flights) / len(flights) if flights else 0:.2f}")
        
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
                print(f"   价格: ¥{found_flight.get('price', 0.0)}")
                print(f"   时间: {found_flight.get('departure_time', 'N/A')} - {found_flight.get('arrival_time', 'N/A')}")
                if found_flight.get('discount_rate'):
                    print(f"   折扣: {found_flight.get('discount_rate')}")
                if found_flight.get('cabin_class'):
                    print(f"   舱位: {found_flight.get('cabin_class')}")
            else:
                print(f"❌ 未找到航班 {check_flight}")
                print(f"\n已识别的航班号列表:")
                for f in flights:
                    print(f"   - {f.get('flight_number', 'N/A')}")
        
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
    test_zai_flight_recognition()
