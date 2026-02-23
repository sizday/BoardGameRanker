"""
Утилиты для настройки логирования в приложении.
"""
import logging
import os
import sys
from typing import Optional

from app.config import config


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Настраивает логирование для всего приложения.

    :param log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                     Если не указан, используется из конфигурации или переменной окружения LOG_LEVEL.
    """
    if log_level:
        level = getattr(logging, log_level.upper(), logging.INFO)
    else:
        # Сначала проверяем переменную окружения LOG_LEVEL
        env_log_level = os.getenv("LOG_LEVEL", "").upper()
        if env_log_level and hasattr(logging, env_log_level):
            level = getattr(logging, env_log_level)
        else:
            # Fallback к старой логике
            level = logging.DEBUG if config.DEBUG else logging.INFO
    
    # Формат логов
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Настройка базового логирования
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    
    # Настройка уровней для внешних библиотек
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Настройка уровней для наших модулей
    logging.getLogger("app").setLevel(level)
    logging.getLogger("app.services.bgg").setLevel(level)
    logging.getLogger("app.api.bgg").setLevel(level)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {level}")


def get_logger(name: str) -> logging.Logger:
    """
    Получить логгер с указанным именем.
    
    :param name: Имя логгера (обычно __name__)
    :return: Настроенный логгер
    """
    return logging.getLogger(name)

