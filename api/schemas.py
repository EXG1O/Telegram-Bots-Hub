from pydantic import BaseModel


class StartBotRequest(BaseModel):
	bot_token: str
