print("🔄 ROUTES.PY STARTING", flush=True)
import logging

from fastapi import APIRouter

print("📦 IMPORTING IMPORT_TABLE", flush=True)
from app.api import import_table
print("✅ IMPORT_TABLE IMPORTED", flush=True)
# from app.api import clear_database, bgg, games, ranking  # Temporarily disabled

logger = logging.getLogger(__name__)

router = APIRouter()
print("🔧 API ROUTER CREATED", flush=True)
logger.info("API router created")

# router.include_router(ranking.router)  # Temporarily disabled
router.include_router(import_table.router)
logger.info("Import table router included")
# router.include_router(clear_database.router)  # Temporarily disabled
# router.include_router(bgg.router)  # Temporarily disabled
# router.include_router(games.router)  # Temporarily disabled

logger.debug("API routes registered")
