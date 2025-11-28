from telegram import Update

from aiohttp import (
    ClientError,
    ClientSession,
    ClientTimeout,
    DummyCookieJar,
    TCPConnector,
)

from service.models import APIRequest, Connection

from ...storage import EventStorage
from ...utils import replace_data_variables
from ...variables import Variables
from ..base import BaseHandler
from .resolver import SafeResolver
from .utils import get_safe_headers, parse_response_body


class APIRequestHandler(BaseHandler[APIRequest]):
    async def handle(
        self,
        update: Update,
        api_request: APIRequest,
        event_storage: EventStorage,
        variables: Variables,
    ) -> list[Connection] | None:
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
                    headers=get_safe_headers(api_request.headers),
                    json=await replace_data_variables(
                        api_request.body, variables, deserialize=True
                    ),
                    allow_redirects=False,
                ) as response:
                    variables.add(
                        'API_RESPONSE',
                        parse_response_body(await response.content.read(2048)),
                    )
        except ClientError:
            return None

        return api_request.source_connections
