from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMedia,
    ReplyKeyboardMarkup,
)

from core.settings import SERVICE_URL
from service.base_models import MessageMedia
from service.enums import MessageKeyboardType
from service.models import MessageKeyboard, MessageKeyboardButton

from urllib.parse import unquote


async def prepare_media[IM: InputMedia, CM: MessageMedia](
    media_cls: type[IM], message_media: list[CM]
) -> list[IM]:
    return [
        media_cls(str(SERVICE_URL / unquote(url[1:])))  # type: ignore [call-arg]
        for file in sorted(message_media, key=lambda media: media.position)
        if (url := file.url or file.from_url)
    ]


async def build_keyboard(
    message_keyboard: MessageKeyboard,
) -> ReplyKeyboardMarkup | InlineKeyboardMarkup | None:
    keyboard: list[list[MessageKeyboardButton]] = []

    for button in sorted(
        message_keyboard.buttons, key=lambda btn: (btn.row, btn.position)
    ):
        while len(keyboard) <= button.row:
            keyboard.append([])

        keyboard[button.row].append(button)

    if message_keyboard.type == MessageKeyboardType.DEFAULT:
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
