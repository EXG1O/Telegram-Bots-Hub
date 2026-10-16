from .enums import Mode

from datetime import timedelta
from typing import TypedDict
import logging


class ProfileSettings(TypedDict):
    bot_telegram_webhook_max_connections: int
    bot_background_monitor_token_interval: timedelta
    bot_background_process_service_tasks_interval: timedelta
    log_level: int


def build_profile_settings(mode: Mode, premium: bool) -> ProfileSettings:
    result = ProfileSettings(
        bot_telegram_webhook_max_connections=10,
        bot_background_monitor_token_interval=timedelta(days=1),
        bot_background_process_service_tasks_interval=timedelta(minutes=15),
        log_level=logging.INFO,
    )

    if premium:
        result.update({'bot_telegram_webhook_max_connections': 30})

    if mode == Mode.DEBUG:
        task_interval = timedelta(minutes=1)
        result.update(
            {
                'bot_background_monitor_token_interval': task_interval,
                'bot_background_process_service_tasks_interval': task_interval,
                'log_level': logging.DEBUG,
            }
        )

    return result
