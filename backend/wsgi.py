from fastapi import FastAPI

# Настраиваем логирование перед импортом других модулей
from app.utils.logging import setup_logging
setup_logging()

app = FastAPI(title="Board Game Ranker API")

# Подключаем API роутеры
@app.get("/health")
def health():
    return {"status": "ok"}
from app.api.routes import router as api_router
app.include_router(api_router, prefix="/api")

# Start the server
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)