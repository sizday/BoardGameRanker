import logging

from fastapi import APIRouter

from app.api import ranking, import_table, clear_database, bgg, games

logger = logging.getLogger(__name__)

router = APIRouter()

router.include_router(ranking.router)
router.include_router(import_table.router)
router.include_router(clear_database.router)
router.include_router(bgg.router)
router.include_router(games.router)

logger.debug("API routes registered")
