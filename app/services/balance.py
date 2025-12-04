from decimal import Decimal
from typing import cast

from db.models import UserBalance
from fastapi import status
from schemas.enums import CurrencyEnum
from schemas.exceptions import NegativeBalanceException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BalanceService:

    @staticmethod
    async def create_balance(session: AsyncSession, user_id: int, currency: CurrencyEnum) -> UserBalance:
        """Create balance for user in database."""

        user_balance = UserBalance(user_id=user_id, currency=currency, amount=0)
        session.add(user_balance)
        await session.commit()
        await session.refresh(user_balance)
        return user_balance

    @staticmethod
    async def select_balance(session: AsyncSession, user_id: int, currency: CurrencyEnum) -> UserBalance:
        """Select balance for user in database."""
        q = select(UserBalance).where(UserBalance.user_id == user_id, UserBalance.currency == currency)
        result = await session.execute(q)
        user_balance = result.scalar_one()
        return cast(UserBalance, user_balance)

    @staticmethod
    async def add_balance(session: AsyncSession, user_id: int, currency: CurrencyEnum, amount: Decimal) -> UserBalance:
        """Add balance for user in database."""
        result = await session.execute(select(UserBalance).where(UserBalance.user_id == user_id, UserBalance.currency == currency))
        user_balance = result.scalar_one()
        user_balance.amount += amount
        await session.commit()
        await session.refresh(user_balance)
        return cast(UserBalance, user_balance)

    @staticmethod
    async def subtract_balance(session: AsyncSession, user_id: int, currency: CurrencyEnum, amount: Decimal) -> UserBalance:
        """Subtract balance for user in database."""
        result = await session.execute(select(UserBalance).where(UserBalance.user_id == user_id, UserBalance.currency == currency))
        user_balance = result.scalar_one()
        if user_balance.amount - amount < 0:
            raise NegativeBalanceException(status_code=status.HTTP_400_BAD_REQUEST, detail="Negative balance")
        user_balance.amount -= amount
        await session.commit()
        await session.refresh(user_balance)
        return cast(UserBalance, user_balance)
