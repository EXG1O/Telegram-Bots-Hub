from dotenv import load_dotenv
from yarl import URL

from .enums import Mode

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


MODE: Final[Mode] = Mode(os.getenv('MODE', 'debug').lower())

BOT_BACKGROUND_MONITOR_TOKEN_INTERVAL: Final[int] = 60 if MODE == Mode.DEBUG else 86400
BOT_BACKGROUND_PROCESS_SERVICE_TASKS_INTERVAL: Final[int] = (
    60 if MODE == Mode.DEBUG else 3600
)

REDIS_URL: Final[str] = os.environ['REDIS_URL']

SELF_TOKEN: Final[str] = os.environ['SELF_TOKEN']
TELEGRAM_TOKEN: Final[str] = os.environ['TELEGRAM_TOKEN']

SERVICE_URL: Final[URL] = URL(os.environ['SERVICE_URL'])
SERVICE_UNIX_SOCK: Final[Path | None] = (
    Path(path) if (path := os.getenv('SERVICE_UNIX_SOCK')) else None
)
SERVICE_TOKEN: Final[str] = os.environ['SERVICE_TOKEN']


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
