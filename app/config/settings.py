from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "fastapi_db"

    class Config:
        env_file = ".env"


settings = Settings()
