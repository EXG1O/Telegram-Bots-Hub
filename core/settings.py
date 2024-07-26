from dotenv import load_dotenv

from typing import Final
import os

load_dotenv()


DEBUG: Final[bool] = os.getenv('DEBUG', 'True') == 'True'

TOKEN: Final[str] = os.environ['TOKEN']

SERVICE_URL: Final[str] = os.environ['SERVICE_URL']
SERVICE_TOKEN: Final[str] = os.environ['SERVICE_TOKEN']
