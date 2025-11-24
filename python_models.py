"""Pydantic models for request/response validation."""

import typing
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel
from pydantic.v1 import root_validator


class CurrencyEnum(StrEnum):
    """Enumeration of supported currencies."""
    USD = "USD"
    EUR = "EUR"
    AUD = "AUD"
    CAD = "CAD"
    ARS = "ARS"
    PLN = "PLN"
    BTC = "BTC"
    ETH = "ETH"
    DOGE = "DOGE"
    USDT = "USDT"


class UserStatusEnum(StrEnum):
    """Enumeration of user statuses."""

    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"


class TransactionStatusEnum(StrEnum):
    """Enumeration of transaction statuses."""

    processed = "PROCESSED"
    roll_backed = "ROLLBACKED"


class RequestUserModel(BaseModel):
    """Model for user creation request."""

    email: str


class RequestUserUpdateModel(BaseModel):
    """Model for user update request."""

    status: UserStatusEnum


class ResponseUserBalanceModel(BaseModel):
    """Model for user balance in response."""
    currency: typing.Optional[CurrencyEnum] = None
    amount: typing.Optional[float] = None


class ResponseUserModel(BaseModel):
    """Model for user in response."""

    id: typing.Optional[int]
    email: typing.Optional[str] = None
    status: typing.Optional[UserStatusEnum] = None
    created: typing.Optional[datetime] = None
    balances: typing.Optional[typing.List[ResponseUserBalanceModel]] = None


class UserModel(BaseModel):
    """Model for user data."""
    id: typing.Optional[int]
    email: typing.Optional[str] = None
    status: typing.Optional[UserStatusEnum] = None
    created: typing.Optional[datetime] = None


class UserBalanceModel(BaseModel):
    """Model for user balance data."""

    id: typing.Optional[int]
    user_id: typing.Optional[int] = None
    currency: typing.Optional[CurrencyEnum] = None
    amount: typing.Optional[float] = None

    @root_validator(pre=True)
    def validate_not_negative(self, values):
        """Validate that amount is not negative."""
        if "amount" in values and values.get("amount"):
            if values["amount"] < 0:
                raise ValueError("Amount cannot be negative")

        return values


class RequestTransactionModel(BaseModel):
    """Model for transaction creation request."""
    currency: CurrencyEnum
    amount: float


class TransactionModel(BaseModel):
    """Model for transaction data."""

    id: typing.Optional[int]
    user_id: typing.Optional[int] = None
    currency: typing.Optional[CurrencyEnum] = None
    amount: typing.Optional[float] = None
    status: typing.Optional[TransactionStatusEnum] = None
    created: typing.Optional[datetime] = None
