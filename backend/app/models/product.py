from __future__ import annotations
from typing import Optional
"""
상품 관련 DB 모델
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    String, Float, Integer, Text, DateTime, Boolean,
    ForeignKey, Enum, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ProductStatus(str, PyEnum):
    SOURCED = "sourced"           # 소싱 완료, 마진 통과
    FILTERED = "filtered"         # 마진 미달 필터링
    PAGE_GENERATED = "page_generated"   # 상세페이지 생성 완료
    PENDING_REVIEW = "pending_review"   # 관리자 검수 대기
    REGISTERED = "registered"     # 쿠팡 등록 완료
    ON_SALE = "on_sale"           # 판매 중
    PRICE_ADJUST = "price_adjust" # 가격 조정 필요
    DELIST_CANDIDATE = "delist_candidate"  # 하차 후보
    DELISTED = "delisted"         # 하차 완료


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 도매처 정보
    source_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    source_name: Mapped[str] = mapped_column(String(50), default="ownerclan")
    name: Mapped[str] = mapped_column(String(500))
    brand: Mapped[Optional[str]] = mapped_column(String(200))
    manufacturer: Mapped[Optional[str]] = mapped_column(String(200))
    origin: Mapped[Optional[str]] = mapped_column(String(100))
    # 가격
    wholesale_price: Mapped[float] = mapped_column(Float)
    sale_price: Mapped[float] = mapped_column(Float, default=0.0)
    # 카테고리
    source_category_code: Mapped[Optional[str]] = mapped_column(String(100))
    coupang_category_id: Mapped[Optional[int]] = mapped_column(Integer)
    coupang_category_name: Mapped[Optional[str]] = mapped_column(String(200))
    # 이미지
    image_urls: Mapped[Optional[list]] = mapped_column(JSON)
    # 스펙/옵션
    specs: Mapped[Optional[dict]] = mapped_column(JSON)
    options: Mapped[Optional[dict]] = mapped_column(JSON)
    # 마진 계산 결과
    margin_rate: Mapped[Optional[float]] = mapped_column(Float)
    margin_amount: Mapped[Optional[float]] = mapped_column(Float)
    commission_rate: Mapped[Optional[float]] = mapped_column(Float)
    # 쿠팡 등록 정보
    coupang_product_id: Mapped[Optional[str]] = mapped_column(String(100))
    detail_page_html: Mapped[Optional[str]] = mapped_column(Text)
    # 상태
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus), default=ProductStatus.SOURCED
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relations
    price_histories: Mapped[list[PriceHistory]] = relationship(
        "PriceHistory", back_populates="product", cascade="all, delete-orphan"
    )
    performance: Mapped[ProductPerformance | None] = relationship(
        "ProductPerformance", back_populates="product", uselist=False
    )


class PriceHistory(Base):
    __tablename__ = "price_histories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    wholesale_price: Mapped[float] = mapped_column(Float)
    sale_price: Mapped[float] = mapped_column(Float)
    margin_rate: Mapped[float] = mapped_column(Float)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    change_reason: Mapped[Optional[str]] = mapped_column(String(300))

    product: Mapped[Product] = relationship("Product", back_populates="price_histories")


class ProductPerformance(Base):
    __tablename__ = "product_performances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), unique=True)
    total_sales_qty: Mapped[int] = mapped_column(Integer, default=0)
    total_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    total_net_profit: Mapped[float] = mapped_column(Float, default=0.0)
    return_qty: Mapped[int] = mapped_column(Integer, default=0)
    last_sale_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    product: Mapped[Product] = relationship("Product", back_populates="performance")
