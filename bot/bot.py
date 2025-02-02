from telegram import (
    BotCommand,
    CallbackQuery,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMedia,
    InputMediaDocument,
    InputMediaPhoto,
    MaybeInaccessibleMessage,
    Message,
    ReplyKeyboardMarkup,
    Update,
    User,
)
from telegram._utils.types import ReplyMarkup
from telegram.constants import MediaGroupLimit, ParseMode, UpdateType
from telegram.error import InvalidToken
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ContextTypes,
    Defaults,
    MessageHandler,
    filters,
)
import aiohttp

from core.settings import SELF_URL, SERVICE_URL, TELEGRAM_TOKEN
from core.storage import bots
from service import API
import service.base_models
import service.enums
import service.models

from .data import Media, MediaType, MediaValue
from .request import ResilientHTTPXRequest
from .utils import html, replace_text_variables

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar, cast
from urllib.parse import unquote
import asyncio
import json
import re
import string

IM = TypeVar('IM', bound=InputMedia)
CM = TypeVar('CM', bound=service.base_models.CommandMedia)


class Bot:
    def __init__(self, service_id: int, token: str):
        self.app = (
            ApplicationBuilder()
            .token(token)
            .defaults(Defaults(parse_mode=ParseMode.HTML))
            .request(ResilientHTTPXRequest(read_timeout=20))
            .updater(None)
            .build()
        )
        self.bot = self.app.bot

        self.service_id = service_id
        self.service_api = API(service_id)
        self.last_messages: dict[int, list[Message]] = {}
        self.background_tasks: dict[int, datetime] = {}

    async def generate_variables(
        self,
        user: User | None = None,
        message: Message | MaybeInaccessibleMessage | None = None,
    ) -> dict[str, Any]:
        bot: User = self.bot.bot
        variables: dict[str, Any] = {
            'BOT_NAME': bot.full_name,
            'BOT_USERNAME': bot.username,
        }

        if user:
            variables.update(
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
            variables.update(
                {
                    'USER_MESSAGE_ID': message.message_id,
                    'USER_MESSAGE_TEXT': message.text
                    if isinstance(message, Message)
                    else '',
                    'USER_MESSAGE_DATE': message.date,
                }
            )

        variables.update(
            {
                variable.name: await html.process_text(variable.value)
                for variable in await self.service_api.get_variables()
            }
        )

        return variables

    async def _send_api_request(
        self, api_request: service.base_models.APIRequest
    ) -> list[Any] | dict[Any, Any] | str:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    api_request.method.value,
                    api_request.url,
                    headers=api_request.headers,
                    json=api_request.body,
                ) as response:
                    try:
                        return await response.json()  # type: ignore [no-any-return]
                    except aiohttp.ContentTypeError:
                        return await response.text()
        except aiohttp.ClientError:
            return {}

    async def _parse_condition_value(self, value: str) -> str | int | float:
        try:
            if value.isdigit():
                return int(value)
            return float(value)
        except ValueError:
            return value

    async def _validate_condition(
        self, condition: service.models.Condition, variables: dict[str, Any]
    ) -> bool:
        result: bool | None = None

        for part in condition.parts:
            current_result: bool = False
            first_value = await self._parse_condition_value(
                await replace_text_variables(part.first_value, variables)
            )
            second_value = await self._parse_condition_value(
                await replace_text_variables(part.second_value, variables)
            )

            match part.operator:
                case service.enums.ConditionPartOperator.EQUAL:
                    current_result = first_value == second_value
                case service.enums.ConditionPartOperator.NOT_EQUAL:
                    current_result = first_value != second_value
                case service.enums.ConditionPartOperator.GREATER:
                    current_result = first_value > second_value  # type: ignore [operator]
                case service.enums.ConditionPartOperator.GREATER_OR_EQUAL:
                    current_result = first_value >= second_value  # type: ignore [operator]
                case service.enums.ConditionPartOperator.LESS:
                    current_result = first_value < second_value  # type: ignore [operator]
                case service.enums.ConditionPartOperator.LESS_OR_EQUAL:
                    current_result = first_value <= second_value  # type: ignore [operator]

            if result is None:
                result = current_result
            else:
                match part.next_part_operator:
                    case service.enums.ConditionPartNextPartOperator.AND:
                        result = result and current_result
                    case service.enums.ConditionPartNextPartOperator.OR:
                        result = result or current_result

        return bool(result)

    async def process_connections(
        self, connections: list[service.models.Connection], variables: dict[str, Any]
    ) -> service.models.Command | None:
        for connection in sorted(
            connections,
            key=lambda conn: conn.target_object_type
            != service.enums.ConnectionTargetObjectType.COMMAND,
        ):
            if (
                connection.target_object_type
                == service.enums.ConnectionTargetObjectType.CONDITION
            ):
                condition: service.models.Condition = (
                    await self.service_api.get_condition(connection.target_object_id)
                )

                if not await self._validate_condition(condition, variables):
                    return None

                if condition.source_connections:
                    return await self.process_connections(
                        condition.source_connections, variables
                    )
            elif (
                connection.target_object_type
                == service.enums.ConnectionTargetObjectType.COMMAND
            ):
                return await self.service_api.get_command(connection.target_object_id)

        return None

    async def get_command(
        self,
        message: Message | MaybeInaccessibleMessage,
        user: User,
        text: str | None = None,
        button_id: int | None = None,
    ) -> service.models.Command | None:
        if text and (trigger := await self.service_api.get_command_triggers(text=text)):
            return await self.service_api.get_command(trigger[0].command_id)

        if buttons := await self.service_api.get_commands_keyboard_buttons(
            id=button_id, text=text
        ):
            variables: dict[str, Any] = await self.generate_variables(user, message)

            return await self.process_connections(
                buttons[0].source_connections, variables
            )

        return None

    async def _build_keyboard(
        self, command: service.models.Command
    ) -> ReplyKeyboardMarkup | InlineKeyboardMarkup | None:
        if not command.keyboard:
            return None

        keyboard: list[list[service.models.CommandKeyboardButton]] = []

        for button in sorted(
            command.keyboard.buttons, key=lambda btn: (btn.row, btn.position)
        ):
            while len(keyboard) <= button.row:
                keyboard.append([])

            keyboard[button.row].append(button)

        if command.keyboard.type == service.enums.CommandKeyboardType.DEFAULT:
            return ReplyKeyboardMarkup(
                [[button.text for button in row] for row in keyboard],
                resize_keyboard=True,
            )

        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        button.text, url=button.url, callback_data=str(button.id)
                    )
                    for button in row
                ]
                for row in keyboard
            ]
        )

    async def send_media_group(
        self,
        chat_id: int,
        media: Media,
        message_text: str,
        reply_to_message_id: int | None = None,
        keyboard: ReplyMarkup | None = None,
    ) -> list[Message]:
        kwargs: dict[str, Any] = {
            'chat_id': chat_id,
            'reply_to_message_id': reply_to_message_id,
        }

        if not any(media.values()):
            return [
                await self.bot.send_message(
                    text=message_text, reply_markup=keyboard, **kwargs
                )
            ]

        new_bot_messages: list[Message] = []
        processed_types: set[MediaType] = set()
        text_attached: bool = False

        for type, files in media.items():
            type = cast(MediaType, type)
            files = cast(MediaValue, files)

            if not files:
                continue

            processed_types.add(type)

            if len(files) < MediaGroupLimit.MIN_MEDIA_LENGTH:
                should_attach_text: bool = not any(
                    len(media[other_type]) > 0  # type: ignore [literal-required]
                    for other_type in media
                    if other_type not in processed_types
                )

                send_file: Callable[..., Awaitable[Message]] = getattr(
                    self.bot, f'send_{type}'
                )

                custom_kwargs: dict[str, Any] = kwargs.copy()
                custom_kwargs[type] = files[0].media

                if should_attach_text and not text_attached:
                    custom_kwargs['caption'] = message_text
                    custom_kwargs['reply_markup'] = keyboard
                    text_attached = True

                new_bot_messages.append(await send_file(**custom_kwargs))
                continue

            for start_index in range(0, len(files), MediaGroupLimit.MAX_MEDIA_LENGTH):
                new_bot_messages.extend(
                    await self.bot.send_media_group(
                        media=files[
                            start_index : start_index + MediaGroupLimit.MAX_MEDIA_LENGTH
                        ],
                        **kwargs,
                    )
                )

        if not text_attached:
            new_bot_messages.append(
                await self.bot.send_message(
                    text=message_text, reply_markup=keyboard, **kwargs
                )
            )

        return new_bot_messages

    async def prepare_media(
        self, media_cls: type[IM], command_media: list[CM]
    ) -> list[IM]:
        return [
            media_cls(str(SERVICE_URL / unquote(url[1:])))  # type: ignore [call-arg]
            for file in command_media
            if (url := file.url or file.from_url)
        ]

    async def perform_command(
        self,
        command: service.models.Command,
        user_is_bot: bool,
        chat_id: int,
        message_id: int | None = None,
        variables: dict[str, Any] | None = None,
    ) -> None:
        if variables is None:
            variables = await self.generate_variables()

        if command.api_request:
            variables['API_RESPONSE'] = await self._send_api_request(
                command.api_request
            )

        if command.database_record:
            await self.service_api.create_database_record(
                data={
                    'data': await replace_text_variables(
                        json.dumps(command.database_record.data), variables
                    )
                }
            )

        message_text: str = await replace_text_variables(
            await html.process_text(command.message.text), variables
        )
        keyboard: ReplyMarkup | None = await self._build_keyboard(command)

        if (
            not command.settings.is_send_as_new_message
            and chat_id in self.last_messages
        ):
            await self.bot.delete_messages(
                chat_id,
                [last_message.id for last_message in self.last_messages.pop(chat_id)],
            )

        self.last_messages[chat_id] = await self.send_media_group(
            chat_id=chat_id,
            reply_to_message_id=message_id
            if command.settings.is_reply_to_user_message
            else None,
            media=Media(
                photo=await self.prepare_media(InputMediaPhoto, command.images),
                document=await self.prepare_media(InputMediaDocument, command.files),
                video=[],
                audio=[],
            ),
            message_text=message_text,
            keyboard=keyboard,
        )

        if message_id and not user_is_bot and command.settings.is_delete_user_message:
            await self.bot.delete_message(chat_id, message_id)

    async def handle_update(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        callback_query: CallbackQuery | None = update.callback_query
        message: Message | MaybeInaccessibleMessage | None = (
            callback_query.message if callback_query else update.message
        )

        if not message:
            return None

        chat: Chat | None = update.effective_chat
        user: User | None = update.effective_user

        if not chat or not user:
            return None

        command: service.models.Command | None = await self.get_command(
            message=message,
            user=user,
            text=(update.message.text if update.message else None),
            button_id=(
                int(update.callback_query.data)
                if update.callback_query and update.callback_query.data
                else None
            ),
        )

        if not command:
            return None

        variables: dict[str, Any] = await self.generate_variables(user, message)

        await self.perform_command(
            command,
            user_is_bot=user.is_bot,
            chat_id=chat.id,
            message_id=message.message_id,
            variables=variables,
        )

    async def feed_webhook_update(self, update: Update) -> None:
        user: User | None = update.effective_user

        if not user:
            return None

        service_bot: service.models.Bot = await self.service_api.get_bot()
        service_user: service.models.User = await self.service_api.create_user(
            {'telegram_id': user.id, 'full_name': user.full_name}
        )

        match (
            service_bot.is_private,
            service_user.is_allowed,
            service_user.is_blocked,
        ):
            case (True, True, False) | (False, _, False):
                await self.app.update_queue.put(update)

    async def run_scheduled_background_tasks(self) -> None:
        while self.app.running:
            current_datetime: datetime = datetime.now(UTC)
            variables: dict[str, Any] = await self.generate_variables()
            users: list[service.models.User] = await self.service_api.get_users()

            for background_task in await self.service_api.get_background_tasks():
                if (
                    self.background_tasks.setdefault(
                        background_task.id, current_datetime
                    )
                    + timedelta(days=background_task.interval.value)
                ) > current_datetime:
                    continue

                if background_task.api_request:
                    variables['API_RESPONSE'] = await self._send_api_request(
                        background_task.api_request
                    )

                command: service.models.Command | None = await self.process_connections(
                    background_task.source_connections, variables
                )

                if not command:
                    continue

                for user in users:
                    variables.update(
                        {'USER_ID': user.telegram_id, 'USER_FULL_NAME': user.full_name}
                    )

                    await self.perform_command(
                        command,
                        user_is_bot=False,
                        chat_id=user.telegram_id,
                        variables=variables,
                    )

                if background_task.api_request:
                    del variables['API_RESPONSE']

                self.background_tasks[background_task.id] = current_datetime

            await asyncio.sleep(21600)

    async def monitor_bot_token(self) -> None:
        try:
            while self.app.running:
                await asyncio.sleep(86400)
                await self.bot.get_me()
        except InvalidToken:
            await self.stop()

    async def start(self) -> None:
        await self.bot.set_my_commands(
            [
                BotCommand(
                    command=re.sub(f'[{string.punctuation}]', '', trigger.text),
                    description=trigger.description,
                )
                for trigger in await self.service_api.get_command_triggers()
                if trigger.description
            ]
        )

        self.app.add_handler(MessageHandler(filters.TEXT, self.handle_update))
        self.app.add_handler(CallbackQueryHandler(self.handle_update))

        await self.bot.set_webhook(
            f'{SELF_URL}/bots/{self.service_id}/webhook/',
            allowed_updates=[UpdateType.MESSAGE, UpdateType.CALLBACK_QUERY],
            secret_token=TELEGRAM_TOKEN,
        )

        await self.app.initialize()
        await self.app.start()

        asyncio.create_task(self.monitor_bot_token())
        asyncio.create_task(self.run_scheduled_background_tasks())

    async def stop(self) -> None:
        try:
            await self.bot.delete_webhook()
        finally:
            del bots[self.service_id]

            await self.app.stop()
            await self.app.shutdown()
            await self.service_api.session.close()
