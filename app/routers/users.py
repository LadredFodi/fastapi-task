import typing
from datetime import datetime, timezone

from db.db import SessionDep
from fastapi import APIRouter, status
from schemas.enums import CurrencyEnum, UserStatusEnum
from schemas.exceptions import BadRequestDataException, UserAlreadyBlockedException
from schemas.pydantic_models import (
    RequestUserModel,
    RequestUserUpdateModel,
    ResponseUserBalanceModel,
    ResponseUserModel,
    UserModel,
)
from services.balance import BalanceService
from services.users import UserService

router = APIRouter()


@router.get("/users", response_model=typing.List[ResponseUserModel], status_code=status.HTTP_200_OK)
async def get_users(
    session: SessionDep,
    user_id: typing.Optional[int] = None,
    email: typing.Optional[str] = None,
    user_status: typing.Optional[str] = None,
) -> typing.List[ResponseUserModel]:

    users_with_balances = await UserService.select_users_with_balances(session, user_id, email, user_status)
    results = []
    for user in users_with_balances:
        result = ResponseUserModel(
            id=user.id, email=user.email, status=UserStatusEnum(user.status), created=user.created
        )
        balances_list = [
            ResponseUserBalanceModel(currency=CurrencyEnum(b.currency), amount=float(b.amount))
            for b in user.user_balance
        ]
        balances_list = sorted(balances_list, key=lambda x: x.amount if x.amount is not None else 0.0)
        result.balances = balances_list
        results.append(result)
    return sorted(results, key=lambda x: x.created if x.created else datetime.min.replace(tzinfo=timezone.utc))


@router.post("/users", status_code=status.HTTP_200_OK)
async def post_user(user: RequestUserModel, session: SessionDep):

    new_user = await UserService.create_user(session, user)

    for currency in CurrencyEnum:
        await BalanceService.create_balance(session, new_user.id, currency)

    result = UserModel(id=new_user.id, email=new_user.email, status=UserStatusEnum(new_user.status), created=new_user.created)
    return result


@router.patch("/users/{user_id}", response_model=UserModel)
async def patch_user(user_id: int, user: RequestUserUpdateModel, session: SessionDep):
    if user_id < 0:
        raise BadRequestDataException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unprocessable data in request")

    db_user = await UserService.select_user(session, user_id)

    if db_user.status == user.status:
        raise UserAlreadyBlockedException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"User with id=`{user_id}` is already {user.status}"
        )

    updated_user = await UserService.update_user(session, user, db_user)

    result = UserModel(id=updated_user.id, email=updated_user.email, status=UserStatusEnum(updated_user.status), created=updated_user.created)
    return result
