"""
주문·판매 관련 DB 모델
"""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum as PyEnum
from app.database import Base


class OrderStatus(str, PyEnum):
    ORDERED = "ordered"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    RETURNED = "returned"
    CANCELED = "canceled"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    coupang_order_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    coupang_product_id: Mapped[str | None] = mapped_column(String(100))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    sale_price: Mapped[float] = mapped_column(Float)          # 판매가
    settlement_amount: Mapped[float] = mapped_column(Float, default=0.0)   # 실제 정산액
    commission_amount: Mapped[float] = mapped_column(Float, default=0.0)   # 수수료
    net_profit: Mapped[float] = mapped_column(Float, default=0.0)         # 순이익
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.ORDERED
    )
    ordered_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
