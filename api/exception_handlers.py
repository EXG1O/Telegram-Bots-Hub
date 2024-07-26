from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

from aiogram.utils.token import TokenValidationError

from core.exceptions import BotAlreadyEnabledError, NotFoundBotError

from collections.abc import Callable, Coroutine
from typing import Any


async def not_found_bot_exception_handler(
	request: Request, exception: NotFoundBotError
) -> JSONResponse:
	return JSONResponse(
		{
			'code': 'not_found_bot',
			'detail': 'The bot was not found, because it is not started here.',
		},
		status.HTTP_400_BAD_REQUEST,
	)


async def bot_already_enabled_exception_handler(
	request: Request, exception: BotAlreadyEnabledError
) -> JSONResponse:
	return JSONResponse(
		{
			'code': 'bot_already_enabled',
			'detail': 'The bot is already enabled and working success.',
		},
		status.HTTP_400_BAD_REQUEST,
	)


async def token_validation_error_exception_handler(
	request: Request, exception: TokenValidationError
) -> JSONResponse:
	return JSONResponse(
		{
			'code': 'invalid_bot_token',
			'detail': 'The API token is invalid for the bot.',
		},
		status.HTTP_400_BAD_REQUEST,
	)


EXCEPTION_HANDLERS: dict[
	int | type[Exception], Callable[[Request, Any], Coroutine[Any, Any, Response]]
] = {
	NotFoundBotError: not_found_bot_exception_handler,
	BotAlreadyEnabledError: bot_already_enabled_exception_handler,
	TokenValidationError: token_validation_error_exception_handler,
}
