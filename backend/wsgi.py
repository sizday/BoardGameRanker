from fastapi import FastAPI
from uvicorn import run

from app.api.routes import router as api_router
from app.infrastructure.db import init_db

app = FastAPI(
    title="Board Game Ranker API",
    description="API for ranking board games",
    version="1.0.0",
)

# Initialize database (создаёт таблицы, если их нет)
# Миграции Alembic уже применены в start.sh, так что это просто подстраховка
try:
    init_db()
except Exception as e:
    # Если таблицы уже созданы через миграции, это нормально
    print(f"Note: Database initialization: {e}")

# Include API router
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8000)


