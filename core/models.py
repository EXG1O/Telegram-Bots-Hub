from pydantic import BaseModel


class StartBotRequest(BaseModel):
	bot_token: str

class RestartBotRequest(StartBotRequest):
	pass

class SendMessageRequest(BaseModel):
	message_text: str