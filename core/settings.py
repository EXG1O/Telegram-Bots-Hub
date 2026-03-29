from dotenv import load_dotenv
from yarl import URL

from pathlib import Path
from secrets import token_hex
from typing import Final
import logging.config
import os

load_dotenv()


BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
LOGS_DIR: Final[Path] = BASE_DIR / 'logs'

os.makedirs(LOGS_DIR, exist_ok=True)


DEBUG: Final[bool] = os.getenv('DEBUG', 'True') == 'True'

BOT_MONITOR_TOKEN_INTERVAL: Final[int] = 60 if DEBUG else 86400
BOT_BACKGROUND_TASKS_INTERVAL: Final[int] = 60 if DEBUG else 3600

REDIS_URL: Final[str] = os.environ['REDIS_URL']

SELF_URL: Final[URL] = URL(os.environ['SELF_URL'])
SELF_TOKEN: Final[str] = os.environ['SELF_TOKEN']
TELEGRAM_TOKEN: Final[str] = token_hex(32)

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
                'backupCount': 10,
                'formatter': 'verbose',
            },
            'error_file': {
                'level': 'WARNING',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOGS_DIR / 'app_error.log',
                'maxBytes': 5 * 1024**2,
                'backupCount': 10,
                'formatter': 'verbose',
            },
        },
        'root': {
            'handlers': ['console', 'info_file', 'error_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
    }
)
