from fastapi import APIRouter, BackgroundTasks, Depends, Request, status

from telegram import Update

import msgspec

from bot import Bot
from core.storage import bots
from core.utils import safe_call

from .deps import ValidBot, verify_token
from .exceptions import BotAlreadyEnabledError
from .schemas import BotWebhookTrigger, RestartBotData, StartBotData, StartBotsItemData

import asyncio

router = APIRouter(dependencies=[Depends(verify_token)])

bot_start_semaphore = asyncio.Semaphore(10)

update_decoder = msgspec.json.Decoder(Update)
bot_webhook_trigger_decoder = msgspec.json.Decoder(BotWebhookTrigger)


@router.get('/bots/')
async def get_bots() -> list[int]:
    return list(bots)


async def _start_bot(service_id: int, token: str, webhook_url: str) -> None:
    async with bot_start_semaphore:
        bot = Bot(service_id=service_id, token=token, webhook_url=webhook_url)
        bots[service_id] = bot
        await bot.start()


async def _start_bots(data: list[StartBotsItemData]) -> None:
    async with asyncio.TaskGroup() as group:
        for item in data:
            group.create_task(
                safe_call(
                    _start_bot(
                        service_id=item.id,
                        token=item.token,
                        webhook_url=item.webhook_url,
                    )
                )
            )


@router.post('/bots/start/', status_code=status.HTTP_202_ACCEPTED)
async def start_bots(
    data: list[StartBotsItemData], background_tasks: BackgroundTasks
) -> None:
    background_tasks.add_task(_start_bots, data)


@router.post('/bots/{service_id}/start/', status_code=status.HTTP_204_NO_CONTENT)
async def start_bot(
    service_id: int, data: StartBotData, background_tasks: BackgroundTasks
) -> None:
    if service_id in bots:
        raise BotAlreadyEnabledError()

    await _start_bot(
        service_id=service_id, token=data.token, webhook_url=data.webhook_url
    )


@router.post('/bots/{service_id}/restart/', status_code=status.HTTP_204_NO_CONTENT)
async def restart_bot(
    service_id: int,
    bot: ValidBot,
    data: RestartBotData,
    background_tasks: BackgroundTasks,
) -> None:
    await bot.stop(retain_registry=True)
    await _start_bot(
        service_id=bot.service_id, token=data.token, webhook_url=data.webhook_url
    )


@router.post('/bots/{service_id}/stop/', status_code=status.HTTP_204_NO_CONTENT)
async def stop_bot(
    service_id: int, bot: ValidBot, background_tasks: BackgroundTasks
) -> None:
    await bot.stop()


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
