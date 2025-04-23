from datetime import datetime

from pydantic_settings import BaseSettings
from pydantic import SecretStr
from dotenv import load_dotenv


class classproperty:
    def __init__(self, method):
        self.method = method

    def __get__(self, obj, owner):
        return self.method(owner)

class Serialize:
    command = "week"
    start_date = datetime(2025, 1, 1, 9)

    _commands = {
        "three_month": "Трехмесячный оптимизатор",
        "week": "Недельный оптимизатор",
        "sups": "Оптимизатор поставок"
    }
    _status = {
        "Закончен": "finished",
    }
    _pos_status = {
        "chosen": "Выбран оптимизатором",
        "deadline": "Вышел за дедлайн",
        "calendar": "Вышел за календарь",
        "data": "Проблема с данными"
    }

    @classmethod
    def get_command(cls):
        return cls._commands.get(cls.command)

    @classmethod
    def get_status(cls, status):
        return cls._status.get(status)

    @classmethod
    def get_pos_status(cls, status):
        return cls._pos_status.get(status)

    @classproperty
    def is_week(cls):
        return cls.get_command() == "Недельный оптимизатор"

class Settings(BaseSettings):
    DB_HOST: SecretStr
    DB_PORT: SecretStr
    DB_USER: SecretStr
    DB_PASS: SecretStr
    DB_NAME: SecretStr

    RMQ_USER: SecretStr
    RMQ_PASS: SecretStr
    RMQ_HOST: SecretStr

    load_dotenv()

    @property
    def database_url_psycopg2(self) -> object:
        return (
            f"postgresql+psycopg2:\
//{self.DB_USER.get_secret_value()}\
:{self.DB_PASS.get_secret_value()}\
@{self.DB_HOST.get_secret_value()}\
:{self.DB_PORT.get_secret_value()}\
/{self.DB_NAME.get_secret_value()}"
        )

    @property
    def database_url_async(self) -> object:
        return (
            f"postgresql+asyncpg:\
//{self.DB_USER.get_secret_value()}\
:{self.DB_PASS.get_secret_value()}\
@{self.DB_HOST.get_secret_value()}\
:{self.DB_PORT.get_secret_value()}\
/{self.DB_NAME.get_secret_value()}"
        )

    @property
    def pg_data(self) -> dict:
        return {
            'dbname': self.DB_NAME.get_secret_value(),
            'user': self.DB_USER.get_secret_value(),
            'password': self.DB_PASS.get_secret_value(),
            'host': self.DB_HOST.get_secret_value(),
            'port': self.DB_PORT.get_secret_value(),
        }

    @property
    def rabbit_mq_credentials(self) -> dict:
        return {
            'username': self.RMQ_USER.get_secret_value(),
            'password': self.RMQ_PASS.get_secret_value()
        }

    @property
    def rabbit_mq_host(self) -> str:
        return self.RMQ_HOST.get_secret_value()


settings = Settings()
