from fastapi import FastAPI

from api import EXCEPTION_HANDLERS, router
from core.enums import Mode
from core.settings import MODE

app = FastAPI(
    debug=MODE == Mode.DEBUG,
    openapi_url='/openapi.json' if MODE == Mode.DEBUG else None,
    exception_handlers=EXCEPTION_HANDLERS,
)
app.include_router(router)
