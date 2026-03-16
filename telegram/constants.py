from enum import IntEnum
from typing import Final

PARSE_MODE: Final[str] = 'HTML'


class MediaGroupLimit(IntEnum):
    MIN_MEDIA_LENGTH = 2
    MAX_MEDIA_LENGTH = 10
