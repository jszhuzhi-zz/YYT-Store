# -*- coding: utf-8 -*-
"""多租户数据模型骨架（对应 docs/13）。所有业务表均带 tenant_id。"""
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base


class Tenant(Base):
    __tablename__ = "tenant"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class Org(Base):
    """组织树：集团 -> 区域 -> 加盟商 -> 门店（门店单列 Store）。"""
    __tablename__ = "org"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), index=True)
    parent_id = Column(Integer, ForeignKey("org.id"), nullable=True)
    name = Column(String)
    type = Column(String)  # region / franchisee


class Store(Base):
    __tablename__ = "store"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), index=True)
    org_id = Column(Integer, ForeignKey("org.id"), nullable=True)
    name = Column(String)
    city = Column(String)
    city_tier = Column(String)      # 一线 / 新一线 ...
    carrier_type = Column(String)   # 购物中心 / 街铺
    biz_type = Column(String)       # 零售-服饰 ...
    area = Column(Float)
    lat = Column(Float)
    lng = Column(Float)
    trend_delta = Column(Integer, default=0)  # 健康分较上月变化（mock）
    indicators = relationship("IndicatorValue", backref="store", cascade="all,delete")

    @property
    def cohort_key(self):
        return f"{self.biz_type}|{self.city_tier}|{self.carrier_type}"


class IndicatorValue(Base):
    """门店原始指标值（生产由数据接入层写入；此处 seed mock）。"""
    __tablename__ = "indicator_value"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), index=True)
    store_id = Column(Integer, ForeignKey("store.id"), index=True)
    key = Column(String, index=True)
    raw = Column(Float)


class MetricSeries(Base):
    """数据查询用的指标时序与维度下钻（mock，payload 为 JSON 文本）。"""
    __tablename__ = "metric_series"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), index=True)
    store_id = Column(Integer, ForeignKey("store.id"), index=True)
    metric = Column(String, index=True)
    payload = Column(Text)
