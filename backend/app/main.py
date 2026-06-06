# -*- coding: utf-8 -*-
"""FastAPI 应用：评分/查询 API + 托管原型前端。

运行：
    cd backend && python -m app.seed && uvicorn app.main:app --reload
文档：http://127.0.0.1:8000/docs   前端：http://127.0.0.1:8000/
"""
import os
import json
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .db import get_db, engine
from .models import Tenant, Store, MetricSeries, Base
from . import scoring

app = FastAPI(title="YYT-Store API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ---------- 工具 ----------
def _cohort(db: Session, store: Store):
    others = db.query(Store).filter(Store.tenant_id == store.tenant_id).all()
    return [s for s in others if s.cohort_key == store.cohort_key]


def _resolve(db: Session, sid):
    if sid == "current":
        s = db.query(Store).filter(Store.name.like("%万象城%")).first()
    else:
        s = db.query(Store).get(int(sid))
    if not s:
        raise HTTPException(404, "store not found")
    return s


def _score(db: Session, store: Store):
    return scoring.compute(store, _cohort(db, store))


# ---------- 基础 ----------
@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/tenant")
def tenant(db: Session = Depends(get_db)):
    t = db.query(Tenant).first()
    n = db.query(Store).filter(Store.tenant_id == t.id).count()
    return {"id": t.id, "name": t.name, "store_count": n}


# ---------- 门店列表 / 驾驶舱 ----------
@app.get("/api/stores")
def stores(db: Session = Depends(get_db)):
    out = []
    for s in db.query(Store).all():
        sc = _score(db, s)
        out.append({
            "id": s.id, "name": s.name, "city": s.city, "carrier": s.carrier_type,
            "composite": sc["composite"], "grade": sc["grade"],
            "quadrant": sc["quadrant"], "trend_delta": s.trend_delta,
            "member_penetration": sc["member_penetration"],
        })
    out.sort(key=lambda x: x["composite"])  # 需干预优先
    return out


@app.get("/api/dashboard/summary")
def summary(db: Session = Depends(get_db)):
    rows = stores(db)
    bands = {"差": 0, "偏弱": 0, "中": 0, "良": 0, "优": 0}
    quad = {"healthy": 0, "ops": 0, "ceiling": 0, "double": 0}
    for r in rows:
        bands[r["grade"]] += 1
        quad[r["quadrant"]["code"]] += 1
    avg = round(sum(r["composite"] for r in rows) / len(rows), 1)
    return {
        "store_count": len(rows), "avg_health": avg,
        "intervene": sum(1 for r in rows if r["composite"] < 55),
        "benchmark": sum(1 for r in rows if r["composite"] >= 85),
        "distribution": bands, "quadrant": quad,
    }


# ---------- 单店 ----------
@app.get("/api/stores/{sid}/workbench")
def workbench(sid: str, db: Session = Depends(get_db)):
    s = _resolve(db, sid); sc = _score(db, s)
    pen = sc["member_penetration"]
    q = sc["quadrant"]
    if q["code"] == "ops":
        verdict = "值得投入改善，不建议止损"; vc = "good"
    elif q["code"] == "double":
        verdict = "建议评估止损 / 调改退出"; vc = "bad"
    elif q["code"] == "ceiling":
        verdict = "点位天花板，理性看待预期"; vc = "mid"
    else:
        verdict = "健康门店，保持并复制经验"; vc = "good"
    diagnosis = (f"综合健康分 {sc['composite']}（{sc['grade']}）。"
                 f"点位潜力 {sc['point_potential']}、经营表现 {sc['operation_performance']}。")
    if q["code"] == "ops":
        diagnosis += f"点位是好的，问题在经营：会员渗透率仅 {pen}%，需提升转化与渗透。"
    # 待办：取经营侧最低的两维
    op_dims = sorted([d for d in sc["dimensions"] if d["side"] == "op"], key=lambda d: d["score"])
    todos = [{"name": d["name"], "icon": d["icon"], "score": d["score"]} for d in op_dims[:2]]
    return {
        "store": {"id": s.id, "name": s.name,
                  "meta": f"{s.carrier_type} · {s.biz_type} · {s.city}"},
        "composite": sc["composite"], "grade": sc["grade"], "trend_delta": s.trend_delta,
        "point_potential": sc["point_potential"], "operation_performance": sc["operation_performance"],
        "quadrant": q, "verdict": verdict, "verdict_color": vc, "diagnosis": diagnosis,
        "todos": todos,
    }


@app.get("/api/stores/{sid}/scorecard")
def scorecard(sid: str, db: Session = Depends(get_db)):
    s = _resolve(db, sid); sc = _score(db, s)
    return {
        "store": {"id": s.id, "name": s.name},
        "composite": sc["composite"], "grade": sc["grade"], "completeness": sc["completeness"],
        "point_potential": sc["point_potential"], "operation_performance": sc["operation_performance"],
        "quadrant": sc["quadrant"], "member_penetration": sc["member_penetration"],
        "dimensions": sc["dimensions"],
    }


@app.get("/api/stores/{sid}/metrics")
def metrics(sid: str, db: Session = Depends(get_db)):
    s = _resolve(db, sid)
    rows = db.query(MetricSeries).filter(MetricSeries.store_id == s.id).all()
    return [r.metric for r in rows]


@app.get("/api/stores/{sid}/query")
def query(sid: str, metric: str = "销售额", db: Session = Depends(get_db)):
    s = _resolve(db, sid)
    r = (db.query(MetricSeries)
         .filter(MetricSeries.store_id == s.id, MetricSeries.metric == metric).first())
    if not r:
        raise HTTPException(404, "metric not found")
    data = json.loads(r.payload)
    data["metric"] = metric
    return data


@app.get("/api/stores/{sid}/kpis")
def kpis(sid: str, db: Session = Depends(get_db)):
    """首页经营概览的关键指标（销售/客流/转化/客单价）。"""
    s = _resolve(db, sid)
    short = {"万元": "万", "万人次": "万", "%": "%", "元": "元"}
    rows = {r.metric: json.loads(r.payload)
            for r in db.query(MetricSeries).filter(MetricSeries.store_id == s.id).all()}
    out = []
    for m in ["销售额", "客流", "进店转化", "客单价"]:
        d = rows.get(m)
        if d:
            out.append({"name": m, "val": d["val"],
                        "unit": short.get(d["unit"], d["unit"]), "env": d["env"]})
    return out


# ---------- 托管原型前端 ----------
PROTO = os.path.join(os.path.dirname(__file__), "..", "..", "prototype")
if os.path.isdir(PROTO):
    app.mount("/ui", StaticFiles(directory=PROTO, html=True), name="ui")


@app.get("/")
def root():
    return RedirectResponse("/ui/index.html")


@app.get("/dashboard")
def dashboard():
    return RedirectResponse("/ui/dashboard.html")
