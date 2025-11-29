from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):  # type: ignore[misc, valid-type]
    """User model representing a user in the system."""
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=True, unique=True)
    status = Column(String, nullable=True)
    created = Column(DateTime(timezone=True), nullable=True)

    user_balance = relationship("UserBalance", back_populates="owner")


class UserBalance(Base):  # type: ignore[misc, valid-type]
    """User balance model representing user's balance for a currency."""
    __tablename__ = "user_balance"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    currency = Column(String, nullable=True)
    amount = Column(Numeric(precision=20, scale=8), nullable=True)
    created = Column(DateTime(timezone=True), nullable=True)
    UniqueConstraint('user_id', 'currency', name='user_balance_user_currency_unique')

    owner = relationship("User", back_populates="user_balance")


class Transaction(Base):  # type: ignore[misc, valid-type]
    """Transaction model representing a financial transaction."""
    __tablename__ = "transaction"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    currency = Column(String, nullable=True)
    amount = Column(Numeric(precision=20, scale=8), nullable=True)
    status = Column(String, nullable=True)
    created = Column(DateTime(timezone=True), nullable=True)
