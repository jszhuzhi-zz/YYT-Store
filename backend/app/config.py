# -*- coding: utf-8 -*-
"""配置驱动的指标体系与评分参数（对应 docs/14-健康度评分设计）。

生产环境中，这些应由 L1 平台后台按业态可配置（见 docs/13）；
此处用 Python 常量承载「零售」业态模板，作为骨架。
"""

# ---- 维度（六维），point=点位侧 / op=经营侧；weight=综合分权重 ----
DIMENSIONS = {
    "trade_area": {"name": "商圈机会", "side": "point", "weight": 0.18, "icon": "map-pin"},
    "carrier":    {"name": "载体质量", "side": "point", "weight": 0.17, "icon": "building"},
    "competition":{"name": "竞争压力", "side": "point", "weight": 0.15, "icon": "crosshair", "negative_display": True},
    "traffic":    {"name": "客流转化", "side": "op",    "weight": 0.20, "icon": "footprints"},
    "member":     {"name": "会员经营", "side": "op",    "weight": 0.15, "icon": "users"},
    "operation":  {"name": "经营达成", "side": "op",    "weight": 0.15, "icon": "wallet"},
}

# ---- 指标目录：key -> (名称, 维度, 方向(+1正/-1负), 折算法, 维度内权重) ----
# method: "pct"=相对分位法 / "attain"=目标达成法
INDICATORS = {
    "reach_pop":    ("可达客群规模", "trade_area", +1, "pct", 0.5),
    "spend_power":  ("客群消费力",   "trade_area", +1, "pct", 0.5),
    "mall_traffic": ("载体客流",     "carrier",    +1, "pct", 0.5),
    "location_q":   ("位置质量",     "carrier",    +1, "pct", 0.5),
    "comp_density": ("竞品密度",     "competition", -1, "pct", 0.6),
    "saturation":   ("同业态饱和度", "competition", -1, "pct", 0.4),
    "capture":      ("客流截流率",   "traffic",    +1, "pct", 0.5),
    "conv":         ("进店转化率",   "traffic",    +1, "pct", 0.5),
    "member_pen":   ("会员渗透率",   "member",     +1, "pct", 0.5),  # 点位vs经营 桥梁指标
    "repurchase":   ("复购率",       "member",     +1, "pct", 0.5),
    "sales_attain": ("销售达成",     "operation",  +1, "attain", 0.5),
    "ppsm":         ("坪效",         "operation",  +1, "pct", 0.5),
}

# ---- 折算锚点：分位(0-100) -> 得分 ----
PCT_ANCHORS = [(0, 10), (10, 30), (25, 45), (50, 60), (75, 75), (90, 88), (99, 98), (100, 100)]
# ---- 目标达成：达成率 -> 得分 ----
ATTAIN_ANCHORS = [(0.7, 30), (0.8, 40), (0.9, 55), (1.0, 70), (1.1, 85), (1.2, 95), (1.3, 98)]

# ---- 评级带 ----
GRADE_BANDS = [(85, "优"), (70, "良"), (55, "中"), (40, "偏弱"), (0, "差")]

# 点位/经营 2x2 阈值
QUADRANT_THRESHOLD = 58
