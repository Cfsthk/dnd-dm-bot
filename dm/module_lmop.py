"""Lost Mine of Phandelver - structured module data for DM context injection."""
from __future__ import annotations

LOCATIONS: dict[str, dict] = {
    "phandalin_outskirts": {
        "name": "法達林外圍小徑",
        "act": 1,
        "description": (
            "冒險者們正沿著高速公路前往法達林小鎮，護送一輛貨物車。"
            "四周是茂密的森林，空氣中彌漫著松樹的氣味。"
            "前方的路上出現了異樣——兩匹馬的屍體橫陳路中。"
        ),
        "npcs": ["西爾達·哈爾維斯（Sildar Hallwinter）—法師公會代表，被俽"],
        "encounters": ["地精伏擊（4隻地精，躲在灌木叢中）"],
        "secrets": ["地精來自Cragmaw部落", "格雷什已被擄走帶往Cragmaw洞穴"],
        "exits": ["cragmaw_hideout", "phandalin_town"],
    },
    "cragmaw_hideout": {
        "name": "蟹爪洞穴",
        "act": 1,
        "description": (
            "一個隱藏在山丘中的地精巢穴，洞口被灌木叢遮蔽。"
            "裡面有多個房間，住著地精、豺狼人和首領Klarg。"
            "地下河流從洞穴中流過，提供天然逃跑路線。"
        ),
        "npcs": ["克拉格（Klarg）—地精首領，兇殘但貧婪", "西爾達（被囚禁）"],
        "encounters": [
            "入口守衛（2隻地精）",
            "豺狼人營地（3隻豺狼人 + 2匹狼）",
            "克拉格的房間（克拉格 + 2隻地精）",
        ],
        "secrets": ["西爾達被囚禁於此", "箱子裡藏著給Black Spider的信件"],
        "exits": ["phandalin_town"],
        "loot": ["100GP賠償金", "地精首領寶箱（50GP珠寶）"],
    },
    "phandalin_town": {
        "name": "法達林小鎮",
        "act": 1,
        "description": (
            "法達林是一個約100人的邊境小鎮。"
            "近年受紅幫傭兵（Redbrand Ruffians）欺壓，居民人心惶惶。"
            "主要地點：翻倒馬車客棧、普拉特福特商店、小鎮廣場、鐘聲教堂。"
        ),
        "npcs": [
            "托菲爾（Toblen Stonehill）—客棧老闆，友善",
            "哈利亞·桑頓（Halia Thornton）—礦工交易所老闆，有秘密議程",
            "達蘭·埃爾德曼（Daran Edermath）—退休冒險者",
            "西西菉亞（Sister Garaele）—女祭司",
            "哈爾維斯特（Harbin Wester）—小鎮長官，懦弱",
        ],
        "encounters": ["紅幫傭兵巡邏（3-4人）", "紅幫城堡（Tresendar Manor）清剰"],
        "quests": [
            "替哈利亞消滅紅幫首領格拉斯塔（Glasstaff）",
            "替西西菉亞尋找Agatha女巫的回答",
            "替達蘭調查地圖岩石的死靈法師活動",
        ],
        "secrets": ["格拉斯塔是法師，與Black Spider有聯繫", "紅幫城堡下有地牢和古老地道"],
        "exits": ["tresendar_manor", "cragmaw_castle", "wave_echo_cave"],
    },
    "tresendar_manor": {
        "name": "崔森達莊園（紅幫城堡）",
        "act": 2,
        "description": (
            "廢棄莊園，地下室被紅幫傭兵佔據。"
            "地下室包括牢房、訓練室、酒窯和奇異洞穴。"
            "洞穴中住著獨眼怪（Nothic），在廢墟下徘迴。"
        ),
        "npcs": [
            "格拉斯塔（Glasstaff/Iarno Albrek）—紅幫法師首領，懦弱叛徒",
            "獨眼怪（Nothic）—被腐化的生物，可以交流，喜歡秘密",
        ],
        "encounters": [
            "入口守衛（2名紅幫）",
            "訓練室（3名紅幫）",
            "牢房（2名紅幫 + 囚犯）",
            "獨眼怪洞穴",
            "格拉斯塔辦公室（格拉斯塔 + 2名紅幫）",
        ],
        "secrets": [
            "格拉斯塔的信件揭露Black Spider計劃",
            "囚犯是Tharden Rockseeker（格雷什的兄弟）",
            "獨眼怪知道格拉斯塔秘密，可用肉食賄賢",
        ],
        "exits": ["phandalin_town", "wave_echo_cave"],
    },
    "cragmaw_castle": {
        "name": "蟹爪城堡",
        "act": 2,
        "description": (
            "殘破城堡，被地精和豺狼人佔據。"
            "城堡首領是豺狼人King Grol，俽處了格雷什。"
        ),
        "npcs": [
            "King Grol—豺狼人首領，效忠Black Spider",
            "格雷什·洛克斯克（Gundren Rockseeker）—被俽矮人，持有Wave Echo Cave地圖",
        ],
        "encounters": [
            "城堡入口（2隻地精）",
            "庭院（4隻地精 + 2隻豺狼人）",
            "國王大廳（King Grol + 豺狼人護衛 + 狼）",
        ],
        "secrets": ["格雷什持有Wave Echo Cave地圖", "Black Spider正等待地圖"],
        "exits": ["wave_echo_cave", "phandalin_town"],
    },
    "wave_echo_cave": {
        "name": "迴浪洞穴（魔法礦坑）",
        "act": 3,
        "description": (
            "傳說中的魔法礦坑，數百年前被地精大軍攻陷，礦工和法師全部罹難。"
            "洞穴中迴蘭著神秘波浪聲響，充滿未死亡生物和魔法能量。"
            "藏著「鑄造魔法的熔爐」（Forge of Spells），能為武器附魔。"
        ),
        "npcs": [
            "Nezznar（Black Spider）—黑暗精靈法師，最終Boss",
            "Nundro Rockseeker—被囚禁的矮人，格雷什的兄弟",
            "波波克（Mormesk the Wraith）—被束縛的怨靈，知道礦坑歷史",
        ],
        "encounters": [
            "洞穴入口（骷髏守衛 × 3）",
            "礦工宿舍（僵屍 × 4）",
            "地精營地（地精 × 4 + 蜘蛛 × 2）",
            "魔法熔爐房間（Flameskull + 僵屍 × 2）",
            "最終決戰（Nezznar + 蜘蛛護衛 × 4）",
        ],
        "secrets": [
            "魔法熔爐仍有效，能製造+1武器",
            "波波克知道礦坑歷史，可被說服協助",
            "Nundro還活著，被關在礦坑深處",
        ],
        "exits": ["phandalin_town"],
        "rewards": ["Forge of Spells控制權", "+1武器", "大量金幣和珠寶"],
    },
}

ACT_STRUCTURE = {
    1: {
        "title": "第一幕：地精伏擊與法達林小鎮",
        "locations": ["phandalin_outskirts", "cragmaw_hideout", "phandalin_town"],
        "main_goal": "護送貨物，解救西爾達，抵達法達林",
        "twist": "發現格雷什被擄走，紅幫傭兵控制小鎮",
        "duration_estimate": "1.5-2小時",
    },
    2: {
        "title": "第二幕：紅幫與蟹爪城堡",
        "locations": ["tresendar_manor", "cragmaw_castle", "phandalin_town"],
        "main_goal": "清剰紅幫，解救格雷什，找到Wave Echo Cave",
        "twist": "格拉斯塔逃跑並警告Black Spider，時間有限",
        "duration_estimate": "2-2.5小時",
    },
    3: {
        "title": "第三幕：迴浪洞穴與最終決戰",
        "locations": ["wave_echo_cave"],
        "main_goal": "進入迴浪洞穴，擊敗Black Spider，奪回魔法熔爐",
        "twist": "魔法熔爐已被啟動，產生意想不到的後果",
        "duration_estimate": "1.5-2小時",
    },
}


def get_location_context(location_key: str, act: int) -> str:
    loc = LOCATIONS.get(location_key)
    if not loc:
        return f"（未知地點：{location_key}）"
    act_info = ACT_STRUCTURE.get(act, {})
    npcs_text = "\n  - ".join(loc.get("npcs", []))
    encounters_text = "\n  - ".join(loc.get("encounters", []))
    secrets_text = "\n  - ".join(loc.get("secrets", []))
    return (
        f"地點：{loc['name']}\n"
        f"描述：{loc['description']}\n"
        f"當前幕目標：{act_info.get('main_goal', '繼續冒險')}\n"
        f"NPC：\n  - {npcs_text}\n"
        f"可能遭遇：\n  - {encounters_text}\n"
        f"隱藏秘密（DM專用）：\n  - {secrets_text}\n"
        f"幕轉折提示：{act_info.get('twist', '')}"
    )


def get_act_intro(act: int) -> str:
    act_info = ACT_STRUCTURE.get(act, {})
    return (
        f"【{act_info.get('title', f'第{act}幕')}】\n"
        f"目標：{act_info.get('main_goal', '')}\n"
        f"預計時長：{act_info.get('duration_estimate', '')}"
    )