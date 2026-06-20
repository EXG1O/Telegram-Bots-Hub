from pydantic import BaseModel
import msgspec

from service.models import Trigger


class BotStartupData(BaseModel):
    token: str
    webhook_url: str


class StartBotsItemData(BotStartupData):
    id: int


class StartBotData(BotStartupData):
    pass


class RestartBotData(BotStartupData):
    pass


class BotWebhookTrigger(msgspec.Struct):
    trigger: Trigger
    trigger_has_target_connections: bool
    payload: str
