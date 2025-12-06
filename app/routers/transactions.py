import json
import typing
from decimal import Decimal

from db.db import SessionDep
from fastapi import APIRouter, status
from schemas.enums import CurrencyEnum, TransactionStatusEnum, TransactionTypeEnum, UserStatusEnum
from schemas.exceptions import (
    CreateTransactionForBlockedUserException,
    TransactionAlreadyRollbackedException,
    UpdateTransactionForBlockedUserException,
)
from schemas.pydantic_models import RequestTransactionModel, TransactionModel
from services.balance import BalanceService
from services.celery.tasks import make_analysis
from services.transactions import TransactionService
from services.users import UserService

router = APIRouter()


@router.get("/transactions", response_model=typing.List[TransactionModel], status_code=status.HTTP_200_OK)
async def get_transactions(
    session: SessionDep,
    user_id: typing.Optional[int] = None,
) -> typing.List[TransactionModel]:

    transactions = await TransactionService.select_transactions(session, user_id)

    results = []
    for t in transactions:
        result = TransactionModel(
            **{
                "id": t.id,
                "user_id": t.user_id,
                "currency": CurrencyEnum(t.currency),
                "amount": t.amount,
                "status": TransactionStatusEnum(t.status),
                "type": TransactionTypeEnum(t.type),
                "created": t.created
            }
        )
        results.append(result)
    return results


@router.post("/transactions/{user_id}/withdraw", response_model=TransactionModel, status_code=status.HTTP_200_OK)
async def post_withdraw_transaction(user_id: int, transaction: RequestTransactionModel, session: SessionDep):
    user = await UserService.select_user(session, user_id)

    if user.status != UserStatusEnum.ACTIVE:
        raise CreateTransactionForBlockedUserException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id=`{user_id}` is blocked"
        )

    await BalanceService.subtract_balance(
        session=session,
        user_id=user_id,
        currency=transaction.currency,
        amount=Decimal(transaction.amount),
    )

    new_transaction = await TransactionService.create_transaction(session, user_id, transaction.currency, float(transaction.amount), type=TransactionTypeEnum.WITHDRAW)

    return TransactionModel(
        id=new_transaction.id,
        user_id=new_transaction.user_id,
        currency=CurrencyEnum(new_transaction.currency),
        amount=new_transaction.amount,
        status=TransactionStatusEnum(new_transaction.status),
        type=TransactionTypeEnum(new_transaction.type),
        created=new_transaction.created
    )


@router.post("/transactions/{user_id}/deposit", response_model=TransactionModel, status_code=status.HTTP_200_OK)
async def post_deposit_transaction(user_id: int, transaction: RequestTransactionModel, session: SessionDep):
    user = await UserService.select_user(session, user_id)

    if user.status != UserStatusEnum.ACTIVE:
        raise CreateTransactionForBlockedUserException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id=`{user_id}` is blocked"
        )

    await BalanceService.add_balance(session, user_id, transaction.currency, Decimal(transaction.amount))

    new_transaction = await TransactionService.create_transaction(
        session=session,
        user_id=user_id,
        currency=transaction.currency,
        amount=float(transaction.amount),
        type=TransactionTypeEnum.DEPOSIT
    )

    return TransactionModel(
        id=new_transaction.id,
        user_id=new_transaction.user_id,
        currency=CurrencyEnum(new_transaction.currency),
        amount=new_transaction.amount,
        status=TransactionStatusEnum(new_transaction.status),
        type=TransactionTypeEnum(new_transaction.type),
        created=new_transaction.created
    )


@router.patch("/transactions/{user_id}/rollback/{transaction_id}", response_model=TransactionModel)
async def patch_rollback_transaction(user_id: int, transaction_id: int, session: SessionDep):

    db_user = await UserService.select_user(session, user_id)

    if db_user.status == UserStatusEnum.BLOCKED:
        raise UpdateTransactionForBlockedUserException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"User with id=`{user_id}` is blocked"
        )

    db_transaction = await TransactionService.select_transaction(session, transaction_id)

    if db_transaction.status == TransactionStatusEnum.ROLLBACKED:
        raise TransactionAlreadyRollbackedException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction with id=`{transaction_id}` is already rollbacked"
        )

    if db_transaction.type == TransactionTypeEnum.WITHDRAW:
        await BalanceService.add_balance(
            session=session,
            user_id=user_id,
            currency=db_transaction.currency,
            amount=Decimal(db_transaction.amount),
        )
    else:
        await BalanceService.subtract_balance(
            session=session,
            user_id=user_id,
            currency=db_transaction.currency,
            amount=Decimal(db_transaction.amount),
        )

    transaction = await TransactionService.update_transaction(session, transaction_id, TransactionStatusEnum.ROLLBACKED)

    return TransactionModel(
        id=transaction.id,
        user_id=transaction.user_id,
        currency=CurrencyEnum(transaction.currency),
        amount=transaction.amount,
        status=TransactionStatusEnum(transaction.status),
        type=TransactionTypeEnum(transaction.type),
        created=transaction.created
    )


@router.get("/transactions/analysis", response_model=typing.List[typing.Dict[str, typing.Any]], status_code=status.HTTP_200_OK)
async def get_transaction_analysis(session: SessionDep) -> typing.List[typing.Dict[str, typing.Any]]:
    """Get transaction analysis for the last 52 weeks."""

    try:
        with open('analysis.json', 'r') as f:
            results: typing.List[typing.Dict[str, typing.Any]] = json.load(f)

    except FileNotFoundError:
        await make_analysis(session)
        with open('analysis.json', 'r') as f:
            results = typing.cast(typing.List[typing.Dict[str, typing.Any]], json.load(f))

    return results
