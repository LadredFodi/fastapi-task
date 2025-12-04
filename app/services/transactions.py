"""Database query functions for analytics."""

import typing
from typing import cast

from db.models import Transaction
from fastapi import status
from schemas.enums import TransactionStatusEnum, TransactionTypeEnum
from schemas.exceptions import TransactionNotExistsException
from schemas.pydantic_models import CurrencyEnum
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class TransactionService:

    @staticmethod
    async def create_transaction(session: AsyncSession, user_id: int, currency: CurrencyEnum, amount: float, type: TransactionTypeEnum) -> Transaction:
        """Create transaction for user in database."""
        transaction = Transaction(user_id=user_id, currency=currency, amount=amount, type=type)
        session.add(transaction)
        await session.commit()
        return transaction

    @staticmethod
    async def select_transaction(session: AsyncSession, transaction_id: int) -> Transaction:
        """Select transaction by id in database."""
        q = select(Transaction).where(Transaction.id == transaction_id)
        result = await session.execute(q)
        transaction = result.scalar_one_or_none()

        if not transaction:
            raise TransactionNotExistsException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transaction with id=`{transaction_id}` does not exist"
            )
        return cast(Transaction, transaction)

    @staticmethod
    async def select_transactions(session: AsyncSession, user_id: typing.Optional[int] = None) -> typing.List[Transaction]:
        """Select transactions for user in database."""
        if user_id is not None:
            q = select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.created.desc())
        else:
            q = select(Transaction).order_by(Transaction.created.desc())
        transactions = await session.execute(q)
        transactions = transactions.scalars()
        return list(transactions)

    @staticmethod
    async def update_transaction(session: AsyncSession, transaction_id: int, status: TransactionStatusEnum) -> Transaction:
        """Update transaction in database."""
        result = await session.execute(select(Transaction).where(Transaction.id == transaction_id))
        transaction = result.scalar_one()
        transaction.status = status
        await session.commit()
        await session.refresh(transaction)
        return cast(Transaction, transaction)
