from datetime import datetime, timezone

from schemas.enums import TransactionStatusEnum, TransactionTypeEnum, UserStatusEnum
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):  # type: ignore[misc, valid-type]
    """User model representing a user in the system."""
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    status = Column(Enum(UserStatusEnum), nullable=False, default=UserStatusEnum.ACTIVE)
    created = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))

    user_balance = relationship("UserBalance", back_populates="owner")


class UserBalance(Base):  # type: ignore[misc, valid-type]
    """User balance model representing user's balance for a currency."""
    __tablename__ = "user_balance"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    currency = Column(String, nullable=False)
    amount = Column(Numeric(precision=20, scale=8), nullable=False)
    created = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    UniqueConstraint('user_id', 'currency', name='user_balance_user_currency_unique')

    owner = relationship("User", back_populates="user_balance")


class Transaction(Base):  # type: ignore[misc, valid-type]
    """Transaction model representing a financial transaction."""
    __tablename__ = "transaction"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    currency = Column(String, nullable=False)
    amount = Column(Numeric(precision=20, scale=8), nullable=False)
    status = Column(Enum(TransactionStatusEnum), nullable=False, default=TransactionStatusEnum.PROCESSED)
    type = Column(Enum(TransactionTypeEnum), nullable=False)
    created = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
