from dotenv import load_dotenv
from yarl import URL

from pathlib import Path
from secrets import token_hex
from typing import Final
import os

load_dotenv()


DEBUG: Final[bool] = os.getenv('DEBUG', 'True') == 'True'

SELF_URL: Final[URL] = URL(os.environ['SELF_URL'])
SELF_TOKEN: Final[str] = os.environ['SELF_TOKEN']
TELEGRAM_TOKEN: Final[str] = token_hex(32)

SERVICE_URL: Final[URL] = URL(os.environ['SERVICE_URL'])
SERVICE_UNIX_SOCK: Final[Path | None] = (
	Path(path) if (path := os.getenv('SERVICE_UNIX_SOCK')) else None
)
SERVICE_TOKEN: Final[str] = os.environ['SERVICE_TOKEN']
