import typing

import uvicorn
from db.db import create_db_and_tables
from fastapi import FastAPI
from routers.router import router


async def lifespan(app: FastAPI) -> typing.AsyncGenerator[None, None]:
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
