from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMedia,
    InputMediaType,
    KeyboardButton,
    KeyboardButtonStyle,
    ReplyKeyboardMarkup,
)
from telegram.types import KeyboardMarkup

from core.settings import SERVICE_URL
import service

from urllib.parse import unquote


def prepare_media[CM: service.MessageMedia](
    type: InputMediaType, message_media: list[CM]
) -> list[InputMedia]:
    return [
        InputMedia(
            type=type,
            media=(
                str(SERVICE_URL / unquote(file.url[1:]))
                if file.url
                else file.from_url or ''
            ),
        )
        for file in sorted(message_media, key=lambda media: media.position)
        if file.url or file.from_url
    ]


def build_keyboard(
    message_keyboard: service.MessageKeyboard,
) -> KeyboardMarkup | None:
    keyboard: list[list[service.MessageKeyboardButton]] = []

    for button in sorted(
        message_keyboard.buttons, key=lambda btn: (btn.row, btn.position)
    ):
        while len(keyboard) <= button.row:
            keyboard.append([])

        keyboard[button.row].append(button)

    if message_keyboard.type == service.MessageKeyboardType.DEFAULT:
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text=button.text,
                        style=(
                            KeyboardButtonStyle(button.style.value)
                            if button.style
                            != service.MessageKeyboardButtonStyle.DEFAULT
                            else None
                        ),
                    )
                    for button in row
                ]
                for row in keyboard
            ],
            resize_keyboard=True,
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=button.text,
                    style=(
                        KeyboardButtonStyle(button.style.value)
                        if button.style != service.MessageKeyboardButtonStyle.DEFAULT
                        else None
                    ),
                    url=button.url,
                    callback_data=str(button.id),
                )
                for button in row
            ]
            for row in keyboard
        ]
    )
