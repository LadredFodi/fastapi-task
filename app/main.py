import typing

import uvicorn
from db.db import create_db_and_tables
from fastapi import FastAPI
from routers.transactions import router as transactions_router
from routers.users import router as users_router


async def lifespan(app: FastAPI) -> typing.AsyncGenerator[None, None]:
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(users_router)
app.include_router(transactions_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
