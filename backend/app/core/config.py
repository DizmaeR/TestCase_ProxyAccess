from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_MODE: str
    APP_PORT: int

    PG_HOST: str
    PG_PORT: int
    PG_DATABASE: str
    PG_USERNAME: str
    PG_PASSWORD: str

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_DAYS: int

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_SERVER: str
    MAIL_PORT: int

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore[call-arg]
