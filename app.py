# ==================== app.py（和风天气完整版 - 基于城市ID）====================
# 运行前安装依赖：pip install flask flask-cors requests

from flask import Flask, request, jsonify
from flask_cors import CORS
import csv
import requests
from collections import Counter
import re
import uuid
import urllib.parse
from datetime import datetime
import time

app = Flask(__name__)
app.secret_key = 'travel-assistant-secret-key-2024'
CORS(app)

import os
from dotenv import load_dotenv

# ==================== 加载环境变量 ====================
# 加载 .env 文件（本地开发用）
load_dotenv()

# ==================== 配置（全部从环境变量读取）====================
# 硅基流动 API Key（必须）
SILICONFLOW_API_KEY = os.environ.get('SILICONFLOW_API_KEY')
if not SILICONFLOW_API_KEY:
    print("⚠️ 警告：SILICONFLOW_API_KEY 未设置！")
    print("   请在 Railway 的 Variables 中添加，或在 .env 文件中配置")

# 和风天气 API Key（如果还在用和风天气）
API_KEY = os.environ.get('API_KEY')
BASE_URL="https://k262b8er2b.re.qweatherapi.com"
if not API_KEY:
    print("ℹ️ 未设置 API_KEY（如使用 wttr.in 则无需配置）")

# 天气服务切换：True=使用和风天气，False=使用wttr.in（免费无需Key）
USE_QWEATHER = os.environ.get('USE_QWEATHER', 'false').lower() == 'true'

print(f"✅ 配置加载完成")
print(f"   硅基流动 API: {'✅ 已配置' if SILICONFLOW_API_KEY else '❌ 未配置'}")
print(f"   天气服务: {'和风天气' if USE_QWEATHER else 'wttr.in（免费）'}")

# ==================== 城市 ID 映射 ====================
CITY_IDS = {
    # 直辖市
    "北京": "101010100",
    "上海": "101020100",
    "重庆": "101040100",
    "天津": "101030100",
    
    # 重庆各区县（都映射到重庆）
    "合川": "101040100",  # 合川区（重庆）
    "巴南": "101040100",  # 巴南区（重庆）
    "北碚": "101040100",  # 北碚区（重庆）
    "大渡口": "101040100",  # 大渡口区（重庆）
    "九龙坡": "101040100",  # 九龙坡区（重庆）
    "永川": "101040100",  # 永川区（重庆）
    "璧山": "101040100",  # 璧山区（重庆）
    "铜梁": "101040100",  # 铜梁区（重庆）
    "潼南": "101040100",  # 潼南区（重庆）
    "荣昌": "101040100",  # 荣昌区（重庆）
    "梁平": "101040100",  # 梁平区（重庆）
    "奉节": "101040100",  # 奉节县（重庆）
    "巫山": "101040100",  # 巫山县（重庆）
    "巫溪": "101040100",  # 巫溪县（重庆）
    "城口": "101040100",  # 城口县（重庆）
    "丰都": "101040100",  # 丰都县（重庆）
    "垫江": "101040100",  # 垫江县（重庆）
    "忠县": "101040100",  # 忠县（重庆）
    "云阳": "101040100",  # 云阳县（重庆）
    "奉节": "101040100",  # 奉节县（重庆）
    "酉阳": "101040100",  # 酉阳土家族苗族自治县（重庆）
    "彭水": "101040100",  # 彭水苗族土家族自治县（重庆）
    "石柱": "101040100",  # 石柱土家族自治县（重庆）
    "秀山": "101040100",  # 秀山土家族苗族自治县（重庆）
    "黔江": "101040100",  # 黔江区（重庆）
    "綦江": "101040100",  # 綦江区（重庆）
    "南川": "101040100",  # 南川区（重庆）
    "江津": "101040100",  # 江津区（重庆）
    "万州": "101040100",  # 万州区（重庆）
    "开州": "101040100",  # 开州区（重庆）
    "涪陵": "101040100",  # 涪陵区（重庆）
    "武隆": "101040100",  # 武隆区（重庆）
    "大足": "101040100",  # 大足区（重庆）
    "沙坪坝": "101040100",  # 沙坪坝区（重庆）
    "渝中": "101040100",  # 渝中区（重庆）
    "南岸": "101040100",  # 南岸区（重庆）
    "江北": "101040100",  # 江北区（重庆）
    "渝北": "101040100",  # 渝北区（重庆）
    
    # 省外
    "宜昌": "101200901",  # 湖北宜昌（长江三峡）
    
    # 浙江省
    "杭州": "101210101",
    "千岛湖": "101210101",  # 千岛湖在杭州
    
    # 福建省
    "厦门": "101230201",
    "鼓浪屿": "101230201",  # 鼓浪屿在厦门
    
    # 广东省
    "阳江": "101282001",
    
    # 贵州省
    "安顺": "101260301",
    
    # 山东省
    "青岛": "101120201",
    
    # 其他常用城市
    "成都": "101270101",
    "广州": "101280101",
    "深圳": "101280601",
    "南京": "101190101",
    "武汉": "101200101",
    "西安": "101110101",
    "长沙": "101250101",
    "郑州": "101180101",
    "沈阳": "101070101",
    "大连": "101070201",
    "哈尔滨": "101050101",
    "长春": "101060101",
    "济南": "101120101",
    "太原": "101100101",
    "石家庄": "101090101",
    "合肥": "101220101",
    "南昌": "101240101",
    "福州": "101230101",
    "南宁": "101300101",
    "昆明": "101290101",
    "贵阳": "101260101",
    "兰州": "101160101",
    "西宁": "101150101",
    "银川": "101170101",
    "乌鲁木齐": "101130101",
    "拉萨": "101140101",
    "海口": "101310101",
    "台北": "101340101",
    "香港": "101320101",
    "澳门": "101330101",
}

# ==================== 景点名称映射 ====================
POI_NAMES = {
10524162: "鼓浪屿",
82093: "磁器口古镇",
78160: "重庆动物园",
13228641: "重庆两江游",
89771: "816工程景区",
91483: "长江索道",
33834153: "重庆欢乐谷",
92173: "武隆喀斯特旅游区",
82315: "武隆天生三桥",
10558680: "解放碑步行街",
76355: "白帝城·瞿塘峡景区",
102734194: "重庆云端之眼观景台",
78137: "仙女山国家森林公园",
78129: "大足石刻",
82101: "重庆湖广会馆",
24654532: "长江三峡",
89625646: "三峡之巅景区",
129377915: "《重庆·1949》演出",
76356: "巫山小三峡",
83050: "乌江画廊",
133855594: "重庆大轰炸六五隧道惨案史实展馆",
82328: "三峡博物馆",
10559407: "龙水峡地缝",
80446: "渣滓洞",
78177: "人民大礼堂",
92169: "丰都鬼城名山景区",
10559506: "观音桥步行街",
78586000: "探索舱·云端乐园",
20365101: "武陵山大裂谷",
56570158: "李子坝轻轨站",
89785: "白鹤梁水下博物馆",
29904239: "蚩尤九黎城",
78161: "朝天门广场",
118732016: "两江小渡",
130846449: "重庆十八梯传统风貌区",
65183944: "重庆长江索道南站",
80447: "白公馆",
78143: "金佛山",
130898810: "巫峡·神女景区",
149543777: "重庆游船观光",
90499682: "李子坝单轨穿楼观景平台",
10758915: "山城步道",
69571118: "朝天门号两江夜景游轮",
65963918: "山城巷历史文化风貌区",
153202781: "重庆盖碗茶文化体验",
94859: "南滨路",
151074799: "重庆citywalk",
98180287: "重庆夜景游船",
82324: "南山一棵树观景台",
56805075: "十八梯",
78157: "酉阳桃花源景区",
33836754: "重庆玛雅海滩水公园",
91809: "万州大瀑布",
82086: "重庆乌江龚滩旅游度假区",
10765188: "乐和乐都动物主题乐园",
134055792: "重庆三峡游船",
119625503: "重庆光环购物公园室内植物园沐光森林",
78174: "南山风景区",
33177820: "WFC会仙楼观景台",
34303518: "二厂文创公园",
69349738: "重庆长江三峡游船",
78142: "黑山谷风景区",
31662389: "龙门浩老街",
78136: "芙蓉洞",
31678830: "下浩里",
22672541: "重庆欢乐海底世界",
82317: "地心探险极地",
76357: "瞿塘峡",
78163: "鹅岭公园",
10534468: "云阳龙缸国家地质公园",
149667375: "重庆滑雪",
128621409: "重庆建川海疆博物馆",
52528404: "重庆建川博物馆聚落",
48612772: "大圆祥博物馆",
10759121: "《印象武隆》实景演出",
76358: "巫峡",
10759202: "融汇温泉城",
52125766: "魁星楼",
15123941: "宝顶山景区",
78148: "金刀峡",
78187: "四面山",
13695434: "濯水古镇",
111709787: "濯水景区",
94890: "天福官驿",
112648519: "长江三峡-世纪系列游船",
15055043: "北山石刻",
149556838: "三峡龙脊",
10534508: "红池坝风景区",
76443: "小小三峡",
145362934: "重庆小渡",
69446838: "夜游两江",
136624774: "嘉陵小渡",
78147: "钓鱼城",
140610757: "乌江画廊（涪陵段）",
76363: "石宝寨",
61422141: "重庆都市观光巴士",
31672376: "千厮门大桥",
39073461: "乌江",
10548576: "阿依河景区",
152937372: "小红船",
133552494: "原气喜剧爆笑脱口秀(观音桥茂业天地店)",
148473894: "【重庆】世贸·天台131高空观景台",
78171: "罗汉寺",
31078384: "重庆汉海海洋公园",
78197: "重庆统景温泉风景区",
15036521: "统景风景区",
15051058: "濯水景区-蒲花暗河",
91763252: "重庆融创海世界",
135472926: "三峡之光",
10552942: "佛影峡漂流",
23073406: "梦幻奥陶纪景区",
13271168: "南天湖景区",
98373934: "重庆融创文旅城",
91769046: "重庆融创水世界",
91763232: "重庆融创渝乐小镇",
56809872: "天生三桥玻璃眺台",
15036359: "重庆园博园",
134056098: "龚滩古镇乌江画廊",
10759203: "海棠晓月圣地温泉",
76428: "夔门",
76364: "神女峰",
135990036: "白帝城",
145678772: "重庆动物园-熊猫馆",
112649521: "长江游轮",
78172: "老君洞",
82088: "边城洪安景区-洪安古镇",
70022346: "人民解放纪念碑",
139484116: "渝州故事·重庆非遗文化体验基地(十八梯解放碑店)",
15053191: "鸿恩寺公园",
24650650: "嘉陵江",
82316: "重庆野生动物世界",
136033242: "金色湖畔·HIFI影音汤泉生活",
144339047: "1941茶馆·戏院",
22865168: "皇冠大扶梯",
10794647: "美心红酒小镇",
100151: "神女溪景区",
56809777: "北仓文创街区",
10534550: "武陵山国家森林公园",
36374740: "长嘉汇弹子石老街",
90682566: "重庆两江游-金碧系列",
56809976: "天龙天坑",
56690165: "重庆国际博览中心",
144841269: "洪崖洞民俗风貌区-观景台",
69545083: "乌江赤壁观景台",
131914402: "金刚碑·温泉老村",
94884: "重庆科技馆",
82325: "重庆南山植物园",
10762780: "华生园金色蛋糕梦幻王国",
76360: "张飞庙",
58279006: "丰都雪玉洞景区",
10534457: "重庆海昌加勒比海水世界",
10521419: "重庆抗战遗址博物馆",
28549631: "大型山水实景演艺《烽烟三国》",
78168: "华岩寺",
152859682: "重庆宫宴 · 礼宴巴国",
56682104: "重庆国际马戏城",
152177538: "重庆 · 开心麻花喜剪吹沉浸剧场《疯狂理发店》",
69142902: "大足石刻博物馆",
148440051: "原气喜剧脱口秀剧场(观音桥阳光世纪店)",
69565751: "兰英大峡谷",
15129249: "白象街",
124155683: "仙女山树顶漫步",
56809904: "重庆武隆天生三桥风景区-天龙桥",
10534501: "歌乐山国家森林公园",
69145732: "重庆中央公园",
82331: "天赐温泉",
78135: "芙蓉江",
72917947: "叠石花谷",
67633257: "仙女山观光火车站",
56380475: "重庆欢乐谷-重庆之眼",
58257413: "《归来三峡》实景演艺",
94887: "重庆大剧院",
144556827: "重庆海洋世界",
78149: "缙云山",
61911458: "天眼洞花岭风景区",
94861: "重庆好吃街夜市",
89768237: "重庆两江游-朝天系列",
56806976: "夔州古城",
52078236: "长江三峡-大美华夏游轮",
38366644: "七星岗",
35165469: "中国黔江城市大峡谷",
56818167: "重庆海洋动物世界",
13695404: "磁器口古镇-宝轮寺",
143217998: "重庆城上天幕乐游观光塔",
82095: "万灵古镇",
82301908: "黄桷垭老街",
24032365: "重庆自然博物馆",
22865185: "武隆天生三桥风景区-青龙桥",
56807481: "七星岗",
23117209: "重庆十八梯传统风貌区",
91763231: "重庆融创渝乐小镇",
112649035: "重庆长江索道",
10787719: "山城步道",
56809420: "山城步道",
13445410: "万盛石林",
10553222: "大风堡景区",
78198: "重庆统景温泉风景区",
149822640: "仙女山国家森林公园",
78167: "华岩寺",
15057101: "濯水景区",
146015991: "重庆十八梯传统风貌区",
24653347: "南山一棵树观景台",
15138981: "梦幻奥陶纪景区",
13353645: "重庆欢乐谷",
146187566: "重庆融创文旅城",
136173932: "江北嘴江滩公园",
15138863: "万盛石林",
108172191: "重庆自然博物馆",
145695931: "重庆园博园",
56809977: "武隆天生三桥风景区-青龙桥",
133975946: "亢家寨风景区",
31658739: "重庆科技馆",
151620670: "安居古城",
30767040: "中山古镇",
13540650: "安居古城",
56381194: "重庆欢乐谷",
35812377: "酉阳红石林景区",
23994602: "山王坪喀斯特国家生态公园",
55940155: "川河盖",
69354635: "綦江古剑山风景区",
134071405: "万盛石林",
30412905: "重庆融创文旅城",
82323: "茶山竹海",
13662764: "中山古镇",
38371261: "重庆野生动物世界",
10758166: "重庆游船观光",
97822: "重庆两江游",
56809906: "武隆天生三桥风景区-天龙桥",
82305: "重庆野生动物世界",
78963626: "天下第一风雨廊桥",
152129424: "安居古城",
56683032: "万盛石林",
149937440: "重庆融创渝乐小镇",
78155: "黄水国家森林公园",
69100538: "百里竹海旅游度假区",
35159810: "万佛峡漂流",
69529850: "川河盖",
148923140: "綦江古剑山风景区",
15057062: "濯水景区",
15053344: "濯水景区",
30284076: "重庆野生动物世界",
143298869: "重庆融创文旅城",
136343877: "重庆融创文旅城",
82097: "中山古镇",
56809781: "重庆科技馆",
133853116: "重庆欢乐谷",
93673647: "万州风景区",
153456738: "重庆自然博物馆",
10559408: "龙水峡地缝",
78132: "潼南大佛寺景区",
82091: "中山古镇",
133528282: "山王坪喀斯特国家生态公园",
153182145: "重庆融创文旅城",
153444551: "安居古城",
58278998: "万州风景区",
91496248: "重庆融创海世界",
79438801: "重庆欢乐谷",
10787745: "山城步道",
15129259: "白象街",
82089: "中山古镇",
98280508: "濯水景区",
123858125: "重庆欢乐谷",
112649946: "重庆长江索道",
85466883: "重庆融创文旅城",
112646972: "重庆十八梯传统风貌区",
125612735: "重庆融创水世界",
15123872: "中山古镇",
83356124: "重庆自然博物馆",
145553961: "重庆园博园",
34492373: "重庆野生动物世界",
148417420: "重庆融创水世界",
15129269: "白象街",
148473969: "【重庆】世贸·天台131高空观景台",
64252311: "重庆野生动物世界",
20957734: "天赐华汤森林温泉(重庆璧山店)"
}

NAME_TO_ID = {v: k for k, v in POI_NAMES.items()}

# ==================== 景点→区县 映射 ====================
SPOT_TO_DISTRICT = {

    # === 渝中区 ===
    "解放碑步行街": "渝中",
    "洪崖洞": "渝中",
    "长江索道": "渝中",
    "重庆长江索道": "渝中",
    "重庆长江索道南站": "渝中",
    "朝天门广场": "渝中",
    "人民大礼堂": "渝中",
    "人民解放纪念碑": "渝中",
    "重庆湖广会馆": "渝中",
    "山城步道": "渝中",
    "山城巷历史文化风貌区": "渝中",
    "十八梯": "渝中",
    "重庆十八梯传统风貌区": "渝中",
    "白象街": "渝中",
    "魁星楼": "渝中",
    "罗汉寺": "渝中",
    "老君洞": "渝中",
    "七星岗": "渝中",
    "重庆大轰炸\"六五\"隧道惨案史实展馆": "渝中",
    "1941茶馆·戏院": "渝中",
    "渝州故事·重庆非遗文化体验基地(十八梯解放碑店)": "渝中",
    "皇冠大扶梯": "渝中",
    "李子坝轻轨站": "渝中",
    "李子坝单轨穿楼观景平台": "渝中",
    "千厮门大桥": "渝中",
    "洪崖洞民俗风貌区-观景台": "渝中",
    "WFC会仙楼观景台": "渝中",
    "重庆云端之眼观景台": "渝中",
    "探索舱·云端乐园": "渝中",
    "世贸·天台131高空观景台": "渝中",
    "重庆城上天幕乐游观光塔": "渝中",
    "两江小渡": "渝中",
    "重庆小渡": "渝中",
    "嘉陵小渡": "渝中",
    "小红船": "渝中",
    "重庆两江游": "渝中",
    "重庆两江游-朝天系列": "渝中",
    "重庆两江游-金碧系列": "渝中",
    "夜游两江": "渝中",
    "重庆夜景游船": "渝中",
    "长江三峡-世纪系列游船": "渝中",
    "重庆长江三峡游船": "渝中",
    "长江游轮": "渝中",
    "重庆游船观光": "渝中",
    "朝天门号两江夜景游轮": "渝中",
    "重庆三峡游船": "渝中",
    "重庆都市观光巴士": "渝中",
    "《重庆·1949》演出": "渝中",
    "原气喜剧爆笑脱口秀(观音桥茂业天地店)": "渝中",
    "原气喜剧脱口秀剧场(观音桥阳光世纪店)": "渝中",
    "开心麻花喜剪吹沉浸剧场《疯狂理发店》": "渝中",
    "重庆好吃街夜市": "渝中",
    "重庆盖碗茶文化体验": "渝中",
    "重庆citywalk": "渝中",
    
    # === 沙坪坝区 ===
    "磁器口古镇": "沙坪坝",
    "磁器口古镇-宝轮寺": "沙坪坝",
    "渣滓洞": "沙坪坝",
    "白公馆": "沙坪坝",
    "歌乐山国家森林公园": "沙坪坝",
    "融汇温泉城": "沙坪坝",
    "重庆1949大剧院": "沙坪坝",
    
    # === 南岸区 ===
    "南山一棵树观景台": "南岸",
    "南山一棵树": "南岸",
    "南山风景区": "南岸",
    "重庆南山植物园": "南岸",
    "南滨路": "南岸",
    "长嘉汇弹子石老街": "南岸",
    "龙门浩老街": "南岸",
    "下浩里": "南岸",
    "黄桷垭老街": "南岸",
    "海棠晓月圣地温泉": "南岸",
    "重庆抗战遗址博物馆": "南岸",
    "重庆游船观光": "南岸",
    
    # === 江北区 ===
    "观音桥步行街": "江北",
    "重庆大剧院": "江北",
    "重庆科技馆": "江北",
    "重庆欢乐谷": "渝北",  # 欢乐谷在渝北区
    "重庆欢乐谷-重庆之眼": "渝北",
    "重庆玛雅海滩水公园": "渝北",
    "重庆欢乐海底世界": "渝北",
    "重庆海洋世界": "渝北",
    "重庆融创文旅城": "沙坪坝",
    "重庆融创渝乐小镇": "沙坪坝",
    "重庆融创水世界": "沙坪坝",
    "重庆融创海世界": "沙坪坝",
    "重庆国际博览中心": "渝北",
    "重庆中央公园": "渝北",
    "重庆园博园": "渝北",
    "重庆光环购物公园室内植物园\"沐光森林\"": "渝北",
    "重庆野生动物世界": "永川",
    "乐和乐都动物主题乐园": "永川",
    "重庆汉海海洋公园": "巴南",
    "华生园金色蛋糕梦幻王国": "大渡口",
    "重庆工业博物馆": "大渡口",
    "重庆建川博物馆聚落": "九龙坡",
    "重庆建川海疆博物馆": "九龙坡",
    "重庆动物园": "九龙坡",
    "重庆动物园-熊猫馆": "九龙坡",
    "重庆自然博物馆": "北碚",
    "缙云山": "北碚",
    "金刚碑·温泉老村": "北碚",
    "重庆统景温泉风景区": "渝北",
    "统景风景区": "渝北",
    "天赐温泉": "九龙坡",
    "天赐华汤森林温泉(重庆璧山店)": "璧山",
    "金色湖畔·HIFI影音汤泉生活": "渝北",
    "海棠晓月圣地温泉": "南岸",
    "融汇温泉城": "沙坪坝",
    "江北嘴江滩公园": "江北",
    "鸿恩寺公园": "江北",
    "北仓文创街区": "江北",
    "二厂文创公园": "渝中",
    "鹅岭公园": "渝中",
    
    # === 武隆区 ===
    "武隆天生三桥": "武隆",
    "武隆喀斯特旅游区": "武隆",
    "仙女山国家森林公园": "武隆",
    "仙女山": "武隆",
    "龙水峡地缝": "武隆",
    "芙蓉洞": "武隆",
    "芙蓉江": "武隆",
    "天福官驿": "武隆",
    "天生三桥玻璃眺台": "武隆",
    "天龙天坑": "武隆",
    "重庆武隆天生三桥风景区-天龙桥": "武隆",
    "武隆天生三桥风景区-青龙桥": "武隆",
    "仙女山树顶漫步": "武隆",
    "仙女山观光火车站": "武隆",
    "《印象武隆》实景演出": "武隆",
    "地心探险极地": "武隆",
    
    # === 大足区 ===
    "大足石刻": "大足",
    "宝顶山景区": "大足",
    "北山石刻": "大足",
    "大足石刻博物馆": "大足",
    
    # === 涪陵区 ===
    "816工程景区": "涪陵",
    "武陵山大裂谷": "涪陵",
    "白鹤梁水下博物馆": "涪陵",
    "乌江画廊": "涪陵",
    "乌江画廊（涪陵段）": "涪陵",
    "美心红酒小镇": "涪陵",
    "武陵山国家森林公园": "涪陵",
    "大木花谷": "涪陵",
    
    # === 奉节县 ===
    "白帝城·瞿塘峡景区": "奉节",
    "白帝城": "奉节",
    "瞿塘峡": "奉节",
    "夔门": "奉节",
    "三峡之巅景区": "奉节",
    "夔州古城": "奉节",
    "《归来三峡》实景演艺": "奉节",
    
    # === 巫山县 ===
    "巫山小三峡": "巫山",
    "小小三峡": "巫山",
    "巫峡": "巫山",
    "巫峡·神女景区": "巫山",
    "神女峰": "巫山",
    "神女溪景区": "巫山",
    "三峡之光": "巫山",
    
    # === 丰都县 ===
    "丰都鬼城名山景区": "丰都",
    "丰都雪玉洞景区": "丰都",
    
    # === 酉阳县 ===
    "酉阳桃花源景区": "酉阳",
    "龚滩古镇乌江画廊": "酉阳",
    "重庆乌江龚滩旅游度假区": "酉阳",
    "叠石花谷": "酉阳",
    "乌江赤壁观景台": "酉阳",
    
    # === 云阳县 ===
    "云阳龙缸国家地质公园": "云阳",
    "张飞庙": "云阳",
    
    # === 黔江区 ===
    "濯水古镇": "黔江",
    "濯水景区": "黔江",
    "濯水景区-蒲花暗河": "黔江",
    "中国黔江城市大峡谷": "黔江",
    "天下第一风雨廊桥": "黔江",
    
    # === 彭水县 ===
    "蚩尤九黎城": "彭水",
    "阿依河景区": "彭水",
    "乌江画廊": "彭水",
    
    # === 綦江区 ===
    "綦江古剑山风景区": "綦江",
    "万盛石林": "綦江",
    "梦幻奥陶纪景区": "綦江",
    "黑山谷风景区": "綦江",
    "重庆万盛石林": "綦江",
    
    # === 南川区 ===
    "金佛山": "南川",
    "山王坪喀斯特国家生态公园": "南川",
    
    # === 江津区 ===
    "四面山": "江津",
    "中山古镇": "江津",
    
    # === 合川区 ===
    "钓鱼城": "合川",
    "涞滩古镇": "合川",
    
    # === 永川区 ===
    "重庆野生动物世界": "永川",
    "乐和乐都动物主题乐园": "永川",
    "茶山竹海": "永川",
    
    # === 璧山区 ===
    "天赐华汤森林温泉(重庆璧山店)": "璧山",
    
    # === 铜梁区 ===
    "安居古城": "铜梁",
    
    # === 潼南区 ===
    "潼南大佛寺景区": "潼南",
    
    # === 梁平区 ===
    "百里竹海旅游度假区": "梁平",
    
    # === 石柱县 ===
    "黄水国家森林公园": "石柱",
    "大风堡景区": "石柱",
    
    # === 巫溪县 ===
    "红池坝风景区": "巫溪",
    "兰英大峡谷": "巫溪",
    
    # === 城口县 ===
    "亢家寨风景区": "城口",
    
    # === 忠县 ===
    "石宝寨": "忠县",
    "大型山水实景演艺《烽烟三国》": "忠县",
    
    # === 秀山县 ===
    "边城洪安景区-洪安古镇": "秀山",
    "川河盖": "秀山",
    
    # === 万州区 ===
    "万州大瀑布": "万州",
    "万州风景区": "万州",
    "三峡移民纪念馆": "万州",
    
    # === 开州区 ===
    "汉丰湖": "开州",
    
    # === 垫江县 ===
    "恺之峰旅游区": "垫江",
    
    # === 省外景点 ===
    "鼓浪屿": "厦门",
    "千岛湖": "杭州",
    "阳西咸水矿温泉": "阳江",
    "云峰屯堡": "安顺",
    "李村步行街": "青岛",
    "长江三峡": "宜昌",

}

# ==================== 数据加载 ====================
def load_comments():
    comments = []
    filename = 'chongqing_comments_cleaned (2).csv'
    
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                score_str = row.get('score', '').strip()
                try:
                    score_value = float(score_str) if score_str else 0.0
                except (ValueError, TypeError):
                    score_value = 0.0
                
                useful_str = row.get('useful_count', '').strip()
                try:
                    useful_value = int(float(useful_str)) if useful_str else 0
                except (ValueError, TypeError):
                    useful_value = 0
                
                poi_str = row.get('poi_id', '').strip()
                try:
                    poi_value = int(float(poi_str)) if poi_str else 0
                except (ValueError, TypeError):
                    poi_value = 0
                
                comment = {
                    'poi_id': poi_value,
                    'content': row.get('content', ''),
                    'score': score_value,
                    'publish_time': row.get('publish_time', ''),
                    'ip_located': row.get('ip_located', ''),
                    'useful_count': useful_value
                }
                comments.append(comment)
        print(f"✅ 成功加载 {len(comments)} 条评论")
    except FileNotFoundError:
        print(f"⚠️ 文件 {filename} 未找到，将使用空数据")
    except Exception as e:
        print(f"⚠️ 加载数据出错: {e}")
    
    return comments

COMMENTS = load_comments()

def group_by_poi(comments):
    poi_dict = {}
    for c in comments:
        poi_id = c.get('poi_id')
        if poi_id not in poi_dict:
            poi_dict[poi_id] = []
        poi_dict[poi_id].append(c)
    return poi_dict

POI_GROUPS = group_by_poi(COMMENTS)

# ==================== 对话存储 ====================
conversations = {}

def get_conversation(session_id):
    if session_id not in conversations:
        conversations[session_id] = []
    return conversations[session_id]

def add_to_conversation(session_id, role, content):
    history = get_conversation(session_id)
    history.append({"role": role, "content": content})
    if len(history) > 20:
        conversations[session_id] = history[-20:]
    return conversations[session_id]

def clear_conversation(session_id):
    if session_id in conversations:
        conversations[session_id] = []

# ==================== 评论分析 ====================
def analyze_comments(comments):
    if not comments:
        return None
    
    total = len(comments)
    scores = []
    for c in comments:
        s = c.get('score', 0)
        if isinstance(s, (int, float)):
            scores.append(float(s))
        else:
            scores.append(0.0)
    
    if not scores:
        return None
    
    avg_score = sum(scores) / len(scores)
    
    all_text = ' '.join([str(c.get('content', '')) for c in comments])
    words = re.findall(r'[\u4e00-\u9fa5]{2,}', all_text)
    common_words = Counter(words).most_common(10)
    
    positive = len([s for s in scores if s >= 4])
    neutral = len([s for s in scores if s == 3])
    negative = len([s for s in scores if s <= 2])
    
    return {
        'total': total,
        'avg_score': round(avg_score, 2),
        'positive': positive,
        'positive_rate': round(positive / total * 100, 1) if total > 0 else 0,
        'negative_rate': round(negative / total * 100, 1) if total > 0 else 0,
        'common_words': common_words,
        'sample_comments': comments[:5]
    }

# ==================== 天气函数 ====================
def need_weather(question):
    keywords = ['天气', '气温', '温度', '下雨', '晴天', '多云', '适合去', '现在去', '今天去', '注意', '带什么', '穿什么', '冷不冷', '热不热', '刮风', '风力', '湿度']
    return any(kw in question for kw in keywords)

def get_weather(city_name):
    """使用你的和风天气 API 获取实时天气"""
    # 查找城市ID
    city_id = CITY_IDS.get(city_name)
    if not city_id:
        print(f"⚠️ 未找到城市 {city_name} 的 ID，尝试 wttr.in")
        return get_weather_wttr(city_name)
    
    url = f"{BASE_URL}/v7/weather/now?location={city_id}&key={API_KEY}"
    
    print(f"📌 请求天气: {city_name} (ID: {city_id})")
    print(f"📌 URL: {url}")
    
    try:
        resp = requests.get(url, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"📌 API返回码: {data.get('code')}")
            
            if data.get('code') == '200':
                now = data.get('now', {})
                return {
                    'success': True,
                    'city': city_name,
                    'temp': now.get('temp', 'N/A'),
                    'text': now.get('text', 'N/A'),
                    'wind': f"{now.get('windDir', '')} {now.get('windScale', '')}级",
                    'humidity': f"{now.get('humidity', 'N/A')}%",
                    'feels_like': now.get('feelsLike', now.get('temp', 'N/A'))
                }
            else:
                print(f"⚠️ API返回错误码: {data.get('code')}")
                print(f"   错误信息: {data}")
                return get_weather_wttr(city_name)
        else:
            print(f"⚠️ HTTP请求失败: {resp.status_code}")
            print(f"   返回内容: {resp.text[:200]}")
            return get_weather_wttr(city_name)
            
    except requests.exceptions.Timeout:
        print(f"⚠️ 天气请求超时: {city_name}")
        return get_weather_wttr(city_name)
    except Exception as e:
        print(f"⚠️ 天气请求异常: {e}")
        return get_weather_wttr(city_name)

def get_weather_wttr(city_name):
    """wttr.in 备用方案（当你的API失败时）"""
    encoded_city = urllib.parse.quote(city_name)
    # 缓存破坏参数，每5分钟刷新
    cache_buster = int(time.time() / 300) * 300
    url = f"https://wttr.in/{encoded_city}?format=%C|%t|%w|%h&lang=zh&_={cache_buster}"
    
    print(f"📌 尝试 wttr.in 备用: {city_name}")
    
    try:
        resp = requests.get(url, timeout=10, headers={
            'User-Agent': 'curl/7.68.0'
        })
        
        if resp.status_code == 200 and resp.text.strip():
            text = resp.text.strip()
            # 检查是否返回了有效数据
            if '<' in text and 'html' in text.lower():
                print("⚠️ wttr.in 返回 HTML，可能被限制")
                return None
            
            parts = text.split('|')
            if len(parts) >= 2:
                temp_str = parts[1].replace('+', '').replace('°C', '').strip()
                temp_match = re.search(r'(-?\d+)', temp_str)
                temp = temp_match.group(1) if temp_match else temp_str
                
                return {
                    'success': True,
                    'city': city_name,
                    'temp': temp,
                    'text': parts[0].strip() if len(parts) > 0 else 'N/A',
                    'wind': parts[2].strip() if len(parts) > 2 else 'N/A',
                    'humidity': parts[3].strip() if len(parts) > 3 else 'N/A',
                    'feels_like': temp
                }
    except Exception as e:
        print(f"⚠️ wttr.in 异常: {e}")
    
    print(f"❌ 所有天气服务均失败: {city_name}")
    return None

def get_weather_for_spot(poi_name):
    """根据景点名称获取天气"""
    # 先通过景点映射获取区县
    district = SPOT_TO_DISTRICT.get(poi_name)
    
    # 如果找不到映射，尝试从景点名称中提取区县
    if not district:
        for d in ['渝中', '大足', '武隆', '沙坪坝', '南岸', '涪陵', '万州', '黔江', 
                  '杭州', '厦门', '阳江', '安顺', '青岛', '北京', '上海', '广州', '深圳']:
            if d in poi_name:
                district = d
                break
    
    # 如果还是找不到，直接使用景点名称
    if not district:
        district = poi_name
    
    print(f"📌 查询天气: {poi_name} -> {district}")
    weather_data = get_weather(district)
    
    if weather_data and weather_data.get('success'):
        weather_data['spot'] = poi_name
        weather_data['district'] = district
    
    return weather_data

def format_weather(weather_data):
    """格式化天气信息"""
    if not weather_data or not weather_data.get('success'):
        return "⚠️ 当前无法获取天气信息，请稍后再试"
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    spot = weather_data.get('spot', '')
    district = weather_data.get('district', '')
    city = weather_data.get('city', '')
    
    # 构建位置名称
    location_parts = []
    if spot:
        location_parts.append(spot)
    if district and district != spot:
        location_parts.append(district)
    if city and city not in location_parts:
        location_parts.append(city)
    
    location = '、'.join(location_parts) if location_parts else '未知位置'
    
    temp = weather_data.get('temp', 'N/A')
    text = weather_data.get('text', 'N/A')
    humidity = weather_data.get('humidity', 'N/A')
    wind = weather_data.get('wind', 'N/A')
    feels_like = weather_data.get('feels_like', 'N/A')
    
    return f"""
【{location}实时天气】
📅 更新时间：{current_time}
🌡️ 温度：{temp}°C（体感 {feels_like}°C）
☁️ 天气：{text}
💨 风力：{wind}
💧 湿度：{humidity}
"""
format_weather
# ==================== 检测景点 ====================
def detect_poi(question):
    for name in NAME_TO_ID.keys():
        if name in question:
            return NAME_TO_ID[name], name
    return None, None
# ==================== 多智能体模块（新增，不影响原有功能）====================

def agent_data_analyst(poi_name, comments, question):
    """
    Agent 1: 数据分析专家
    职责：分析评论数据，提取关键信息
    """
    analysis = analyze_comments(comments)
    
    if not analysis or analysis['total'] == 0:
        return "暂无该景点的评论数据"
    
    # 提取正面和负面评论样本
    positive_comments = [c for c in comments if c.get('score', 0) >= 4][:2]
    negative_comments = [c for c in comments if c.get('score', 0) <= 2][:2]
    
    positive_text = '、'.join([c.get('content', '')[:30] for c in positive_comments]) if positive_comments else '无'
    negative_text = '、'.join([c.get('content', '')[:30] for c in negative_comments]) if negative_comments else '无'
    
    # 判断用户是否问到特定主题
    topics = []
    if '孩子' in question or '亲子' in question:
        kid_comments = [c for c in comments if '孩子' in c.get('content', '') or '亲子' in c.get('content', '')]
        if kid_comments:
            topics.append(f"亲子相关评论 {len(kid_comments)} 条")
    
    if '价格' in question or '门票' in question or '贵' in question:
        price_comments = [c for c in comments if '价格' in c.get('content', '') or '门票' in c.get('content', '') or '贵' in c.get('content', '')]
        if price_comments:
            topics.append(f"价格相关评论 {len(price_comments)} 条")
    
    topics_text = '、'.join(topics) if topics else '无特定主题'
    
    result = f"""📊 【数据分析专家报告】
景点：{poi_name}
评论总数：{analysis['total']}条
平均评分：{analysis['avg_score']}/5.0
好评率：{analysis['positive_rate']}%
差评率：{analysis['negative_rate']}%

高频词：{', '.join([w for w, _ in analysis['common_words']][:5])}

用户关注的方面：{topics_text}

正面评论示例：{positive_text}
负面评论示例：{negative_text}"""
    
    return result


def agent_weather_expert(poi_name):
    """
    Agent 2: 天气专家
    职责：获取天气并给出出行建议
    """
    weather_data = get_weather_for_spot(poi_name)
    
    if not weather_data or not weather_data.get('success'):
        return "🌤️ 【天气专家报告】天气服务暂时不可用"
    
    district = weather_data.get('district', '')
    temp = weather_data.get('temp', 'N/A')
    text = weather_data.get('text', 'N/A')
    wind = weather_data.get('wind', 'N/A')
    humidity = weather_data.get('humidity', 'N/A')
    feels_like = weather_data.get('feels_like', 'N/A')
    
    # 根据天气给出建议
    suggestions = []
    temp_num = int(temp) if temp != 'N/A' and temp.isdigit() else None
    if temp_num is not None:
        if temp_num >= 35:
            suggestions.append("🔥 高温天气，注意防暑防晒，建议上午或傍晚出行")
        elif temp_num >= 30:
            suggestions.append("☀️ 天气较热，建议携带遮阳伞和充足饮水")
        elif temp_num <= 10:
            suggestions.append("❄️ 气温较低，注意保暖，建议穿厚外套")
        elif temp_num <= 5:
            suggestions.append("🥶 天气寒冷，注意防寒防冻")
    
    if '雨' in text or '雪' in text:
        suggestions.append("🌂 有降水天气，建议携带雨具")
    
    if int(humidity) > 80 if humidity != 'N/A' and humidity.isdigit() else False:
        suggestions.append("💧 湿度较大，体感可能不适，注意除湿")
    
    suggestion_text = '、'.join(suggestions) if suggestions else '天气适宜出行'
    
    result = f"""🌤️ 【天气专家报告】
📍 {district}
🌡️ 温度：{temp}°C（体感 {feels_like}°C）
☁️ 天气：{text}
💨 风力：{wind}
💧 湿度：{humidity}%

💡 出行建议：{suggestion_text}"""
    
    return result


def agent_travel_consultant(poi_name, question, data_report, weather_report, has_comments=True):
    """
    Agent 3: 旅游顾问（主控Agent）
    职责：综合数据专家和天气专家的报告，给出最终回答
    """
    if has_comments:
        system_prompt = f"""你是一个经验丰富的旅游顾问，负责综合「数据分析专家」和「天气专家」的报告，回答用户的问题。

【你的风格】
- 热情、专业、亲切
- 回答要实用、接地气
- 像朋友一样给出真诚建议

【回答要求】
1. 先给出明确的结论（值不值得去）
2. 引用数据支撑（来自数据分析专家报告）
3. 引用评论中的具体例子
4. 结合天气给出出行建议（来自天气专家报告）
5. 结构清晰但不死板

不要生硬念报告，要像在和朋友聊天。"""
    else:
        system_prompt = f"""你是一个经验丰富的旅游顾问。用户询问的是「{poi_name}」，但目前没有该景点的游客评论数据。

请你根据自己的知识回答：
1. 该景点的基本情况
2. 你的建议（值不值得去、适合谁去）
3. 如果有天气信息，结合天气给出建议

语气要亲切、实用，像和朋友聊天一样。"""

    user_message = f"""用户问题：{question}

【数据分析专家报告】
{data_report}

【天气专家报告】
{weather_report}

请给出综合回答。"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    try:
        response = requests.post(
            "https://api.siliconflow.cn/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-ai/DeepSeek-V3",
                "messages": messages,
                "temperature": 0.85,
                "max_tokens": 1000
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"AI调用失败：{response.text}"
    except Exception as e:
        return f"请求异常：{str(e)}"


def multi_agent_ask(poi_name, comments, question, history=[]):
    """
    多智能体主入口
    三个Agent分工协作：
    1. 数据专家 → 分析评论
    2. 天气专家 → 获取天气
    3. 旅游顾问 → 综合回答
    """
    print(f"🚀 启动多智能体模式：{poi_name}")
    
    # Agent 1: 数据分析专家
    print("  📊 Agent 1: 数据分析专家 工作中...")
    has_comments = comments and len(comments) > 0
    if has_comments:
        data_report = agent_data_analyst(poi_name, comments, question)
    else:
        data_report = "暂无该景点的游客评论数据"
    
    # Agent 2: 天气专家
    print("  🌤️ Agent 2: 天气专家 工作中...")
    weather_report = agent_weather_expert(poi_name)
    
    # Agent 3: 旅游顾问（综合）
    print("  💬 Agent 3: 旅游顾问 综合中...")
    final_answer = agent_travel_consultant(poi_name, question, data_report, weather_report, has_comments)
    
    return final_answer
# ==================== AI问答 ====================
def ask_ai(poi_name, comments, question, history=[]):
    analysis = analyze_comments(comments)
    
    # ===== 天气 =====
    weather_info = ""
    if need_weather(question):
        weather_data = get_weather_for_spot(poi_name)
        if weather_data is None:
            weather_info = "⚠️ 天气服务暂时不可用，请稍后再试"
        elif weather_data.get('success'):
            weather_info = format_weather(weather_data)
        else:
            weather_info = "⚠️ 天气信息获取失败"
    
    # ===== 构建上下文 =====
    if analysis and analysis['total'] > 0:
        stats = f"""评论总数：{analysis['total']}条
平均评分：{analysis['avg_score']}/5.0
好评率：{analysis['positive_rate']}%
差评率：{analysis['negative_rate']}%

评论样本：
"""
        for i, c in enumerate(analysis['sample_comments'], 1):
            stats += f"{i}. {c.get('content', '')}（评分：{c.get('score', 0)}）\n"""
        
        context = f"景点名称：{poi_name}\n{stats}"
        
        system_prompt = """你是一个热情、专业的旅游助手，基于游客评论数据回答用户问题。

【你的风格】
- 语气亲切自然，像朋友聊天一样
- 回答要实用、接地气
- 可以适当使用表情符号

【回答结构（灵活运用）】
1. 先给出直观感受
2. 用数据支撑（引用评分和评论）
3. 引用1-2条真实评论
4. 给出具体建议（什么时候去、适合谁去）
5. 有天气信息时自然融入建议

不要生硬念数据，要像和朋友聊天一样回答。"""
        
    else:
        context = f"景点名称：{poi_name}（暂无游客评论数据）"
        system_prompt = f"""你是一个热情、专业的旅游助手。用户询问「{poi_name}」，但目前没有该景点的游客评论数据。

请你根据自己的知识回答，并说明：
1. 该景点的基本情况
2. 你的建议
3. 注意：回答基于通用知识，不是真实评论
4.如果提到了时间如“今天”、“这个月”，“现在”等，可以列出天气情况供用户参考
5.试着推荐以下与这个景点相关的景点
6.评论仅供参考，不需要依据评论一板一眼的回答

语气要亲切、实用，像和朋友聊天一样。"""
    
    # ===== 构建消息 =====
    messages = [{"role": "system", "content": system_prompt}]
    
    for h in history[-8:]:
        messages.append(h)
    
    user_msg = f"""用户问题：{question}

{context}

{weather_info}

请回答。"""
    messages.append({"role": "user", "content": user_msg})
    
    # ===== 调用 API =====
    try:
        response = requests.post(
            "https://api.siliconflow.cn/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-ai/DeepSeek-V3",
                "messages": messages,
                "temperature": 0.85,
                "max_tokens": 1000
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"AI调用失败：{response.text}"
    except Exception as e:
        return f"请求异常：{str(e)}"

def ask_general(question, history=[]):
    system_prompt = """你是一个热情、专业的旅游助手。

- 如果用户问题涉及旅游但未指定景点，给出一般性建议
- 如果完全无关，礼貌地引导用户回到旅游话题
- 语气亲切自然"""
    
    messages = [{"role": "system", "content": system_prompt}]
    for h in history[-6:]:
        messages.append(h)
    messages.append({"role": "user", "content": question})
    
    try:
        response = requests.post(
            "https://api.siliconflow.cn/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-ai/DeepSeek-V3",
                "messages": messages,
                "temperature": 0.85,
                "max_tokens": 600
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"AI调用失败：{response.text}"
    except Exception as e:
        return f"请求异常：{str(e)}"

# ==================== Flask 路由 ====================
@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get('question', '').strip()
    session_id = data.get('session_id', str(uuid.uuid4()))
    mode = data.get('mode', 'single')  

    if not question:
        return jsonify({'success': False, 'error': '请输入问题'})
    
    if question in ['清空', '重置', '重新开始', '新对话', 'clear']:
        clear_conversation(session_id)
        return jsonify({
            'success': True,
            'answer': '🔄 对话已重置，可以开始新的旅程了！',
            'session_id': session_id,
            'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    history = get_conversation(session_id)
    
    poi_id, poi_name = detect_poi(question)
    
    if not poi_id:
        answer = ask_general(question, history)
    else:
        comments = POI_GROUPS.get(poi_id, [])
        if mode == 'multi':
            print(f"🧠 多智能体模式：{poi_name}")
            answer = multi_agent_ask(poi_name, comments, question, history)
        else:
            print(f"🤖 单智能体模式：{poi_name}")
            answer = ask_ai(poi_name, comments, question, history)
    
    add_to_conversation(session_id, 'user', question)
    add_to_conversation(session_id, 'assistant', answer)
    
    return jsonify({
        'success': True,
        'answer': answer,
        'session_id': session_id,
        'history_count': len(get_conversation(session_id)),
        'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/health', methods=['GET'])
def health():
    # 测试天气服务状态
    weather_status = "unknown"
    try:
        test_weather = get_weather("重庆")
        if test_weather and test_weather.get('success'):
            weather_status = "api_ok"
        else:
            weather_status = "api_fail"
    except:
        weather_status = "api_error"
    
    return jsonify({
        'status': 'ok',
        'total_comments': len(COMMENTS),
        'active_sessions': len(conversations),
        'weather_service': weather_status,
        'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/')
def index():
    return jsonify({
        'message': '智能旅游助手 API 已启动（和风天气实时数据）',
        'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'endpoints': {
            '/api/ask': 'POST - 提问',
            '/api/health': 'GET - 健康检查'
        }
    })

# ==================== 启动 ====================
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
