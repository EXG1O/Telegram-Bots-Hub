from telegram.models import InputMedia

from typing import Literal, TypedDict


class Media(TypedDict):
    photo: list[InputMedia]
    document: list[InputMedia]
    video: list[InputMedia]
    audio: list[InputMedia]


MediaType = Literal['photo', 'document', 'video', 'audio']
MediaValue = list[InputMedia]
