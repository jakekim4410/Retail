"""
카테고리 매핑 DB 모델
도매처 카테고리 코드 ↔ 쿠팡 카테고리 코드
"""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class CategoryMapping(Base):
    __tablename__ = "category_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_name: Mapped[str] = mapped_column(String(50))           # "ownerclan"
    source_category_code: Mapped[str] = mapped_column(String(100), index=True)
    source_category_name: Mapped[str] = mapped_column(String(300))
    coupang_category_id: Mapped[int] = mapped_column(Integer)
    coupang_category_name: Mapped[str] = mapped_column(String(300))
    commission_rate: Mapped[float] = mapped_column(Float, default=0.07)  # 기본 7%
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class ProductNoticeTemplate(Base):
    """카테고리별 상품정보제공고시 템플릿"""
    __tablename__ = "product_notice_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    coupang_category_id: Mapped[int] = mapped_column(Integer, index=True)
    category_name: Mapped[str] = mapped_column(String(300))
    notice_template: Mapped[str] = mapped_column(Text)  # JSON 직렬화 문자열
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
