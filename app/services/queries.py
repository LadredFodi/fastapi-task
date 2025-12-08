"""Database query functions for analytics."""

from datetime import date

from db.models import Transaction, User
from schemas.pydantic_models import CurrencyEnum
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class QueryService:

    EXCHANGE_RATES_TO_USD = {
        CurrencyEnum.USD: 1,
        CurrencyEnum.EUR: 0.9342,
        CurrencyEnum.AUD: 0.5447,
        CurrencyEnum.CAD: 0.6162,
        CurrencyEnum.ARS: 0.0009,
        CurrencyEnum.PLN: 0.2343,
        CurrencyEnum.BTC: 100000.0,
        CurrencyEnum.ETH: 3557.3476,
        CurrencyEnum.DOGE: 0.3627,
        CurrencyEnum.USDT: 0.9709,
    }

    @staticmethod
    async def get_registered_users_count(session: AsyncSession, dt_gt: date, dt_lt: date) -> int:
        """Get count of registered users in date range."""
        q = select(User).where((func.date(User.created) >= dt_gt) & (func.date(User.created) <= dt_lt))
        registered_users = await session.execute(q)
        registered_users = registered_users.fetchall()
        return len(registered_users)

    @staticmethod
    async def get_registered_and_deposit_users_count(session: AsyncSession, dt_gt: date, dt_lt: date) -> int:
        """Get count of registered users who made deposits in date range."""
        result = 0
        q = select(User).where((func.date(User.created) >= dt_gt) & (func.date(User.created) <= dt_lt))
        registered_users = await session.execute(q)
        registered_users = registered_users.scalars()
        for user in registered_users:
            q = select(Transaction).where((func.date(Transaction.created) >= dt_gt) & (func.date(Transaction.created) <= dt_lt) & (Transaction.user_id == user.id) & (Transaction.amount > 0))
            deposits = await session.execute(q)
            deposits = deposits.fetchall()
            if len(deposits) > 0:
                result += 1
        return result

    @staticmethod
    async def get_registered_and_not_rollbacked_deposit_users_count(
        session: AsyncSession, dt_gt: date, dt_lt: date
    ) -> int:
        """Get count of registered users with non-rollbacked deposits in date range."""
        result = 0
        q = select(User).where((func.date(User.created) >= dt_gt) & (func.date(User.created) <= dt_lt))
        registered_users = await session.execute(q)
        registered_users = registered_users.scalars()
        for user in registered_users:
            q = select(Transaction).where(
                (func.date(Transaction.created) >= dt_gt) & (func.date(Transaction.created) <= dt_lt) & (Transaction.user_id == user.id) & (Transaction.amount > 0) & (Transaction.status != "ROLLBACKED"))
            not_rollbacked_deposits = await session.execute(q)
            not_rollbacked_deposits = not_rollbacked_deposits.fetchall()
            if len(not_rollbacked_deposits) > 0:
                result += 1
        return result

    @staticmethod
    async def get_not_rollbacked_deposit_amount(session: AsyncSession, dt_gt: date, dt_lt: date) -> float:
        """Get total amount of non-rollbacked deposits in USD in date range."""
        q = select(Transaction).where((func.date(Transaction.created) >= dt_gt) & (func.date(Transaction.created) <= dt_lt) & (Transaction.amount > 0) & (Transaction.status != "ROLLBACKED"))
        not_rollbacked_deposits = await session.execute(q)
        not_rollbacked_deposits = not_rollbacked_deposits.scalars()
        total = sum([float(x.amount) * QueryService.EXCHANGE_RATES_TO_USD[CurrencyEnum(x.currency)] for x in not_rollbacked_deposits])
        return float(total)

    @staticmethod
    async def get_not_rollbacked_withdraw_amount(session: AsyncSession, dt_gt: date, dt_lt: date) -> float:
        """Get total amount of non-rollbacked withdrawals in USD in date range."""
        q = select(Transaction).where(
            (func.date(Transaction.created) >= dt_gt) & (func.date(Transaction.created) <= dt_lt) & (Transaction.amount < 0) & (Transaction.status != "ROLLBACKED"))
        not_rollbacked_withdraws = await session.execute(q)
        not_rollbacked_withdraws = not_rollbacked_withdraws.scalars()
        return float(sum([float(x.amount) * QueryService.EXCHANGE_RATES_TO_USD[CurrencyEnum(x.currency)] for x in not_rollbacked_withdraws]))

    @staticmethod
    async def get_transactions_count(session: AsyncSession, dt_gt: date, dt_lt: date) -> int:
        """Get count of transactions in date range."""
        q = select(Transaction).where(
            (func.date(Transaction.created) >= dt_gt) & (func.date(Transaction.created) <= dt_lt))
        transactions = await session.execute(q)
        transactions = transactions.fetchall()
        return len(transactions)

    @staticmethod
    async def get_not_rollbacked_transactions_count(session: AsyncSession, dt_gt: date, dt_lt: date) -> int:
        """Get count of non-rollbacked transactions in date range."""
        q = select(Transaction).where(
            (func.date(Transaction.created) >= dt_gt) & (func.date(Transaction.created) <= dt_lt) & (Transaction.status != "ROLLBACKED"))
        transactions = await session.execute(q)
        transactions = transactions.fetchall()
        return len(transactions)
