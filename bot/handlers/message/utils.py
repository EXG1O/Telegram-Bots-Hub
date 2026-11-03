from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMedia,
    InputMediaType,
    KeyboardButton,
    KeyboardButtonStyle,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.types import KeyboardMarkup

from core.settings import SERVICE_URL
import service

from ...utils.variables import replace_text_variables
from ...variables import Variables

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


async def build_keyboard(
    message_keyboard: service.MessageKeyboard, variables: Variables
) -> KeyboardMarkup | None:
    if message_keyboard.type == service.MessageKeyboardType.PAYMENT:
        return None

    rows: list[list[service.MessageKeyboardButton]] = []

    for button in sorted(
        message_keyboard.buttons, key=lambda btn: (btn.row, btn.position)
    ):
        while len(rows) <= button.row:
            rows.append([])

        rows[button.row].append(button)

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
                for row in rows
            ],
            is_persistent=message_keyboard.is_persistent,
            resize_keyboard=message_keyboard.is_compact,
            one_time_keyboard=message_keyboard.hide_on_click,
            input_field_placeholder=(
                await replace_text_variables(text, variables)
                if (text := message_keyboard.input_placeholder)
                else None
            ),
        )

    if message_keyboard.type == service.MessageKeyboardType.INLINE:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=button.text,
                        style=(
                            KeyboardButtonStyle(button.style.value)
                            if button.style
                            != service.MessageKeyboardButtonStyle.DEFAULT
                            else None
                        ),
                        url=button.url,
                        callback_data=str(button.id),
                    )
                    for button in row
                ]
                for row in rows
            ]
        )

    if message_keyboard.type == service.MessageKeyboardType.REMOVAL:
        return ReplyKeyboardRemove(remove_keyboard=True)

    return None  # type: ignore [unreachable]
