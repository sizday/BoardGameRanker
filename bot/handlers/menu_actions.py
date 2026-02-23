"""
Обработчики действий меню бота.
"""

import logging
import httpx
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from aiogram.fsm.context import FSMContext

from config import config
from services.import_ratings import import_ratings_from_sheet
from services.clear_database import clear_database

from .login import LoginStates
from .my_games import _cmd_my_games_impl
from .ranking import cmd_start_ranking
from .bgg_game import GameSearchStates

from .menu_keyboards import create_back_to_menu_keyboard, create_ranking_start_keyboard
from .menu_utils import update_main_menu

logger = logging.getLogger(__name__)


async def handle_menu_back_to_main(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка возврата в главное меню"""
    # Используем update_main_menu для редактирования текущего сообщения
    await update_main_menu(callback)

    # Затем очищаем состояние поиска, если оно активно
    current_state = await state.get_state()
    if current_state in [GameSearchStates.waiting_for_game_name, LoginStates.waiting_for_name]:
        await state.clear()


async def handle_menu_login(callback: CallbackQuery, state: FSMContext, api_base_url: str) -> None:
    """
    Обработка логина через меню.
    """
    user_id = callback.from_user.id
    user_full_name = callback.from_user.full_name or f"User_{user_id}"

    logger.info(f"User {user_full_name} (ID: {user_id}) initiated login via menu")

    # Проверяем, зарегистрирован ли пользователь
    try:
        async with httpx.AsyncClient() as client:
            # Проверяем существование пользователя через GET запрос
            response = await client.get(
                f"{api_base_url}/api/users/{user_id}/games",
                timeout=10.0
            )

            if response.status_code == 200:
                # Пользователь уже зарегистрирован
                login_text = (
                "👋 Ты уже зарегистрирован в системе!\n\n"
                "Если хочешь изменить своё имя, введи новое имя ниже.\n"
                "Если хочешь оставить текущее имя, нажми '⬅️ Назад в меню'"
            )
            # Отправляем новое сообщение
            await callback.message.answer(login_text, reply_markup=create_back_to_menu_keyboard())

            await state.set_state(LoginStates.waiting_for_name)

            if response.status_code == 404:
                # Пользователь не зарегистрирован
                login_text = (
                    "👋 Привет! Для регистрации в системе мне нужно знать, как тебя называть.\n\n"
                    "Введи своё имя (то, под которым ты хочешь быть известен в системе):"
                )
                # Отправляем новое сообщение вместо редактирования
                await callback.message.answer(login_text, reply_markup=create_back_to_menu_keyboard())
                await state.set_state(LoginStates.waiting_for_name)
            else:
                response.raise_for_status()

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            # Пользователь не зарегистрирован
            login_text = (
                "👋 Привет! Для регистрации в системе мне нужно знать, как тебя называть.\n\n"
                "Введи своё имя (то, под которым ты хочешь быть известен в системе):"
            )
            # Отправляем новое сообщение вместо редактирования
            await callback.message.answer(login_text, reply_markup=create_back_to_menu_keyboard())
            await state.set_state(LoginStates.waiting_for_name)
        else:
            logger.error(f"HTTP error during user check: {exc.response.status_code}")
            error_text = f"❌ Ошибка сервера: {exc.response.status_code}"
            # Отправляем новое сообщение вместо редактирования
            await callback.message.answer(error_text, reply_markup=create_back_to_menu_keyboard())
    except Exception as exc:
        logger.error(f"Error during user check: {exc}", exc_info=True)
        error_text = f"❌ Не удалось проверить статус пользователя: {exc}"
        # Отправляем новое сообщение
        await callback.message.answer(error_text, reply_markup=create_back_to_menu_keyboard())


async def handle_menu_my_games(callback: CallbackQuery, user_id: int, user_name: str, api_base_url: str, state: FSMContext) -> None:
    """Обработка показа списка игр пользователя"""
    # Показываем список игр так же, как команда /my_games
    sent_messages = []

    async def answer_func_with_tracking(text, **kwargs):
        message = await callback.message.answer(text, **kwargs)
        sent_messages.append(message)
        return message

    await _cmd_my_games_impl(
        user_id=user_id,
        user_name=user_name,
        answer_func=answer_func_with_tracking,
        api_base_url=api_base_url
    )

    # Добавляем кнопку "Назад в меню" к последнему сообщению
    if sent_messages:
        from .menu_keyboards import create_back_to_menu_keyboard
        await sent_messages[-1].edit_reply_markup(reply_markup=create_back_to_menu_keyboard())


async def handle_menu_start_ranking(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка начала ранжирования"""
    # Показываем экран начала ранжирования с кнопкой назад
    ranking_text = (
        "🏆 Ранжирование игр\n\n"
        "Сейчас начнется процесс ранжирования ваших игр.\n"
        "Вам будут показаны пары игр, выбирайте ту,\n"
        "которая вам больше нравится.\n\n"
        "Готовы начать?"
    )
    # Отправляем новое сообщение
    await callback.message.answer(ranking_text, reply_markup=create_ranking_start_keyboard())


async def handle_menu_search_game(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка поиска игры"""
    # Показываем экран поиска игры с кнопкой назад
    search_text = (
        "🔍 Поиск игры\n\n"
        "Введите название игры для поиска:\n\n"
        "Примеры: Покорение марса, Wingspan, Каркассон, Ticket to Ride"
    )
    # Отправляем новое сообщение
    await callback.message.answer(search_text, reply_markup=create_back_to_menu_keyboard())

    await state.set_state(GameSearchStates.waiting_for_game_name)


async def handle_menu_ranking_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка запуска ранжирования"""
    # Начинаем процесс ранжирования
    await cmd_start_ranking(callback.message, state)


async def handle_menu_import(callback: CallbackQuery, state: FSMContext, user_id: int, api_base_url: str) -> None:
    """Обработка импорта данных (только для админов)"""
    # Проверяем, что пользователь админ
    if not config.is_admin(user_id):
        # Отправляем новое сообщение вместо редактирования
        await callback.message.answer("❌ У вас нет прав для выполнения этой команды.", reply_markup=create_back_to_menu_keyboard())
        return

    # Показываем статус импорта
    # Отправляем новое сообщение
    await callback.message.answer("🚀 Начинаю импорт данных из Google Sheets...", reply_markup=create_back_to_menu_keyboard())

    # Проверяем конфигурацию
    if not config.RATING_SHEET_CSV_URL:
        error_text = (
            "❌ Ошибка: RATING_SHEET_CSV_URL не настроена\n\n"
            "Чтобы настроить импорт:\n"
            "1. Создайте Google Таблицу с данными\n"
            "2. Опубликуйте её: Файл → Опубликовать в интернете → CSV\n"
            "3. Скопируйте ссылку в переменную RATING_SHEET_CSV_URL в .env файле\n\n"
            "Пример: RATING_SHEET_CSV_URL=https://docs.google.com/spreadsheets/d/YOUR_ID/export?format=csv"
        )
        # Отправляем новое сообщение вместо редактирования
        await callback.message.answer(error_text, reply_markup=create_back_to_menu_keyboard())
        return

    # Проверяем доступность backend
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_base_url}/health", timeout=5.0)
            if response.status_code != 200:
                error_text = f"❌ Backend недоступен: HTTP {response.status_code}"
                # Отправляем новое сообщение вместо редактирования
                await callback.message.answer(error_text, reply_markup=create_back_to_menu_keyboard())
                return
    except Exception as exc:
        error_text = f"❌ Не удалось подключиться к backend: {exc}"
        # Отправляем новое сообщение вместо редактирования
        await callback.message.answer(error_text, reply_markup=create_back_to_menu_keyboard())
        return

    try:
        imported_count = await import_ratings_from_sheet(
            api_base_url=api_base_url,
            sheet_csv_url=config.RATING_SHEET_CSV_URL,
        )

        if imported_count == 0:
            result_text = (
                "⚠️ Импорт завершен, но игры не были загружены.\n\n"
                "Возможные причины:\n"
                "• CSV файл пустой или недоступен\n"
                "• Неправильный формат данных\n"
                "• Все игры уже есть в базе данных\n\n"
                "Проверьте логи для подробной информации."
            )
        else:
            logger.info(f"Import completed successfully: {imported_count} games imported")
            result_text = (
                f"✅ Импорт завершен!\n\n"
                f"📊 Обработано {imported_count} игр из таблицы\n"
                f"🎮 Игры добавлены в базу данных\n"
                f"🌐 Данные из BGG загружаются автоматически\n\n"
                f"⚠️ Рейтинги добавляются только для зарегистрированных пользователей\n"
                f"💡 Если рейтинги не появились, убедитесь, что пользователи зарегистрированы с теми же именами, что и в таблице"
            )

        # Отправляем новое сообщение вместо редактирования
        await callback.message.answer(result_text, reply_markup=create_back_to_menu_keyboard())

    except ValueError as exc:
        error_text = f"❌ Ошибка валидации: {str(exc)}"
        # Отправляем новое сообщение вместо редактирования
        await callback.message.answer(error_text, reply_markup=create_back_to_menu_keyboard())
    except Exception as exc:  # noqa: BLE001
        error_text = f"❌ Ошибка при импорте данных: {type(exc).__name__}: {str(exc)}"
        # Отправляем новое сообщение вместо редактирования
        await callback.message.answer(error_text, reply_markup=create_back_to_menu_keyboard())


async def handle_menu_clear(callback: CallbackQuery, state: FSMContext, user_id: int, api_base_url: str) -> None:
    """Обработка очистки базы данных (только для админов)"""
    # Проверяем, что пользователь админ
    if not config.is_admin(user_id):
        # Отправляем новое сообщение вместо редактирования
        await callback.message.answer("❌ У вас нет прав для выполнения этой команды.", reply_markup=create_back_to_menu_keyboard())
        return

    # Показываем статус очистки
    # Отправляем новое сообщение
    await callback.message.answer("🗑️ Очищаю базу данных...", reply_markup=create_back_to_menu_keyboard())

    try:
        result = await clear_database(api_base_url=api_base_url)

        games_deleted = result.get("games_deleted", 0)
        ratings_deleted = result.get("ratings_deleted", 0)
        sessions_deleted = result.get("sessions_deleted", 0)

        logger.info(f"Database cleared by admin {user_id}: games={games_deleted}, ratings={ratings_deleted}, sessions={sessions_deleted}")

        result_text = (
            "✅ База данных успешно очищена!\n\n"
            f"Удалено:\n"
            f"• Игр: {games_deleted}\n"
            f"• Рейтингов: {ratings_deleted}\n"
            f"• Сессий ранжирования: {sessions_deleted}\n"
        )

        # Отправляем новое сообщение вместо редактирования
        await callback.message.answer(result_text, reply_markup=create_back_to_menu_keyboard())

    except RuntimeError as exc:
        error_text = f"❌ Ошибка при очистке базы данных: {exc}"
        # Отправляем новое сообщение вместо редактирования
        await callback.message.answer(error_text, reply_markup=create_back_to_menu_keyboard())
    except Exception as exc:  # noqa: BLE001
        error_text = f"❌ Неожиданная ошибка при очистке базы данных: {exc}"
        # Отправляем новое сообщение вместо редактирования
        await callback.message.answer(error_text, reply_markup=create_back_to_menu_keyboard())