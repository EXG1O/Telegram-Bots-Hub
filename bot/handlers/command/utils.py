from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMedia,
    ReplyKeyboardMarkup,
)

from core.settings import SERVICE_URL
from service.base_models import CommandMedia
from service.enums import CommandKeyboardType
from service.models import Command, CommandKeyboardButton

from urllib.parse import unquote


async def prepare_media[IM: InputMedia, CM: CommandMedia](
    media_cls: type[IM], command_media: list[CM]
) -> list[IM]:
    return [
        media_cls(str(SERVICE_URL / unquote(url[1:])))  # type: ignore [call-arg]
        for file in sorted(command_media, key=lambda media: media.position)
        if (url := file.url or file.from_url)
    ]


async def build_keyboard(
    command: Command,
) -> ReplyKeyboardMarkup | InlineKeyboardMarkup | None:
    if not command.keyboard:
        return None

    keyboard: list[list[CommandKeyboardButton]] = []

    for button in sorted(
        command.keyboard.buttons, key=lambda btn: (btn.row, btn.position)
    ):
        while len(keyboard) <= button.row:
            keyboard.append([])

        keyboard[button.row].append(button)

    if command.keyboard.type == CommandKeyboardType.DEFAULT:
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
