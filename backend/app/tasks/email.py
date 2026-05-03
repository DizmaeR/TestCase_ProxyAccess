import asyncio

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import NameEmail, SecretStr

from app.core.config import settings
from app.tasks.celery_app import celery_app

mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=SecretStr(settings.MAIL_PASSWORD),
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)


@celery_app.task
def send_activation_email(email: str, activation_key: str) -> None:
    async def _send() -> None:
        message = MessageSchema(
            subject="Ваш ключ активации",
            recipients=[NameEmail(name="", email=email)],
            body=f"Добро пожаловать!\n\nВаш ключ активации: {activation_key}",
            subtype=MessageType.plain,
        )
        fm = FastMail(mail_config)
        await fm.send_message(message)

    asyncio.run(_send())
