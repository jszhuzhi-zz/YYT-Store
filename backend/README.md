# YYT-Store 后端骨架（可运行）

FastAPI 实现的**最小可运行骨架**：把 [健康度评分引擎](../docs/14-健康度评分设计.md) 真正用代码跑在
[多租户数据模型](../docs/13-SaaS多租户与平台管理后台.md) + mock 数据上，输出 API，并托管前端原型。

> 当前为骨架/Demo：数据是 mock，认证/权限中间件、真实数据接入、行业大脑对接等为后续。

## 技术栈
- **FastAPI**（API + 自动文档）· **SQLAlchemy**（ORM）· **SQLite**（开发，生产换 PostgreSQL+PostGIS）
- 生产追加：Anthropic SDK（AI/RAG）、角色-权限-数据范围中间件、Docker 部署

## 运行
```bash
cd backend
pip install -r requirements.txt
python -m app.seed            # 初始化并灌入 mock 数据（示例服饰集团·6 店）
uvicorn app.main:app --reload # 启动
```
- 前端原型（实时数据）：http://127.0.0.1:8000/  ·  驾驶舱：http://127.0.0.1:8000/dashboard
- API 文档（Swagger）：http://127.0.0.1:8000/docs

> 前端原型 `prototype/*.html` 通过 HTTP 打开时自动调用后端实时计算；用 `file://` 直接打开则回退到内置示例数据。

## 目录
```
backend/app/
  config.py    指标体系/维度/权重/折算锚点/评级带（配置驱动，对应业态模板）
  scoring.py   评分引擎：分位/达成折算 → 维度 → 综合 → 点位vs经营象限
  models.py    多租户模型：Tenant/Org/Store/IndicatorValue/MetricSeries
  seed.py      mock 数据
  main.py      API + 托管前端
```

## 主要 API
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/tenant` | 租户信息 |
| GET | `/api/stores` | 门店列表（含实时评分，需干预优先） |
| GET | `/api/dashboard/summary` | 驾驶舱 KPI / 分布 / 象限统计 |
| GET | `/api/stores/{id}/workbench` | 工作台：综合分 / 点位vs经营 / AI 诊断 / 待办 |
| GET | `/api/stores/{id}/scorecard` | 六维评分 / 雷达 / 渗透率 / 完整度 |
| GET | `/api/stores/{id}/query?metric=` | 数据查询：值/同环比/趋势/维度下钻 |

`{id}` 可用 `current`（解析为示例「万象城店」）。

## 评分引擎要点（docs/14）
- **相对分位法**：对标组内分位 → 锚点映射（中位=60、前10%≈88、后10%≈30）
- **目标达成法**：达成率 → 得分（用于销售达成）
- **负向指标**（竞争密度等）取反；竞争维度对外展示为「压力」
- **综合分**：维度加权，可得维度归一化并给出**数据完整度**
- **点位 vs 经营**：六维折叠为两轴 → 2×2 象限；桥梁指标=会员渗透率
