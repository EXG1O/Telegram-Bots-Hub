from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from aiogram.utils.token import TokenValidationError

import uvicorn

from core import dispatcher, settings
from core.exceptions import (
	BotAlreadyEnabledError,
	NoSpaceForStartBotError,
	NotFoundBotError,
)
from core.routes import bots

from typing import Any

app = FastAPI(title='Telegram Bots Hub')
app.include_router(bots.router)


@app.exception_handler(NoSpaceForStartBotError)
def no_space_to_start_bot_exception_handler(
	request: Request, exception: NoSpaceForStartBotError
) -> JSONResponse:
	return JSONResponse({'code': 'no_space_to_start_bot'}, 400)


@app.exception_handler(NotFoundBotError)
def not_found_bot_exception_handler(
	request: Request, exception: NotFoundBotError
) -> JSONResponse:
	return JSONResponse({'code': 'not_found_bot'}, 400)


@app.exception_handler(BotAlreadyEnabledError)
def bot_already_enabled_exception_handler(
	request: Request, exception: NoSpaceForStartBotError
) -> JSONResponse:
	return JSONResponse({'code': 'bot_already_enabled'}, 400)


@app.exception_handler(TokenValidationError)
def token_validation_error_exception_handler(
	request: Request, exception: TokenValidationError
) -> JSONResponse:
	return JSONResponse({'code': 'invalid_bot_token'}, 400)


@app.get('/')
async def root() -> dict[str, Any]:
	return {
		'token': settings.service_token,
		'max_bots_limit': settings.max_bots_limit,
		'bots_count': len(dispatcher.bots),
	}


if __name__ == '__main__':
	uvicorn.run('main:app', port=settings.port)
