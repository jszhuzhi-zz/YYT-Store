# -*- coding: utf-8 -*-
"""Mock 数据：示例服饰集团 + 6 家门店（构成一个对标组）+ 指标时序。"""
import json
from .db import Base, engine, SessionLocal
from .models import Tenant, Org, Store, IndicatorValue, MetricSeries

# 指标顺序：reach_pop, spend_power, mall_traffic, location_q, comp_density,
#           saturation, capture, conv, member_pen, repurchase, sales_attain, ppsm
IND_KEYS = ["reach_pop", "spend_power", "mall_traffic", "location_q", "comp_density",
            "saturation", "capture", "conv", "member_pen", "repurchase", "sales_attain", "ppsm"]

STORES = [
    # name, city, 趋势Δ, [12 指标原始值]
    ("徐家汇店",   "上海", -6, [30, 40, 35, 30, 90, 85, 25, 22, 18, 28, 0.78, 30]),
    ("万象城店",   "杭州", -3, [78, 82, 72, 55, 80, 70, 38, 30, 28, 40, 0.92, 42]),
    ("大悦城店",   "北京",  1, [75, 70, 68, 60, 65, 60, 45, 38, 34, 45, 0.95, 48]),
    ("万达广场店", "成都",  0, [40, 45, 50, 48, 40, 45, 70, 65, 61, 62, 1.05, 66]),
    ("天环店",     "广州",  4, [68, 72, 75, 70, 45, 50, 72, 68, 58, 64, 1.08, 70]),
    ("IFS旗舰店",  "深圳",  3, [88, 90, 85, 82, 50, 55, 80, 78, 66, 72, 1.15, 85]),
]

# 数据查询用的指标时序（沿用移动端原型口径，仅 万象城店）
METRICS = {
    "销售额": {"unit": "万元", "val": "86.5", "env": -4, "yoy": -8, "color": "var(--bad)",
             "trend": [92, 95, 90, 88, 86, 84, 86.5],
             "insight": "环比 -4%，主因客流下滑；客单价回升部分对冲。建议优先抓进店转化。",
             "dims": {"按时段": [["午市", 38], ["晚市", 32], ["上午", 18], ["下午", 12]],
                      "按品类": [["女装", 54], ["男装", 28], ["配饰", 18]]}},
    "客流": {"unit": "万人次", "val": "1.24", "env": -8, "yoy": -12, "color": "var(--bad)",
            "trend": [1.5, 1.45, 1.38, 1.32, 1.28, 1.22, 1.24],
            "insight": "跑输商圈大盘 3 个点，同场新增竞品分流明显。",
            "dims": {"按时段": [["午市", 40], ["晚市", 30], ["上午", 16], ["下午", 14]],
                     "按来源": [["商场自然", 62], ["会员到店", 24], ["营销引流", 14]]}},
    "进店转化": {"unit": "%", "val": "18.6", "env": -1, "yoy": -2, "color": "var(--mid)",
              "trend": [20, 19.5, 19, 18.8, 18.4, 18.2, 18.6],
              "insight": "低于同场服饰店均值(24%)，是当前最大短板，优化空间最高。",
              "dims": {"按时段": [["晚市", 22], ["午市", 19], ["上午", 15], ["下午", 14]]}},
    "客单价": {"unit": "元", "val": "412", "env": 6, "yoy": 3, "color": "var(--good)",
            "trend": [388, 392, 400, 405, 402, 408, 412],
            "insight": "连带率提升带动，表现优于同类店，可继续强化连带销售。",
            "dims": {"按品类": [["女装", 56], ["男装", 26], ["配饰", 18]],
                     "会员/非会员": [["会员", 520], ["非会员", 360]]}},
    "会员复购": {"unit": "%", "val": "33.2", "env": -2, "yoy": -1, "color": "var(--mid)",
              "trend": [36, 35, 34.5, 34, 33.5, 33, 33.2],
              "insight": "沉睡会员增加，建议启动召回（见「增长」）。",
              "dims": {"会员分层": [["高价值", 58], ["活跃", 40], ["沉睡", 22]]}},
}


def run():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    t = Tenant(name="示例服饰集团")
    db.add(t); db.flush()
    region = Org(tenant_id=t.id, name="华东大区", type="region")
    db.add(region); db.flush()

    first_id = None
    for name, city, delta, vals in STORES:
        s = Store(tenant_id=t.id, org_id=region.id, name=f"示例服饰·{name}",
                  city=city, city_tier="一线", carrier_type="购物中心",
                  biz_type="零售-服饰", area=320, trend_delta=delta)
        db.add(s); db.flush()
        if name == "万象城店":
            first_id = s.id
        for k, v in zip(IND_KEYS, vals):
            db.add(IndicatorValue(tenant_id=t.id, store_id=s.id, key=k, raw=float(v)))
        if name == "万象城店":
            for m, payload in METRICS.items():
                db.add(MetricSeries(tenant_id=t.id, store_id=s.id, metric=m,
                                    payload=json.dumps(payload, ensure_ascii=False)))
    db.commit()
    print(f"seeded tenant={t.id} stores={len(STORES)} current_store(万象城)={first_id}")
    db.close()


if __name__ == "__main__":
    run()
