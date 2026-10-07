from dotenv import load_dotenv
from yarl import URL

from .enums import Mode

from datetime import timedelta
from pathlib import Path
from typing import Final
import logging.config
import os
import socket

load_dotenv()


CONTAINER_ID: Final[str] = socket.gethostname()

BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
LOGS_DIR: Final[Path] = BASE_DIR / 'logs' / CONTAINER_ID

os.makedirs(LOGS_DIR, exist_ok=True)


MODE: Final[Mode] = Mode(os.getenv('MODE', Mode.DEBUG).lower())

REDIS_URL: Final[str] = os.environ['REDIS_URL']

APP_TOKEN: Final[str] = os.environ['APP_TOKEN']
TELEGRAM_TOKEN: Final[str] = os.environ['TELEGRAM_TOKEN']

SERVICE_URL: Final[URL] = URL(os.environ['SERVICE_URL'])
SERVICE_SOCKET: Final[Path | None] = (
    Path(path) if (path := os.getenv('SERVICE_SOCKET')) else None
)
SERVICE_TOKEN: Final[str] = os.environ['SERVICE_TOKEN']


TELEGRAM_GLOBAL_RATE_LIMIT: Final[float] = 30
TELEGRAM_GLOBAL_RATE_PERIOD: Final[float] = 1
TELEGRAM_USER_RATE_LIMIT: Final[float] = 1
TELEGRAM_USER_RATE_PERIOD: Final[float] = 1
TELEGRAM_GROUP_RATE_LIMIT: Final[float] = 20
TELEGRAM_GROUP_RATE_PERIOD: Final[float] = 60


BOT_TELEGRAM_WEBHOOK_MAX_CONNECTIONS: Final[int] = 10

BOT_BACKGROUND_MONITOR_TOKEN_INTERVAL: Final[float] = (
    timedelta(minutes=1) if MODE == Mode.DEBUG else timedelta(days=1)
).total_seconds()
BOT_BACKGROUND_PROCESS_SERVICE_TASKS_INTERVAL: Final[float] = (
    timedelta(minutes=1) if MODE == Mode.DEBUG else timedelta(minutes=15)
).total_seconds()


logging.config.dictConfig(
    {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '[{asctime}]: {levelname}: {name} > {funcName} || {message}',
                'style': '{',
            },
            'simple': {
                'format': '[{asctime}]: {message}',
                'style': '{',
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            },
            'info_file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOGS_DIR / 'app_info.log',
                'maxBytes': 5 * 1024**2,
                'formatter': 'verbose',
            },
            'error_file': {
                'level': 'WARNING',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOGS_DIR / 'app_error.log',
                'maxBytes': 5 * 1024**2,
                'formatter': 'verbose',
            },
        },
        'root': {
            'handlers': ['console', 'info_file', 'error_file'],
            'level': 'DEBUG' if MODE == Mode.DEBUG else 'INFO',
        },
    }
)
