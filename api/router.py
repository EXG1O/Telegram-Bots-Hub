from fastapi import APIRouter

from .routes import bots

router = APIRouter()
router.include_router(bots.router)
