# ==================== city_mapping_loader.py ====================
import json
import os

def load_city_mapping(file_path='city_mapping.json'):
    """
    加载城市映射配置文件
    
    返回:
        spot_to_district: 景点名 → 区县名
        district_to_id: 区县名 → 天气ID
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, file_path)
    
    if not os.path.exists(full_path):
        full_path = file_path
    
    if not os.path.exists(full_path):
        print(f"⚠️ 配置文件 {full_path} 不存在，使用默认映射")
        return get_default_mapping()
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        spot_to_district = data.get('景点映射', {})
        district_to_id = data.get('城市ID映射', {})
        
        print(f"✅ 成功加载配置文件：{len(spot_to_district)} 个景点映射，{len(district_to_id)} 个区县ID")
        return spot_to_district, district_to_id
        
    except Exception as e:
        print(f"❌ 加载配置文件失败：{e}")
        return get_default_mapping()


def get_default_mapping():
    """默认映射（当配置文件不存在时使用）"""
    spot_to_district = {
        "武隆天生三桥": "武隆",
        "大足石刻": "大足",
        "解放碑步行街": "渝中",
        "磁器口古镇": "沙坪坝",
        "千岛湖": "杭州",  # 非重庆景点保留
        "鼓浪屿": "厦门",
    }
    
    district_to_id = {
        "渝中": "101040100",
        "沙坪坝": "101040100",
        "南岸": "101040100",
        "大足": "101040108",
        "武隆": "101040112",
        "涪陵": "101040101",
        "万州": "101040201",
        "黔江": "101040125",
        "杭州": "101210101",
        "厦门": "101230201",
    }
    
    return spot_to_district, district_to_id


# ==================== 快速测试 ====================
if __name__ == "__main__":
    spot_to_district, district_to_id = load_city_mapping()
    
    print("\n📋 景点→区县 映射：")
    for spot, district in list(spot_to_district.items())[:10]:
        print(f"  {spot} → {district}")
    
    print("\n📋 区县→ID 映射（部分）：")
    for district, district_id in list(district_to_id.items())[:10]:
        print(f"  {district} → {district_id}")
    
    # 测试：获取武隆的天气
    test_spot = "武隆天生三桥"
    if test_spot in spot_to_district:
        district = spot_to_district[test_spot]
        city_id = district_to_id.get(district)
        print(f"\n✅ {test_spot} → {district} → {city_id}")