from dotenv import load_dotenv
from yarl import URL

from ._profile_settings import ProfileSettings, build_profile_settings
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


MODE: Final[Mode] = Mode(os.getenv('MODE', Mode.DEBUG).lower())
PREMIUM: Final[bool] = os.getenv('PREMIUM', 'False') == 'True'

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


_profile_settings: ProfileSettings = build_profile_settings(mode=MODE, premium=PREMIUM)

BOT_TELEGRAM_WEBHOOK_MAX_CONNECTIONS: Final[int] = _profile_settings[
    'bot_telegram_webhook_max_connections'
]

BOT_BACKGROUND_MONITOR_TOKEN_INTERVAL: Final[float] = (
    _profile_settings['bot_background_monitor_token_interval']
).total_seconds()
BOT_BACKGROUND_PROCESS_SERVICE_TASKS_INTERVAL: Final[float] = (
    _profile_settings['bot_background_process_service_tasks_interval']
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
            'level': _profile_settings['log_level'],
        },
    }
)
