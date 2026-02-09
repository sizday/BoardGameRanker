import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from handlers.ranking import router as ranking_router
from services.import_ratings import import_ratings_from_sheet

API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:8000")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
RATING_SHEET_CSV_URL = os.getenv("RATING_SHEET_CSV_URL", "")


async def on_start(message: Message):
    await message.answer(
        "Привет! Я помогу составить топ-50 твоих настольных игр.\n"
        "Команды:\n"
        "/import_ratings — загрузить данные из Google-таблицы\n"
        "/start_ranking — начать формирование рейтинга"
    )


async def on_import_ratings(message: Message):
    """
    Команда для импорта данных из Google-таблицы в БД через backend API.
    """
    await message.answer("Начинаю загрузку данных из Google-таблицы...")

    try:
        imported_count = await import_ratings_from_sheet(
            api_base_url=API_BASE_URL,
            sheet_csv_url=RATING_SHEET_CSV_URL,
        )
        if imported_count == 0:
            await message.answer("Таблица пуста, нечего импортировать.")
        else:
            await message.answer(
                f"Импорт данных в БД успешно завершен. Импортировано игр: {imported_count}."
            )
    except ValueError as exc:
        await message.answer(str(exc))
    except Exception as exc:  # noqa: BLE001
        await message.answer(f"Ошибка при импорте данных: {exc}")


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    # сохраняем базовый URL API в объекте бота,
    # чтобы хендлеры могли к нему обращаться
    bot["api_base_url"] = API_BASE_URL

    dp = Dispatcher()

    # Команды верхнего уровня
    dp.message.register(on_start, CommandStart())
    dp.message.register(on_import_ratings, Command("import_ratings"))

    # Подключаем роутер с логикой ранжирования
    dp.include_router(ranking_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


