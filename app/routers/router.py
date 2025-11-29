"""FastAPI application main module."""

import typing
from datetime import datetime, timedelta, timezone

from db.db import SessionDep
from db.models import Transaction, User, UserBalance
from fastapi import APIRouter, status
from schemas.enums import CurrencyEnum, TransactionStatusEnum, UserStatusEnum
from schemas.exceptions import (
    BadRequestDataException,
    CreateTransactionForBlockedUserException,
    NegativeBalanceException,
    TransactionAlreadyRollbackedException,
    TransactionDoesNotBelongToUserException,
    TransactionNotExistsException,
    UpdateTransactionForBlockedUserException,
    UserAlreadyActiveException,
    UserAlreadyBlockedException,
    UserAlreadyExistsException,
    UserNotExistsException,
)
from schemas.pydantic_models import (
    RequestTransactionModel,
    RequestUserModel,
    RequestUserUpdateModel,
    ResponseUserBalanceModel,
    ResponseUserModel,
    TransactionModel,
    UserModel,
)
from services.queries import (
    get_not_rollbacked_deposit_amount,
    get_not_rollbacked_transactions_count,
    get_not_rollbacked_withdraw_amount,
    get_registered_and_deposit_users_count,
    get_registered_and_not_rollbacked_deposit_users_count,
    get_registered_users_count,
    get_transactions_count,
)
from sqlalchemy import insert, select, update

router = APIRouter()


@router.get("/users", response_model=typing.List[ResponseUserModel], status_code=status.HTTP_200_OK)
async def get_users(
    session: SessionDep,
    user_id: typing.Optional[int] = None,
    email: typing.Optional[str] = None,
    user_status: typing.Optional[str] = None,
) -> typing.List[ResponseUserModel]:
    q = select(User).order_by(User.created.desc())
    if user_id is not None:
        q = q.where(User.id == user_id)
    if email is not None:
        q = q.where(User.email == email)
    if user_status is not None:
        q = q.where(User.status == user_status)
    users = await session.execute(q)
    users = users.scalars()
    results = []
    for user in users:
        result = ResponseUserModel(
            id=user.id, email=user.email, status=UserStatusEnum(user.status), created=user.created
        )
        balances = await session.execute(select(UserBalance).where(UserBalance.user_id == user.id))
        balances = balances.scalars()

        balances_list = [
            ResponseUserBalanceModel(currency=CurrencyEnum(b.currency), amount=float(b.amount))
            for b in balances
        ]
        balances_list = sorted(balances_list, key=lambda x: x.amount if x.amount is not None else 0.0)
        result.balances = balances_list
        results.append(result)
    return sorted(results, key=lambda x: x.created if x.created else datetime.min.replace(tzinfo=timezone.utc))


@router.post("/users", status_code=status.HTTP_200_OK)
async def post_user(user: RequestUserModel, session: SessionDep):
    email = user.email.strip()
    email = ''.join([x for x in email if x != ' '])
    if len(email) == 0:
        raise BadRequestDataException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Email can't consist entirely of spaces")
    db_user = await session.execute(select(User).where(User.email == user.email))
    if db_user.scalar():
        raise UserAlreadyExistsException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email=`{user.email}` already exists"
        )
    db_user = User(email=user.email, status="ACTIVE", created=datetime.now(timezone.utc))
    session.add(db_user)
    await session.commit()
    currencies = list({str(x) for x in CurrencyEnum})
    for currency in currencies:
        user_balance = UserBalance(user_id=db_user.id, currency=currency, amount=0, created=datetime.now(timezone.utc))
        session.add(user_balance)
        await session.commit()
    result = await session.execute(select(User).where(User.email == user.email))
    result = result.scalar()
    result = UserModel(id=result.id, email=result.email, status=UserStatusEnum(result.status), created=result.created)
    return result


@router.patch("/users/{user_id}", response_model=UserModel)
async def patch_user(user_id: int, user: RequestUserUpdateModel, session: SessionDep):
    if user_id < 0:
        raise BadRequestDataException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unprocessable data in request")
    db_user = await session.execute(select(User).where(User.id == user_id))
    db_user = db_user.scalar()
    if not db_user:
        raise UserNotExistsException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id=`{user_id}` does not exist"
        )
    if db_user.status == "BLOCKED" and user.status == "BLOCKED":
        raise UserAlreadyBlockedException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"User with id=`{user_id}` is already blocked"
        )
    if db_user.status == "ACTIVE" and user.status == "ACTIVE":
        raise UserAlreadyActiveException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"User with id=`{user_id}` is already active"
        )
    await session.execute(update(User).values(**{"status": user.status}).where(User.id == user_id))
    await session.commit()
    user = await session.execute(select(User).where(User.id == user_id))
    user = user.scalar()
    result = UserModel(id=user.id, email=user.email, status=UserStatusEnum(user.status), created=user.created)
    return result


@router.get("/transactions", response_model=typing.List[TransactionModel], status_code=status.HTTP_200_OK)
async def get_transactions(
    session: SessionDep,
    user_id: typing.Optional[int] = None,
) -> typing.List[TransactionModel]:
    q = select(Transaction).order_by(Transaction.created.desc())
    if user_id:
        q = q.where(Transaction.user_id == user_id)

    transactions = await session.execute(q)
    transactions = transactions.scalars()
    results = []
    for t in transactions:
        result = TransactionModel(
            **{
                "id": t.id,
                "user_id": t.user_id,
                "currency": CurrencyEnum(t.currency),
                "amount": t.amount,
                "status": TransactionStatusEnum(t.status),
                "created": t.created
            }
        )
        results.append(result)
    return results


@router.post("/{user_id}/transactions", response_model=TransactionModel, status_code=status.HTTP_200_OK)
async def post_transaction(user_id: int, transaction: RequestTransactionModel, session: SessionDep):
    if user_id < 0:
        raise BadRequestDataException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unprocessable data in request")
    if transaction.currency not in {str(x) for x in CurrencyEnum}:
        raise BadRequestDataException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Currency does not exist")
    if transaction.amount == 0:
        raise BadRequestDataException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Transaction can not have zero amount")

    db_user = await session.execute(select(User).where(User.id == user_id))
    db_user = db_user.scalar()
    if not db_user:
        raise UserNotExistsException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id=`{user_id}` does not exist"
        )
    if db_user.status != "ACTIVE":
        raise CreateTransactionForBlockedUserException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id=`{user_id}` is blocked"
        )

    db_user_balance = await session.execute(
        select(UserBalance).where((UserBalance.user_id == user_id) & (UserBalance.currency == transaction.currency))
    )
    db_user_balance = db_user_balance.scalar()
    if float(db_user_balance.amount) + transaction.amount < 0:
        raise NegativeBalanceException(status_code=status.HTTP_400_BAD_REQUEST, detail="Negative balance")

    await session.execute(
        update(UserBalance).values(**{"amount": transaction.amount}).where(UserBalance.id == db_user_balance.id)
    )
    await session.commit()
    await session.execute(
        insert(Transaction).values(
            **{
                "user_id": db_user.id,
                "currency": transaction.currency,
                "amount": transaction.amount,
                "status": "PROCESSED",
                "created": datetime.now(timezone.utc)
            }
        )
    )
    await session.commit()


@router.patch("/{user_id}/transactions/{transaction_id}", response_model=TransactionModel)
async def patch_rollback_transaction(user_id: int, transaction_id: int, session: SessionDep):
    if user_id < 0 or transaction_id < 0:
        raise BadRequestDataException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unprocessable data in request")
    db_user = await session.execute(select(User).where(User.id == user_id))
    db_user = db_user.scalar()
    if not db_user:
        raise UserNotExistsException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id=`{user_id}` does not exist"
        )
    db_transaction = await session.execute(select(Transaction).where(Transaction.id == transaction_id))
    db_transaction = db_transaction.scalar()
    if not db_transaction:
        raise TransactionNotExistsException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction with id=`{transaction_id}` does not exist"
        )
    if db_transaction.user_id != db_user.id:
        raise TransactionDoesNotBelongToUserException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction with id=`{transaction_id}` does not belong to user with id=`{user_id}`"
        )
    if db_transaction.status == "ROLLBACKED":
        raise TransactionAlreadyRollbackedException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction with id=`{transaction_id}` is already rollbacked"
        )
    if db_user.status == "BLOCKED":
        raise UpdateTransactionForBlockedUserException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"User with id=`{user_id}` is blocked"
        )

    db_user_balance = await session.execute(
        select(UserBalance).where((UserBalance.user_id == user_id) & (UserBalance.currency == db_transaction.currency))
    )
    db_user_balance = db_user_balance.scalar()
    new_amount = float(db_user_balance.amount)
    if db_transaction.amount < 0:
        new_amount += abs(float(db_transaction.amount))
    else:
        new_amount -= float(db_transaction.amount)
    if new_amount < 0:
        raise NegativeBalanceException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Negative balance: {new_amount}")
    await session.execute(
        update(UserBalance).values(**{"amount": new_amount}).where(UserBalance.id == db_user_balance.id)
    )
    await session.commit()
    await session.execute(update(Transaction).values(**{"status": "ROLLBACKED"}).where(Transaction.id == transaction_id))
    await session.commit()


@router.get("/transactions/analysis", response_model=typing.List[typing.Dict[str, typing.Any]], status_code=status.HTTP_200_OK)
async def get_transaction_analysis(session: SessionDep) -> typing.List[typing.Dict[str, typing.Any]]:
    """Get transaction analysis for the last 52 weeks."""
    dt_gt = datetime.now(timezone.utc).date() - timedelta(weeks=1) + timedelta(days=1)
    dt_lt = datetime.now(timezone.utc).date()
    results = []
    for i in range(52):
        registered_users_count = await get_registered_users_count(session, dt_gt=dt_gt, dt_lt=dt_lt)
        registered_and_deposit_users_count = await get_registered_and_deposit_users_count(session, dt_gt=dt_gt, dt_lt=dt_lt)
        registered_and_not_rollbacked_deposit_users_count = await get_registered_and_not_rollbacked_deposit_users_count(session, dt_gt=dt_gt, dt_lt=dt_lt)
        not_rollbacked_deposit_amount = await get_not_rollbacked_deposit_amount(session, dt_gt=dt_gt, dt_lt=dt_lt)
        not_rollbacked_withdraw_amount = await get_not_rollbacked_withdraw_amount(session, dt_gt=dt_gt, dt_lt=dt_lt)
        transactions_count = await get_transactions_count(session, dt_gt=dt_gt, dt_lt=dt_lt)
        not_rollbacked_transactions_count = await get_not_rollbacked_transactions_count(session, dt_gt=dt_gt, dt_lt=dt_lt)
        result = {
            "start_date": dt_gt,
            "end_date": dt_lt,
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
    return results
