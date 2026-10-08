from telegram import Chat, Update, User

from .storage import ChatStorageData, Storage, UserStorageData
from .variables import Variables

from typing import TYPE_CHECKING
import copy

if TYPE_CHECKING:
    from .bot import Bot


class Context:
    def __init__(self, bot: Bot, update: Update) -> None:
        chat: Chat | None = update.effective_chat
        user: User | None = update.effective_user

        self.chat_storage: Storage[ChatStorageData] | None = (
            Storage.for_chat(bot_id=bot.telegram_id, chat_id=chat.id) if chat else None
        )
        self.user_storage: Storage[UserStorageData] | None = (
            Storage.for_user(bot_id=bot.telegram_id, chat_id=chat.id, user_id=user.id)
            if chat and user
            else None
        )
        self.variables = Variables(
            bot=bot,
            chat=chat,
            user=user,
            message=update.message,
            user_storage=self.user_storage,
        )

    def copy(self) -> Context:
        context: Context = copy.copy(self)
        context.variables = self.variables.copy()
        return context
