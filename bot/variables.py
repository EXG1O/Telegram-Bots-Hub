from telegram.models import Chat, Message, User

from service.models import DatabaseRecord, Variable

from .utils.html import process_html_text

from typing import TYPE_CHECKING, Any, Self
import re

if TYPE_CHECKING:
    from ..bot import Bot
else:
    Bot = Any


VARIABLE_SEARCH_PATTERN: re.Pattern[str] = re.compile(r'\[search=([^\[\]]+)\]')


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
            'BOT_ID': bot.me.id,
            'BOT_NAME': bot.me.name,
            'BOT_USERNAME': bot.me.username,
            'BOT_FULL_NAME': bot.me.full_name,
            'BOT_LINK': bot.me.link,
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
        except TypeError, KeyError, IndexError:
            return None

    async def _resolve_user_value(self, path: str) -> Any | None:
        name, _, new_path = path.partition('.')
        final_path: str | None = new_path or None

        variables: list[Variable] = await self.bot.service.get_variables(name=name)

        if not variables:
            return None

        if len(variables) > 1:
            result: list[str] = [
                process_html_text(variable.value) for variable in variables
            ]
            return self._resolve_value(result, final_path) if final_path else result

        return process_html_text(variables[0].value)

    async def _resolve_database_value(self, path: str) -> Any | None:
        match: re.Match[str] | None = VARIABLE_SEARCH_PATTERN.match(path)
        search_value: str | None = None

        if TYPE_CHECKING:
            final_path: str | None

        if match:
            final_path = path[match.end() + 1 :] or None
            raw_search_value: str = match.group(1)
            search_value = (await self.get(raw_search_value)) or raw_search_value
        else:
            final_path = path

        records: list[DatabaseRecord] = await self.bot.service.get_database_records(
            search=search_value, has_data_path=final_path
        )

        if not records:
            return None

        if len(records) > 1:
            records_data: list[dict[str, Any] | list[Any]] = [
                record.data for record in records
            ]
            return (
                self._resolve_value(records_data, final_path)
                if final_path
                else records_data
            )

        record_data: dict[str, Any] | list[Any] = records[0].data
        return (
            self._resolve_value(record_data, final_path) if final_path else record_data
        )

    async def get(self, key: str) -> Any | None:
        prefix, _, nested_key = key.partition('.')

        if nested_key:
            if prefix == 'SYSTEM':
                return self.system_store.get(nested_key)
            elif prefix == 'USER':
                return await self._resolve_user_value(nested_key)
            elif prefix == 'DATABASE':
                return await self._resolve_database_value(nested_key)
            elif (value := self.store.get(prefix)) and isinstance(
                value, dict | list | tuple | set
            ):
                return self._resolve_value(value, nested_key)

        return self.store.get(key)

    def add(self, key: str, value: Any) -> None:
        self.store[key] = value
