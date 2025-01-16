from fastapi import FastAPI

from api.exception_handlers import EXCEPTION_HANDLERS
from api.router import router
from core import settings

app = FastAPI(
	title='Telegram Bots Hub',
	description=(
		'Microservice for managing Telegram bots within '
		'the [**Constructor Telegram Bots**](https://constructor.exg1o.org/) project.'
	),
	license_info={
		'name': 'MIT License',
		'url': 'https://github.com/EXG1O/Telegram-Bots-Hub/blob/master/LICENSE',
	},
	version='1.0.0',
	debug=settings.DEBUG,
	openapi_url='/openapi.json' if settings.DEBUG else None,
	exception_handlers=EXCEPTION_HANDLERS,
)
app.include_router(router)
