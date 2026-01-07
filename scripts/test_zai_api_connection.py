#!/usr/bin/env python3
"""
Z.ai API连接测试脚本
快速测试Z.ai API是否畅通，无需连接设备
"""
import os
import sys
import json
import base64
import requests
from io import BytesIO

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def create_test_image():
    """创建一个测试图片（包含航班信息）"""
    if not PIL_AVAILABLE:
        print("⚠️ PIL未安装，无法创建测试图片")
        return None
    
    # 创建一个简单的测试图片
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # 绘制一些测试文本
    try:
        # 尝试使用默认字体
        font = ImageFont.load_default()
    except:
        font = None
    
    # 绘制测试航班信息
    test_text = [
        "航班搜索结果",
        "MU6648  20:30 - 23:15",
        "成都双流T2 - 北京大兴",
        "¥450起  经济舱2.0折",
        "",
        "CZ3911  08:55 - 14:40",
        "深圳宝安T3 - 乌鲁木齐",
        "¥1260  经济舱3.3折"
    ]
    
    y = 50
    for line in test_text:
        if font:
            draw.text((50, y), line, fill='black', font=font)
        else:
            draw.text((50, y), line, fill='black')
        y += 60
    
    # 转换为字节
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    return img_bytes.getvalue()


def test_zai_api_connection():
    """测试Z.ai API连接"""
    print("=" * 80)
    print("Z.ai GLM-4.6V-Flash API连接测试")
    print("=" * 80)
    
    # 检查API密钥
    api_key = os.getenv('ZAI_API_KEY', '1f3dfbf15dfb41488e34c87ef478e023.Ez05JCLs9ix8GPTh')
    
    if not api_key:
        print("❌ 未设置ZAI_API_KEY环境变量")
        print("   请设置: export ZAI_API_KEY='your-api-key'")
        return False
    
    print(f"\n🔑 API密钥: {api_key[:20]}...{api_key[-10:]}")
    print(f"🌐 API端点: https://api.z.ai/api/paas/v4/chat/completions")
    print(f"🤖 模型: glm-4.6v-flash")
    
    # 创建测试图片
    print("\n📸 创建测试图片...")
    test_image = create_test_image()
    if not test_image:
        print("❌ 无法创建测试图片")
        return False
    
    # 编码图片
    base64_image = base64.b64encode(test_image).decode('utf-8')
    print(f"✅ 测试图片已创建（大小: {len(test_image)} 字节）")
    
    # 准备API请求
    url = "https://api.z.ai/api/paas/v4/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    prompt = """请分析这张航班搜索结果截图，提取每个航班卡片的信息。

要求：
1. 识别每个独立的航班卡片
2. 为每个航班卡片提取以下信息：
   - 航班号（如：MU6648, CZ3911等）
   - 出发时间（如：20:30）
   - 到达时间（如：23:15）
   - 出发机场（如：成都双流T2）
   - 到达机场（如：北京大兴）
   - 价格（如：¥450起）
   - 折扣信息（如：经济舱2.0折）
   - 舱位等级（经济舱/商务舱/头等舱）

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
    "cabin_class": "经济舱"
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
        "max_tokens": 2000
    }
    
    # 发送API请求
    print("\n" + "=" * 80)
    print("📡 发送API请求...")
    print("=" * 80)
    
    try:
        print("⏳ 正在调用Z.ai API...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"📊 HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API调用成功！")
            
            result = response.json()
            
            # 显示响应内容
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"\n📝 API响应内容（前200字符）:")
                print("-" * 80)
                print(content[:200])
                if len(content) > 200:
                    print("...")
                print("-" * 80)
                
                # 尝试解析JSON
                import re
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    try:
                        flights_data = json.loads(json_match.group(0))
                        print(f"\n✅ 成功解析JSON，提取到 {len(flights_data)} 条航班信息")
                        
                        # 显示解析结果
                        print("\n📊 解析结果:")
                        for i, flight in enumerate(flights_data, 1):
                            print(f"   {i}. {flight.get('flight_number', 'N/A')}: "
                                  f"{flight.get('departure_time', 'N/A')} - "
                                  f"{flight.get('arrival_time', 'N/A')}, "
                                  f"¥{flight.get('price', 0)}")
                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON解析失败: {e}")
                else:
                    print("⚠️ 响应中未找到JSON数组")
            else:
                print("⚠️ 响应格式异常")
                print(f"完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            print("\n" + "=" * 80)
            print("✅ API连接测试通过！")
            print("=" * 80)
            return True
            
        else:
            print(f"❌ API调用失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 401:
                print("\n💡 可能的原因:")
                print("   - API密钥无效或已过期")
                print("   - API密钥格式错误")
            elif response.status_code == 429:
                print("\n💡 可能的原因:")
                print("   - API调用频率超限")
                print("   - 请稍后重试")
            elif response.status_code == 500:
                print("\n💡 可能的原因:")
                print("   - Z.ai服务器内部错误")
                print("   - 请稍后重试")
            
            return False
            
    except requests.exceptions.Timeout:
        print("❌ API请求超时（30秒）")
        print("💡 可能的原因:")
        print("   - 网络连接问题")
        print("   - Z.ai服务器响应慢")
        return False
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 网络连接失败: {e}")
        print("💡 可能的原因:")
        print("   - 无法连接到Z.ai服务器")
        print("   - 网络配置问题")
        print("   - 防火墙阻止")
        return False
        
    except Exception as e:
        print(f"❌ API调用异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_zai_api_connection()
    sys.exit(0 if success else 1)
