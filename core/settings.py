from dotenv import load_dotenv
from yarl import URL

from secrets import token_hex
from typing import Final
import os

load_dotenv()


DEBUG: Final[bool] = os.getenv('DEBUG', 'True') == 'True'

SELF_URL: Final[URL] = URL(os.environ['SELF_URL'])
SELF_TOKEN: Final[str] = os.environ['SELF_TOKEN']
SELF_TELEGRAM_TOKEN: Final[str] = token_hex(32)

SERVICE_URL: Final[URL] = URL(os.environ['SERVICE_URL'])
SERVICE_TOKEN: Final[str] = os.environ['SERVICE_TOKEN']
