from pydantic import BaseModel


class BotStartupData(BaseModel):
    token: str
    webhook_url: str


class StartBotsItemData(BotStartupData):
    id: int


class StartBotData(BotStartupData):
    pass


class RestartBotData(BotStartupData):
    pass
