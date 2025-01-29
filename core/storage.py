from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from bot import Bot
else:
    Bot = Any

bots: Final[dict[int, Bot]] = {}
