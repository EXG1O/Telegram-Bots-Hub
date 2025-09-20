from telegram import Update

from aiohttp import (
    ClientError,
    ClientSession,
    ClientTimeout,
    DummyCookieJar,
    TCPConnector,
)
from multidict import CIMultiDict

from service.models import APIRequest, Connection

from ...utils import replace_text_variables
from ...variables import Variables
from ..base import BaseHandler
from .resolver import SafeResolver
from .utils import get_safe_headers, parse_response_body

import json


class APIRequestHandler(BaseHandler[APIRequest]):
    async def handle(
        self, update: Update, api_request: APIRequest, variables: Variables
    ) -> list[Connection] | None:
        headers: CIMultiDict[str] = get_safe_headers(api_request.headers)
        data: str | None = None

        if api_request.body:
            data = await replace_text_variables(json.dumps(api_request.body), variables)
            headers['Content-Type'] = 'application/json'

        try:
            async with ClientSession(
                connector=TCPConnector(resolver=SafeResolver()),
                headers={
                    'User-Agent': (
                        'ConstructorTelegramBots '
                        f'(constructor.exg1o.org; bot_id={self.bot.telegram.id})'
                    )
                },
                skip_auto_headers=['User-Agent'],
                cookie_jar=DummyCookieJar(),
                timeout=ClientTimeout(6),
            ) as session:
                async with session.request(
                    api_request.method.value,
                    api_request.url,
                    headers=headers,
                    data=data,
                    allow_redirects=False,
                ) as response:
                    variables.add(
                        'API_RESPONSE',
                        parse_response_body(await response.content.read(2048)),
                    )
        except ClientError:
            return None

        return api_request.source_connections
