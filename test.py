import requests

BASE_URL = "https://k262b8er2b.re.qweatherapi.com"
API_KEY = "bfd35bb41fa343c39e58801bc3075a19"

# 城市 ID 映射
CITY_IDS = {
    "重庆": "101040100",
    "杭州": "101210101",
    "北京": "101010100",
    "上海": "101020100",
    "成都": "101270101",
    "厦门": "101230201"
}

def test_weather(city_name):
    """测试天气API"""
    city_id = CITY_IDS.get(city_name)
    if not city_id:
        print(f"❌ 未找到城市 {city_name} 的 ID")
        return False
    
    url = f"{BASE_URL}/v7/weather/now?location={city_id}&key={API_KEY}"
    
    print(f"📌 正在测试城市: {city_name} (ID: {city_id})")
    print(f"📌 请求URL: {url}")
    print("-" * 40)
    
    try:
        resp = requests.get(url, timeout=10)
        print(f"✅ HTTP状态码: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ API返回码: {data.get('code')}")
            
            if data.get('code') == '200':
                now = data.get('now', {})
                print("\n📊 天气数据：")
                print(f"  城市: {city_name}")
                print(f"  温度: {now.get('temp', 'N/A')}°C")
                print(f"  体感温度: {now.get('feelsLike', 'N/A')}°C")
                print(f"  天气状况: {now.get('text', 'N/A')}")
                print(f"  风向: {now.get('windDir', 'N/A')}")
                print(f"  风力: {now.get('windScale', 'N/A')}级")
                print(f"  湿度: {now.get('humidity', 'N/A')}%")
                print("\n✅ 天气API工作正常！")
                return True
            else:
                print(f"❌ API返回错误码: {data.get('code')}")
                print(f"   完整返回: {data}")
                return False
        else:
            print(f"❌ HTTP请求失败: {resp.status_code}")
            print(f"   返回内容: {resp.text}")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

# ==================== 测试 ====================
if __name__ == "__main__":
    print("=" * 50)
    print("🌤️ 和风天气 API 测试")
    print("=" * 50)
    
    test_weather("重庆")
    print("\n" + "=" * 50)
    test_weather("杭州")
    print("\n" + "=" * 50)
    test_weather("北京")