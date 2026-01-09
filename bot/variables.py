from telegram import Chat, Message, User

from service.models import DatabaseRecord, Variable

from .utils.html import process_html_text

from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from ..bot import Bot
else:
    Bot = Any


class Variables:
    def __init__(
        self,
        bot: Bot,
        chat: Chat | None = None,
        user: User | None = None,
        message: Message | None = None,
    ):
        self.bot = bot
        self.chat = chat
        self.user = user
        self.message = message

        self.store: dict[str, Any] = {}
        self.system_store: dict[str, Any] = {
            'BOT_ID': bot.telegram.bot.id,
            'BOT_NAME': bot.telegram.bot.name,
            'BOT_USERNAME': bot.telegram.bot.username,
            'BOT_FULL_NAME': bot.telegram.bot.full_name,
            'BOT_LINK': bot.telegram.bot.link,
        }

        if chat:
            self.system_store.update(
                {
                    'CHAT_ID': chat.id,
                    'CHAT_TYPE': chat.type,
                    'CHAT_NAME': chat.effective_name,
                    'CHAT_USERNAME': chat.username,
                    'CHAT_FULL_NAME': chat.full_name,
                    'CHAT_LINK': chat.link,
                }
            )
        if user:
            self.system_store.update(
                {
                    'USER_ID': user.id,
                    'USER_IS_BOT': user.is_bot,
                    'USER_IS_PREMIUM': user.is_premium,
                    'USER_NAME': user.name,
                    'USER_USERNAME': user.username,
                    'USER_FIRST_NAME': user.first_name,
                    'USER_LAST_NAME': user.last_name,
                    'USER_FULL_NAME': user.full_name,
                    'USER_LANGUAGE_CODE': user.language_code,
                    'USER_LINK': user.link,
                }
            )
        if message:
            self.system_store.update(
                {
                    'USER_MESSAGE_ID': message.message_id,
                    'USER_MESSAGE_TEXT': message.text,
                    'USER_MESSAGE_DATE': message.date,
                    'USER_MESSAGE_LINK': message.link,
                }
            )

    def __copy__(self) -> Self:
        obj = self.__class__(self.bot, self.chat, self.user, self.message)
        obj.store = self.store.copy()
        return obj

    def _resolve_value(self, data: Any, path: str) -> Any | None:
        try:
            for part in path.split('.'):
                data = data[int(part) if part.isdigit() else part]
            return data
        except (TypeError, KeyError, IndexError):
            return None

    async def _resolve_user_value(
        self, name: str, path: str | None = None
    ) -> Any | None:
        variables: list[Variable] = await self.bot.service_api.get_variables(name=name)

        if not variables:
            return None

        if len(variables) > 1:
            result: list[str] = [
                process_html_text(variable.value) for variable in variables
            ]
            return self._resolve_value(result, path) if path else result

        return process_html_text(variables[0].value)

    async def _resolve_database_value(self, path: str) -> Any | None:
        records: list[DatabaseRecord] = await self.bot.service_api.get_database_records(
            has_data_path=path
        )
        return self._resolve_value(records[0].data, path) if records else None

    async def get(self, key: str) -> Any | None:
        prefix, _, nested_key = key.partition('.')

        if prefix == 'SYSTEM':
            return self.system_store.get(nested_key)
        elif prefix == 'USER':
            return await self._resolve_user_value(nested_key)
        elif prefix == 'DATABASE':
            return await self._resolve_database_value(nested_key)
        elif (
            nested_key
            and (value := self.store.get(prefix))
            and isinstance(value, dict | list | tuple | set)
        ):
            return self._resolve_value(value, nested_key)

        return self.store.get(key)

    def add(self, key: str, value: Any) -> None:
        self.store[key] = value
