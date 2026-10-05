from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from bot import Bot

bots: Final[dict[int, Bot]] = {}
