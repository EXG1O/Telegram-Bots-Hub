from telegram import (
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
)

from typing import Literal, TypedDict


class Media(TypedDict):
    photo: list[InputMediaPhoto]
    document: list[InputMediaDocument]
    video: list[InputMediaVideo]
    audio: list[InputMediaAudio]


MediaType = Literal['photo', 'document', 'video', 'audio']
MediaValue = list[
    InputMediaPhoto | InputMediaDocument | InputMediaVideo | InputMediaAudio
]
