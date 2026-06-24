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

from sqlalchemy import Boolean, ForeignKey, Numeric, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    user_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user")


class Merchant(Base):
    __tablename__ = "merchants"

    merchant_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    merchant_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="merchant")


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"))
    merchant_id: Mapped[str] = mapped_column(String(50), ForeignKey("merchants.merchant_id"))
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    payment_method: Mapped[str] = mapped_column(String(50))
    transaction_status: Mapped[str] = mapped_column(String(20))
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False)
    suspicious_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="transactions")
    merchant: Mapped["Merchant"] = relationship(back_populates="transactions")
