import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from typing import Annotated

from docs.database import settings
from docs.utils import setup_logger


logging = setup_logger(__name__)

intpk = Annotated[int, mapped_column(primary_key=True)]


try:
    """Синхронный движок и синхронная сессия"""
    sync_engine = create_engine(
        url=settings.database_url_psycopg2,
        echo=False,
    )
    logging.info('Sync Engine успешно создан')

    sync_session = sessionmaker(sync_engine)
    logging.info('Sync Session успешно создан')

    with sync_engine.connect() as conn:  # проверка подключения к БД
        res = conn.execute(text("SELECT VERSION()"))
        logging.info(f"Успешное подключение с Sync Engine {res.first()}")

except Exception as e:
    logging.error("sync connect:: ", e)

try:
    """Асинхронный движок и асинхронная сессия"""
    async_engine = create_async_engine(
        url=settings.database_url_async,
        echo=False,
    )
    logging.info('Async Engine успешно создан')

    async_session = async_sessionmaker(async_engine)
    logging.info('Async Session успешно создан')

except Exception as e:
    logging.error("async connect:: ", e)

try:
    """Коннект для psycopg"""
    connect = psycopg2.connect(**settings.pg_data)
    logging.info("psycog connect успешно создан")

except Exception as e:
    logging.error("psycopg connect:: ", e)
