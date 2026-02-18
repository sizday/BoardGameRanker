import asyncio
import logging
from typing import Optional

from sqlalchemy.orm import Session

try:
    from googletrans import Translator
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    GOOGLETRANS_AVAILABLE = False
    logging.warning("googletrans not available, translation service will be disabled")

from app.config import config
from app.infrastructure.models import GameModel

logger = logging.getLogger(__name__)


class TranslationService:
    """
    Сервис для перевода текстов с использованием Google Translate API.
    """

    def __init__(self):
        self.translator = None
        if GOOGLETRANS_AVAILABLE:
            self.translator = Translator()
        else:
            logger.error("Translation service unavailable: googletrans not installed")

    async def translate_to_russian(self, text: str) -> Optional[str]:
        """
        Переводит текст на русский язык.

        :param text: Исходный текст на английском
        :return: Переведенный текст или None при ошибке
        """
        if not text or not text.strip():
            return None

        if not self.translator:
            logger.warning("Translation service not available")
            return None

        try:
            # Google Translate работает синхронно, но мы запускаем в executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.translator.translate(text, src='en', dest='ru')
            )

            translated_text = result.text
            logger.debug(f"Translated text ({len(text)} chars) to Russian ({len(translated_text)} chars)")
            return translated_text

        except Exception as e:
            logger.error(f"Error translating text: {e}", exc_info=True)
            return None

    async def is_available(self) -> bool:
        """Проверяет доступность сервиса перевода."""
        return self.translator is not None

    async def translate_game_descriptions_background(self, db: Session) -> None:
        """
        Фоновая задача для перевода описаний игр, у которых нет русского перевода.

        :param db: Сессия базы данных
        """
        if not self.translator:
            logger.warning("Translation service not available, skipping background translation")
            return

        try:
            # Находим игры без русского описания, но с английским
            games_to_translate = (
                db.query(GameModel)
                .filter(GameModel.description.isnot(None))
                .filter(GameModel.description_ru.is_(None))
                .filter(GameModel.description != '')
                .all()
            )

            if not games_to_translate:
                logger.info("No games found that need translation")
                return

            logger.info(f"Starting background translation for {len(games_to_translate)} games")

            # Переводим описания по одному (чтобы не перегружать API)
            for game in games_to_translate:
                try:
                    logger.debug(f"Translating description for game: {game.name}")

                    translated_text = await self.translate_to_russian(game.description)
                    if translated_text:
                        game.description_ru = translated_text
                        logger.info(f"Successfully translated description for game: {game.name}")
                    else:
                        logger.warning(f"Failed to translate description for game: {game.name}")

                    # Небольшая задержка между запросами, чтобы не превысить лимиты API
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f"Error translating description for game {game.name}: {e}")
                    continue

            # Сохраняем изменения
            db.commit()
            logger.info(f"Background translation completed for {len(games_to_translate)} games")

        except Exception as e:
            logger.error(f"Error in background translation task: {e}", exc_info=True)
            db.rollback()


# Глобальный экземпляр сервиса
translation_service = TranslationService()


async def translate_game_descriptions_background(db: Session) -> None:
    """
    Фоновая задача для перевода описаний игр.
    Вызывается из FastAPI BackgroundTasks.

    :param db: Сессия базы данных
    """
    await translation_service.translate_game_descriptions_background(db)