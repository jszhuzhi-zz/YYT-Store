# -*- coding: utf-8 -*-
"""健康度评分引擎（docs/14 的代码实现）。

流程：原始指标 --对标组分位/达成--> 指标好分(越高越好)
     --维度内加权--> 维度分 --综合权重--> 综合健康分
     --点位/经营两轴--> 点位vs经营象限。
"""
from collections import defaultdict
from .config import (DIMENSIONS, INDICATORS, PCT_ANCHORS, ATTAIN_ANCHORS,
                     GRADE_BANDS, QUADRANT_THRESHOLD)


def _interp(anchors, x):
    """分段线性插值。"""
    if x <= anchors[0][0]:
        return anchors[0][1]
    if x >= anchors[-1][0]:
        return anchors[-1][1]
    for (x0, y0), (x1, y1) in zip(anchors, anchors[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return anchors[-1][1]


def pct_to_score(p):
    return max(10.0, min(100.0, _interp(PCT_ANCHORS, p)))


def attain_to_score(r):
    return max(10.0, min(100.0, _interp(ATTAIN_ANCHORS, r)))


def _percentile(values, x):
    """x 在 values 中的百分位(0-100)，含并列折半。"""
    n = len(values)
    if n == 0:
        return 50.0
    below = sum(1 for v in values if v < x)
    equal = sum(1 for v in values if v == x)
    return (below + 0.5 * equal) / n * 100.0


def grade_of(score):
    for thr, label in GRADE_BANDS:
        if score >= thr:
            return label
    return "差"


def indicator_good_score(key, raw, cohort_raws):
    """返回该指标的「好分」(越高越好)。"""
    name, dim, direction, method, _w = INDICATORS[key]
    if method == "attain":
        return attain_to_score(raw)
    p = _percentile(cohort_raws, raw)
    if direction < 0:        # 负向指标：值越高越差 -> 取反分位
        p = 100 - p
    return pct_to_score(p)


def compute(store, cohort_stores):
    """计算单店全套评分。

    store / cohort_stores：含 .indicators 的 ORM 对象（store 也应在 cohort 内）。
    """
    # 组装对标组每个指标的原始值分布
    cohort_vals = defaultdict(list)
    for s in cohort_stores:
        for iv in s.indicators:
            cohort_vals[iv.key].append(iv.raw)
    my = {iv.key: iv.raw for iv in store.indicators}

    # 1) 指标好分
    ind_scores = {}
    for key in INDICATORS:
        if key in my:
            ind_scores[key] = round(indicator_good_score(key, my[key], cohort_vals[key]), 1)

    # 2) 维度好分（维度内加权）
    dim_good = {}
    for dim in DIMENSIONS:
        items = [(k, w) for k, (_n, d, _dir, _m, w) in INDICATORS.items()
                 if d == dim and k in ind_scores]
        if not items:
            continue
        tw = sum(w for _k, w in items)
        dim_good[dim] = round(sum(ind_scores[k] * w for k, w in items) / tw, 1)

    # 3) 综合分（按维度综合权重，可得维度归一化 -> 数据完整度）
    avail_w = sum(DIMENSIONS[d]["weight"] for d in dim_good)
    composite = round(sum(dim_good[d] * DIMENSIONS[d]["weight"] for d in dim_good) / avail_w, 1)
    completeness = round(avail_w / sum(x["weight"] for x in DIMENSIONS.values()) * 100)

    # 4) 点位/经营两轴
    def axis(side):
        items = [(d, DIMENSIONS[d]["weight"]) for d in dim_good if DIMENSIONS[d]["side"] == side]
        tw = sum(w for _d, w in items)
        return round(sum(dim_good[d] * w for d, w in items) / tw, 1) if tw else 0.0

    point, op = axis("point"), axis("op")
    quadrant = _quadrant(point, op)

    # 维度对外展示（竞争维度展示为「压力」= 100-好分）
    dim_display = []
    for d, g in dim_good.items():
        meta = DIMENSIONS[d]
        shown = round(100 - g, 1) if meta.get("negative_display") else g
        dim_display.append({"key": d, "name": meta["name"], "icon": meta["icon"],
                            "side": meta["side"], "score": shown, "good": g,
                            "negative": bool(meta.get("negative_display"))})

    return {
        "composite": composite, "grade": grade_of(composite), "completeness": completeness,
        "point_potential": point, "operation_performance": op, "quadrant": quadrant,
        "dimensions": dim_display, "indicators": ind_scores,
        "member_penetration": my.get("member_pen"),
    }


def _quadrant(point, op):
    t = QUADRANT_THRESHOLD
    if point >= t and op >= t:
        return {"code": "healthy", "label": "健康", "advice": "维持·可借鉴"}
    if point >= t and op < t:
        return {"code": "ops", "label": "经营问题", "advice": "重点赋能·提转化（值得投入）"}
    if point < t and op >= t:
        return {"code": "ceiling", "label": "点位天花板", "advice": "已到位·控成本/理性预期"}
    return {"code": "double", "label": "双重问题", "advice": "评估止损/调改退出"}
