import asyncio
import json
from datetime import datetime, timedelta, timezone

from celery import shared_task
from config.settings import settings
from services.queries import QueryService
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@shared_task
def get_analysis():

    async def run():

        base_url = f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
        engine = create_async_engine(
            base_url,
            echo=False,
        )
        Session = async_sessionmaker(engine, expire_on_commit=False)
        async with Session() as session:
            return await make_analysis(session)

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(run())
    finally:
        loop.close()


# TODO optimize
async def make_analysis(session: AsyncSession):

    dt_gt = datetime.now(timezone.utc).date() - timedelta(weeks=1) + timedelta(days=1)
    dt_lt = datetime.now(timezone.utc).date()
    results = []
    for i in range(52):
        registered_users_count = await QueryService.get_registered_users_count(session, dt_gt=dt_gt, dt_lt=dt_lt)
        registered_and_deposit_users_count = await QueryService.get_registered_and_deposit_users_count(session, dt_gt=dt_gt, dt_lt=dt_lt)
        registered_and_not_rollbacked_deposit_users_count = await QueryService.get_registered_and_not_rollbacked_deposit_users_count(session, dt_gt=dt_gt, dt_lt=dt_lt)
        not_rollbacked_deposit_amount = await QueryService.get_not_rollbacked_deposit_amount(session, dt_gt=dt_gt, dt_lt=dt_lt)
        not_rollbacked_withdraw_amount = await QueryService.get_not_rollbacked_withdraw_amount(session, dt_gt=dt_gt, dt_lt=dt_lt)
        transactions_count = await QueryService.get_transactions_count(session, dt_gt=dt_gt, dt_lt=dt_lt)
        not_rollbacked_transactions_count = await QueryService.get_not_rollbacked_transactions_count(session, dt_gt=dt_gt, dt_lt=dt_lt)
        result = {
            "start_date": str(dt_gt),
            "end_date": str(dt_lt),
            "registered_users_count": registered_users_count,
            "registered_and_deposit_users_count": registered_and_deposit_users_count,
            "registered_and_not_rollbacked_deposit_users_count": registered_and_not_rollbacked_deposit_users_count,
            "not_rollbacked_deposit_amount": not_rollbacked_deposit_amount,
            "not_rollbacked_withdraw_amount": not_rollbacked_withdraw_amount,
            "transactions_count": transactions_count,
            "not_rollbacked_transactions_count": not_rollbacked_transactions_count,
        }
        for field in (
            "registered_users_count",
            "registered_and_deposit_users_count",
            "registered_and_not_rollbacked_deposit_users_count",
            "not_rollbacked_deposit_amount",
            "not_rollbacked_withdraw_amount",
            "transactions_count",
            "not_rollbacked_transactions_count",
        ):
            field_value = result[field]
            if isinstance(field_value, (int, float)) and field_value > 0:
                results.append(result)
                break
        dt_gt -= timedelta(weeks=1)
        dt_lt -= timedelta(weeks=1)

    with open('analysis.json', 'w') as f:
        json.dump(results, f)
