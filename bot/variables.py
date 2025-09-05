from telegram import Message, User

from service.models import DatabaseRecord, Variable

from .utils import process_html_text

from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from ..bot import Bot
else:
    Bot = Any


class Variables:
    def __init__(
        self, bot: Bot, user: User | None = None, message: Message | None = None
    ):
        self.bot = bot
        self.user = user
        self.message = message
        self.store: dict[str, Any] = {
            'BOT_NAME': bot.telegram.bot.full_name,
            'BOT_USERNAME': bot.telegram.bot.username,
        }

        if user:
            self.store.update(
                {
                    'USER_ID': user.id,
                    'USER_USERNAME': user.username,
                    'USER_FIRST_NAME': user.first_name,
                    'USER_LAST_NAME': user.last_name,
                    'USER_FULL_NAME': user.full_name,
                    'USER_LANGUAGE_CODE': user.language_code,
                }
            )
        if message:
            self.store.update(
                {
                    'USER_MESSAGE_ID': message.message_id,
                    'USER_MESSAGE_TEXT': message.text,
                    'USER_MESSAGE_DATE': message.date,
                }
            )

    async def _get_self_variable(self, name: str) -> str | None:
        variables: list[Variable] = await self.bot.service_api.get_variables(name=name)
        return process_html_text(variables[0].value) if variables else None

    async def _get_database_record(self, path: str) -> Any | None:
        records: list[DatabaseRecord] = await self.bot.service_api.get_database_records(
            has_data_path=path
        )
        return self._resolve_data_path(records[0].data, path) if records else None

    def _resolve_data_path(self, data: Any, path: str) -> Any | None:
        try:
            for part in path.split('.'):
                data = data[int(part) if part.isdigit() else part]
            return data
        except (TypeError, KeyError, IndexError):
            return None

    async def get(self, key: str) -> Any | None:
        prefix, _, nested_key = key.partition('.')

        if prefix == 'SELF':
            return await self._get_self_variable(nested_key)
        elif prefix == 'DATABASE':
            return await self._get_database_record(nested_key)
        elif (
            nested_key
            and (value := self.store.get(prefix))
            and isinstance(value, dict | list | tuple | set)
        ):
            return self._resolve_data_path(value, nested_key)

        return self.store.get(key)

    def add(self, key: str, value: Any) -> None:
        self.store[key] = value

    def __copy__(self) -> Self:
        obj = self.__class__(self.bot, self.user, self.message)
        obj.store = self.store.copy()
        return obj
