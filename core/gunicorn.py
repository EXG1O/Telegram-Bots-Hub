from core.settings import CONTAINER_ID, LOGS_DIR

from typing import Final

worker_class: Final[str] = 'uvicorn.workers.UvicornWorker'
workers: Final[int] = 1
threads: Final[int] = 1

bind: Final[str] = f'unix:/app/sockets/{CONTAINER_ID}.sock'

capture_output: Final[bool] = True
accesslog: Final[str] = str(LOGS_DIR / 'gunicorn_info.log')
errorlog: Final[str] = str(LOGS_DIR / 'gunicorn_info.log')
