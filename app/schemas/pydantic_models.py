"""Pydantic models for request/response validation."""

import typing
from datetime import datetime
from decimal import Decimal

from fastapi import status
from pydantic import BaseModel, EmailStr, field_validator
from schemas.enums import CurrencyEnum, TransactionStatusEnum, TransactionTypeEnum, UserStatusEnum
from schemas.exceptions import BadRequestDataException


class RequestUserModel(BaseModel):
    """Model for user creation request."""

    email: EmailStr


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

    @field_validator("amount")
    def validate_not_negative(cls, v):
        """Validate that amount is not negative."""
        if v < 0:
            raise BadRequestDataException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Amount cannot be negative")
        return v


class RequestTransactionModel(BaseModel):
    """Model for transaction creation request."""
    currency: CurrencyEnum
    amount: Decimal

    @field_validator("amount")
    def validate_amount_not_zero(cls, v):
        """Validate that amount is not zero."""
        if v == 0:
            raise BadRequestDataException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Transaction can not have zero amount")
        return v


class TransactionModel(BaseModel):
    """Model for transaction data."""

    id: typing.Optional[int]
    user_id: typing.Optional[int] = None
    currency: typing.Optional[CurrencyEnum] = None
    amount: typing.Optional[Decimal] = None
    status: typing.Optional[TransactionStatusEnum] = None
    type: typing.Optional[TransactionTypeEnum] = None
    created: typing.Optional[datetime] = None
