from typing import Optional, cast

from db.models import User
from fastapi import status
from schemas.exceptions import UserAlreadyExistsException, UserNotExistsException
from schemas.pydantic_models import RequestUserModel, RequestUserUpdateModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload


class UserService:

    @staticmethod
    async def select_user(session: AsyncSession, user_id: int) -> User:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise UserNotExistsException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id=`{user_id}` does not exist"
            )
        return cast(User, user)

    @staticmethod
    async def select_users(session: AsyncSession, user_id: Optional[int] = None, email: Optional[str] = None, user_status: Optional[str] = None) -> list[User]:
        q = select(User).order_by(User.created.desc())
        if user_id is not None:
            q = q.where(User.id == user_id)
        if email is not None:
            q = q.where(User.email == email)
        if user_status is not None:
            q = q.where(User.status == user_status)
        result = await session.execute(q)
        users = result.scalars().all()
        return list(users)

    @staticmethod
    async def select_users_with_balances(session: AsyncSession, user_id: Optional[int] = None, email: Optional[str] = None, user_status: Optional[str] = None) -> list[User]:
        q = select(User).options(joinedload(User.user_balance)).order_by(User.created.desc())
        if user_id is not None:
            q = q.where(User.id == user_id)
        if email is not None:
            q = q.where(User.email == email)
        if user_status is not None:
            q = q.where(User.status == user_status)
        result = await session.execute(q)
        users = result.unique().scalars().all()
        return list(users)

    @staticmethod
    async def create_user(session: AsyncSession, user: RequestUserModel) -> User:
        db_user = await session.execute(select(User).where(User.email == user.email))
        if db_user.scalar():
            raise UserAlreadyExistsException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email=`{user.email}` already exists"
            )

        db_user = User(email=user.email, status="ACTIVE")
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)

        return cast(User, db_user)

    @staticmethod
    async def update_user(session: AsyncSession, user: RequestUserUpdateModel, db_user: User) -> User:
        db_user.status = user.status
        await session.commit()
        await session.refresh(db_user)
        return db_user
