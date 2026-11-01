from telegram import Update
from telegram.exceptions import BadRequestError
from telegram.models import Chat, Message, User

from service import Action, ActionMessageDeletionTarget, Connection

from ..context import Context
from ..storage import ChatStorageData, Storage
from .base import BaseHandler

from contextlib import suppress


class ActionHandler(BaseHandler[Action]):
    async def handle(
        self, update: Update, action: Action, context: Context
    ) -> list[Connection] | None:
        if action.message_deletion:
            chat: Chat | None = update.effective_chat

            if not chat:
                return None

            if (
                action.message_deletion.target
                == ActionMessageDeletionTarget.USER_MESSAGE
            ):
                message: Message | None = update.effective_message

                if not message:
                    return None

                message_user: User | None = message.user

                if not message_user or message_user.id == self._bot.telegram_id:
                    return None

                with suppress(BadRequestError):
                    await self._bot.telegram.delete_message(chat.id, message.message_id)
            elif (
                action.message_deletion.target
                == ActionMessageDeletionTarget.LAST_BOT_MESSAGES
            ):
                chat_storage: Storage[ChatStorageData] | None = context.chat_storage

                if not chat_storage:
                    return None

                async with chat_storage.transaction() as storage_data:
                    last_bot_message_ids: list[int] = (
                        storage_data.last_bot_message_ids.copy()
                    )
                    storage_data.last_bot_message_ids.clear()

                if last_bot_message_ids:
                    with suppress(BadRequestError):
                        await self._bot.telegram.delete_messages(
                            chat.id, last_bot_message_ids
                        )
            else:
                return None  # type: ignore [unreachable]
        else:
            return None

        return action.source_connections
