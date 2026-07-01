from fastapi import APIRouter, BackgroundTasks, Depends, Request, status

from telegram.models import Update

import msgspec

from bot import Bot
from core.storage import bots

from .deps import ValidBot, verify_self_token
from .exceptions import BotAlreadyEnabledError
from .schemas import BotWebhookTrigger, RestartBotData, StartBotData, StartBotsItemData

import asyncio
import logging

logger = logging.getLogger(__name__)


router = APIRouter(dependencies=[Depends(verify_self_token)])

bot_start_sem = asyncio.Semaphore(10)

update_decoder = msgspec.json.Decoder(Update)
bot_webhook_trigger_decoder = msgspec.json.Decoder(BotWebhookTrigger)


@router.get('/bots/')
async def get_bots() -> list[int]:
    return list(bots)


async def _start_bot(service_id: int, token: str, webhook_url: str) -> None:
    async with bot_start_sem:
        bot = Bot(service_id=service_id, token=token, webhook_url=webhook_url)
        bots[service_id] = bot

        try:
            await bot.start()
        except Exception as error:
            await bot.stop()
            logger.exception(
                'Unexpected error during start of bot (service_id=%s).', service_id
            )
            raise error


async def _start_bots(data: list[StartBotsItemData]) -> None:
    await asyncio.gather(
        *[_start_bot(item.id, item.token, item.webhook_url) for item in data],
        return_exceptions=True,
    )


@router.post('/bots/start/', status_code=status.HTTP_202_ACCEPTED)
async def start_bots(
    data: list[StartBotsItemData], background_tasks: BackgroundTasks
) -> None:
    background_tasks.add_task(_start_bots, data)


@router.post('/bots/{service_id}/start/', status_code=status.HTTP_202_ACCEPTED)
async def start_bot(
    service_id: int, data: StartBotData, background_tasks: BackgroundTasks
) -> None:
    if service_id in bots:
        raise BotAlreadyEnabledError()

    background_tasks.add_task(_start_bot, service_id, data.token, data.webhook_url)


async def _restart_bot(bot: Bot, token: str, webhook_url: str) -> None:
    await bot.stop()
    await _start_bot(bot.service_id, token, webhook_url)


@router.post('/bots/{service_id}/restart/', status_code=status.HTTP_202_ACCEPTED)
async def restart_bot(
    service_id: int,
    bot: ValidBot,
    data: RestartBotData,
    background_tasks: BackgroundTasks,
) -> None:
    background_tasks.add_task(_restart_bot, bot, data.token, data.webhook_url)


@router.post('/bots/{service_id}/stop/', status_code=status.HTTP_202_ACCEPTED)
async def stop_bot(
    service_id: int, bot: ValidBot, background_tasks: BackgroundTasks
) -> None:
    background_tasks.add_task(bot.stop)


@router.post(
    '/bots/{service_id}/webhooks/telegram/', status_code=status.HTTP_202_ACCEPTED
)
async def bot_webhook(
    service_id: int, bot: ValidBot, request: Request, background_tasks: BackgroundTasks
) -> None:
    background_tasks.add_task(
        bot.feed_webhook_update, update_decoder.decode(await request.body())
    )


@router.post(
    '/bots/{service_id}/webhooks/trigger/', status_code=status.HTTP_202_ACCEPTED
)
async def bot_webhook_trigger(
    service_id: int, bot: ValidBot, request: Request, background_tasks: BackgroundTasks
) -> None:
    data: BotWebhookTrigger = bot_webhook_trigger_decoder.decode(await request.body())
    background_tasks.add_task(
        bot.feed_webhook_trigger,
        data.trigger,
        data.trigger_has_target_connections,
        data.payload,
    )
