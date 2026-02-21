from __future__ import annotations

import logging
import httpx
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import config

# Импортируем функции из других хендлеров для прямого вызова
from .login import cmd_login
from .my_games import cmd_my_games
from .ranking import cmd_start_ranking

# Импортируем FSMContext для работы с состояниями
from aiogram.fsm.context import FSMContext

# Импортируем функции для импорта и очистки
from services.import_ratings import import_ratings_from_sheet
from services.clear_database import clear_database

logger = logging.getLogger(__name__)

router = Router()


def create_main_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру главного меню в зависимости от роли пользователя"""

    # Базовые кнопки для всех пользователей
    buttons = [
        [
            InlineKeyboardButton(
                text="👤 Регистрация/Изменить имя",
                callback_data="menu_login"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎮 Мои игры",
                callback_data="menu_my_games"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏆 Начать ранжирование",
                callback_data="menu_start_ranking"
            )
        ]
    ]

    # Кнопки для админов
    if config.is_admin(user_id):
        admin_buttons = [
            [
                InlineKeyboardButton(
                    text="📊 Импорт данных",
                    callback_data="menu_import"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑️ Очистить БД",
                    callback_data="menu_clear"
                )
            ]
        ]
        buttons.extend(admin_buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """
    Обработчик команды /start с отображением меню.
    """
    user_id = message.from_user.id
    user_name = message.from_user.full_name or str(user_id)

    logger.info(f"User {user_name} (ID: {user_id}) started bot")

    greeting_text = (
        "Привет! 👋\n\n"
        "Я помогу составить топ-50 твоих настольных игр.\n"
        "Выбери действие из меню ниже:"
    )

    keyboard = create_main_menu_keyboard(user_id)

    await message.answer(
        greeting_text,
        reply_markup=keyboard
    )


@router.callback_query(lambda c: c.data.startswith("menu_"))
async def handle_menu_callbacks(
    callback: CallbackQuery,
    state: FSMContext,
    api_base_url: str,
    default_language: str
) -> None:
    """
    Обработчик callback запросов от кнопок меню.
    """
    action = callback.data.replace("menu_", "")
    user_id = callback.from_user.id
    user_name = callback.from_user.full_name or str(user_id)

    logger.info(f"Menu action '{action}' from user {user_name} (ID: {user_id})")

    # Отвечаем на callback, чтобы убрать "часики" у кнопки
    await callback.answer()

    try:
        if action == "login":
            # Вызываем функцию логина напрямую
            await cmd_login(callback.message, state, api_base_url)

        elif action == "my_games":
            # Вызываем функцию просмотра игр напрямую
            await cmd_my_games(callback.message, api_base_url)

        elif action == "start_ranking":
            # Вызываем функцию начала ранжирования напрямую
            await cmd_start_ranking(callback.message, state)

        elif action == "import":
            # Проверяем, что пользователь админ
            if not config.is_admin(user_id):
                await callback.message.answer("❌ У вас нет прав для выполнения этой команды.")
                return

            # Запускаем импорт данных
            await callback.message.answer("🚀 Начинаю импорт данных из Google Sheets...")

            try:
                imported_count = await import_ratings_from_sheet(
                    api_base_url=api_base_url,
                    sheet_csv_url=config.RATING_SHEET_CSV_URL,
                )

                if imported_count == 0:
                    logger.warning("Import completed but no games were imported")
                    await callback.message.answer("⚠️ Таблица пуста или данные не найдены.")
                else:
                    logger.info(f"Import completed successfully: {imported_count} games imported")
                    await callback.message.answer(
                        f"✅ Импорт завершен!\n\n"
                        f"Загружено данных для {imported_count} игр.\n"
                        f"Игры добавляются в базу данных по одной с автоматической загрузкой данных из BGG."
                    )
            except ValueError as exc:
                logger.error(f"Validation error during import: {exc}")
                await callback.message.answer(str(exc))
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Error during ratings import: {exc}", exc_info=True)
                await callback.message.answer(f"Ошибка при импорте данных: {exc}")

        elif action == "clear":
            # Проверяем, что пользователь админ
            if not config.is_admin(user_id):
                await callback.message.answer("❌ У вас нет прав для выполнения этой команды.")
                return

            # Запускаем очистку базы данных
            logger.info(f"Admin {user_name} (ID: {user_id}) started database clear via menu")

            try:
                result = await clear_database(api_base_url=api_base_url)

                games_deleted = result.get("games_deleted", 0)
                ratings_deleted = result.get("ratings_deleted", 0)
                sessions_deleted = result.get("sessions_deleted", 0)
                users_deleted = result.get("users_deleted", 0)

                logger.info(f"Database cleared successfully by admin {user_name}: games={games_deleted}, ratings={ratings_deleted}, sessions={sessions_deleted}, users={users_deleted}")

                await callback.message.answer(
                    "✅ База данных успешно очищена!\n\n"
                    f"Удалено:\n"
                    f"• Игр: {games_deleted}\n"
                    f"• Рейтингов: {ratings_deleted}\n"
                    f"• Сессий ранжирования: {sessions_deleted}\n"
                    f"• Пользователей: {users_deleted}"
                )

            except RuntimeError as exc:
                logger.error(f"Runtime error during database clear: {exc}")
                await callback.message.answer(f"❌ Ошибка при очистке базы данных: {exc}")
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Unexpected error during database clear: {exc}", exc_info=True)
                await callback.message.answer(f"❌ Неожиданная ошибка при очистке базы данных: {exc}")

        else:
            logger.warning(f"Unknown menu action: {action}")
            await callback.message.answer("❌ Неизвестная команда.")

    except Exception as exc:
        logger.error(f"Error handling menu action '{action}': {exc}", exc_info=True)
        await callback.message.answer(f"❌ Произошла ошибка при выполнении команды: {exc}")