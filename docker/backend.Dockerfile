FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Копируем весь backend (включая alembic и конфиг) внутрь контейнера
COPY backend/ /app/

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

# При старте контейнера сначала выполняем миграции Alembic,
# затем запускаем сервер приложения.
CMD ["sh", "-c", "cd /app && alembic -c alembic.ini upgrade head && python wsgi.py"]


