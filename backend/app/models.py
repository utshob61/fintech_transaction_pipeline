"""
models.py
---------
SQLAlchemy ORM models mirroring database/schema.sql.

These are mainly used for read queries via the ORM where convenient;
the ETL load step uses raw SQL (see etl/load.py) for performance and
explicit upsert control, but having ORM models keeps the API layer
clean and type-safe.
"""

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    user_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user")


class Merchant(Base):
    __tablename__ = "merchants"

    merchant_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    merchant_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="merchant")


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"), index=True)
    merchant_id: Mapped[str] = mapped_column(String(50), ForeignKey("merchants.merchant_id"), index=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    payment_method: Mapped[str] = mapped_column(String(50), index=True)
    transaction_status: Mapped[str] = mapped_column(String(20), index=True)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    suspicious_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="transactions")
    merchant: Mapped["Merchant"] = relationship(back_populates="transactions")

    __table_args__ = (
        Index("idx_transactions_pm_ts", "payment_method", "transaction_status"),
        Index("idx_transactions_ts_pm_ts", "timestamp", "payment_method", "transaction_status"),
    )
