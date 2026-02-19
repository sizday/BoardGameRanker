print("🚀 STARTING WSGI.PY", flush=True)

from fastapi import FastAPI, Request
import logging
from typing import List, Optional, Callable
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.infrastructure.db import get_db
from app.infrastructure.repositories import replace_all_from_table
from app.services.translation import translate_game_descriptions_background

logger = logging.getLogger(__name__)

app = FastAPI(title="Board Game Ranker API")

print("✅ FASTAPI APP CREATED", flush=True)

class ImportTableRequest(BaseModel):
    rows: List[dict]
    is_forced_update: bool = False

class ImportTableResponse(BaseModel):
    status: str
    games_imported: int = 0
    message: str = ""

@app.post("/api/import-table")
async def import_table(request_data: dict):
    print("🎯 IMPORT-TABLE ENDPOINT CALLED!", flush=True)
    print(f"🔍 REQUEST_DATA TYPE: {type(request_data)}", flush=True)
    print(f"🔍 REQUEST_DATA: {request_data}", flush=True)
    try:
        """Import games data from table to database."""
        rows = request_data.get('rows', [])
        print(f"📝 REQUEST: {len(rows)} rows", flush=True)

        if rows:
            sample_ratings = rows[0].get('ratings', {})
            print(f"📊 SAMPLE RATINGS: {list(sample_ratings.keys())}", flush=True)

        print("🔄 CALLING replace_all_from_table...", flush=True)
        from app.infrastructure.db import get_db
        from sqlalchemy.orm import Session
        db: Session = next(get_db())
        games_imported = replace_all_from_table(
            session=db,
            rows=rows,
            is_forced_update=False,
            progress_callback=None,
        )
        print(f"✅ replace_all_from_table returned: {games_imported}", flush=True)

        return {
            "status": "success",
            "games_imported": games_imported,
            "message": f"Successfully imported {games_imported} games"
        }

    except Exception as e:
        print(f"❌ IMPORT FAILED: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

print("✅ ENDPOINT REGISTERED", flush=True)

@app.get("/health")
def health():
    return {"status": "ok"}

# Start the server
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)