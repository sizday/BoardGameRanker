from __future__ import annotations

import logging
import httpx
from aiogram import Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import config

# Импортируем функции из других хендлеров для прямого вызова
from .login import cmd_login, LoginStates
from .my_games import _cmd_my_games_impl
from .ranking import cmd_start_ranking, RankingStates
from .bgg_game import GameSearchStates

# Импортируем FSMContext для работы с состояниями
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Импортируем функции для импорта и очистки
from services.import_ratings import import_ratings_from_sheet
from services.clear_database import clear_database

logger = logging.getLogger(__name__)

router = Router()

# Ключ для хранения message_id главного меню в FSMContext
MAIN_MENU_MESSAGE_ID_KEY = "main_menu_message_id"


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
        ],
        [
            InlineKeyboardButton(
                text="🔍 Поиск игры",
                callback_data="menu_search_game"
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


def create_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопкой возврата в главное меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⬅️ Назад в меню",
                callback_data="menu_back_to_main"
            )
        ]
    ])


async def update_main_menu(
    callback: CallbackQuery,
    state: FSMContext,
    text: str = None,
    reply_markup: InlineKeyboardMarkup = None
) -> None:
    """Обновляет главное меню - редактирует сообщение вместо отправки нового"""

    greeting_text = (
        "Привет! 👋\n\n"
        "Я помогу составить топ-50 твоих настольных игр.\n"
        "Выбери действие из меню ниже:"
    )

    if text is None:
        text = greeting_text
    if reply_markup is None:
        reply_markup = create_main_menu_keyboard(callback.from_user.id)

    # Получаем сохраненный message_id главного меню
    data = await state.get_data()
    old_main_menu_message_id = data.get(MAIN_MENU_MESSAGE_ID_KEY)

    # Всегда пытаемся редактировать текущее сообщение callback'а
    try:
        logger.info(f"Editing callback message {callback.message.message_id} in update_main_menu")
        await callback.message.edit_text(
            text=text,
            reply_markup=reply_markup
        )
        # Сохраняем message_id текущего сообщения как главное меню
        await state.update_data({MAIN_MENU_MESSAGE_ID_KEY: callback.message.message_id})
        logger.info(f"Successfully edited callback message {callback.message.message_id}, saved as MAIN_MENU_MESSAGE_ID_KEY")
    except Exception as exc:
        # Неудачное редактирование - нормально для старых сообщений
        # Отправляем новое сообщение
        new_message = await callback.message.answer(text, reply_markup=reply_markup)
        await state.update_data({MAIN_MENU_MESSAGE_ID_KEY: new_message.message_id})

        # Пытаемся удалить старое сообщение меню, если оно отличается от нового
        if old_main_menu_message_id and old_main_menu_message_id != new_message.message_id:
            try:
                await callback.bot.delete_message(
                    chat_id=callback.message.chat.id,
                    message_id=old_main_menu_message_id
                )
                logger.info(f"Deleted old main menu message {old_main_menu_message_id}")
            except Exception as delete_exc:
                logger.warning(f"Failed to delete old main menu message {old_main_menu_message_id}: {delete_exc}")


async def update_main_menu_from_message(
    message: Message,
    state: FSMContext,
    text: str = None,
    reply_markup: InlineKeyboardMarkup = None
) -> None:
    """Обновляет главное меню из обычного сообщения (не callback)"""

    # Получаем сохраненный message_id главного меню
    data = await state.get_data()
    main_menu_message_id = data.get(MAIN_MENU_MESSAGE_ID_KEY)
    logger.info(f"update_main_menu_from_message: main_menu_message_id = {main_menu_message_id}, text starts with: {text[:30] if text else 'None'}")

    greeting_text = (
        "Привет! 👋\n\n"
        "Я помогу составить топ-50 твоих настольных игр.\n"
        "Выбери действие из меню ниже:"
    )

    if text is None:
        text = greeting_text
    if reply_markup is None:
        reply_markup = create_main_menu_keyboard(message.from_user.id)

    # Всегда удаляем старое главное меню и отправляем новое сообщение
    if main_menu_message_id:
        try:
            logger.info(f"Deleting old main menu message {main_menu_message_id} in chat {message.chat.id}")
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=main_menu_message_id
            )
            logger.info(f"Successfully deleted old main menu message {main_menu_message_id}")
        except Exception as delete_exc:
            # Не логируем ошибки удаления сообщений - это нормально, если сообщение старое или уже удалено
            pass

    # Отправляем новое сообщение
    logger.info("Sending new main menu message")
    new_message = await message.answer(text, reply_markup=reply_markup)
    await state.update_data({MAIN_MENU_MESSAGE_ID_KEY: new_message.message_id})
    logger.info(f"New main menu message_id: {new_message.message_id}")


async def handle_menu_login(callback: CallbackQuery, state: FSMContext, api_base_url: str) -> None:
    """
    Обработка логина через меню - использует редактирование главного меню.
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
            await update_main_menu(
                callback,
                state,
                text=login_text,
                reply_markup=create_back_to_menu_keyboard()
            )

            # Логируем сохраненный message_id
            data = await state.get_data()
            current_menu_id = data.get(MAIN_MENU_MESSAGE_ID_KEY)
            logger.info(f"After handle_menu_login, MAIN_MENU_MESSAGE_ID_KEY: {current_menu_id}")

            await state.set_state(LoginStates.waiting_for_name)

            if response.status_code == 404:
                # Пользователь не зарегистрирован
                login_text = (
                    "👋 Привет! Для регистрации в системе мне нужно знать, как тебя называть.\n\n"
                    "Введи своё имя (то, под которым ты хочешь быть известен в системе):"
                )
                await update_main_menu(
                    callback,
                    state,
                    text=login_text,
                    reply_markup=create_back_to_menu_keyboard()
                )
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
            await update_main_menu(
                callback,
                state,
                text=login_text,
                reply_markup=create_back_to_menu_keyboard()
            )
            await state.set_state(LoginStates.waiting_for_name)
        else:
            logger.error(f"HTTP error during user check: {exc.response.status_code}")
            error_text = f"❌ Ошибка сервера: {exc.response.status_code}"
            await update_main_menu(
                callback,
                state,
                text=error_text,
                reply_markup=create_back_to_menu_keyboard()
            )
    except Exception as exc:
        logger.error(f"Error during user check: {exc}", exc_info=True)
        error_text = f"❌ Не удалось проверить статус пользователя: {exc}"
        await update_main_menu(
            callback,
            state,
            text=error_text,
            reply_markup=create_back_to_menu_keyboard()
        )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
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

    # Отправляем сообщение с меню и сохраняем его message_id
    sent_message = await message.answer(
        greeting_text,
        reply_markup=keyboard
    )

    # Сохраняем message_id главного меню в состоянии
    await state.update_data({MAIN_MENU_MESSAGE_ID_KEY: sent_message.message_id})


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
        if action == "back_to_main":
            # Сначала возвращаем главное меню к исходному состоянию
            await update_main_menu(callback, state)

            # Затем очищаем состояние поиска, если оно активно
            current_state = await state.get_state()
            if current_state in [GameSearchStates.waiting_for_game_name, LoginStates.waiting_for_name]:
                await state.clear()

        elif action == "login":
            # Вызываем функцию логина через меню
            await handle_menu_login(callback, state, api_base_url)

        elif action == "my_games":
            # Показываем список игр так же, как команда /my_games
            from .my_games import _cmd_my_games_impl
            await _cmd_my_games_impl(
                user_id=user_id,
                user_name=user_name,
                answer_func=callback.message.answer,
                api_base_url=api_base_url
            )

        elif action == "start_ranking":
            # Показываем экран начала ранжирования с кнопкой назад
            ranking_text = (
                "🏆 Ранжирование игр\n\n"
                "Сейчас начнется процесс ранжирования ваших игр.\n"
                "Вам будут показаны пары игр, выбирайте ту,\n"
                "которая вам больше нравится.\n\n"
                "Готовы начать?"
            )
            ranking_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🚀 Начать ранжирование",
                        callback_data="ranking_start"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад в меню",
                        callback_data="menu_back_to_main"
                    )
                ]
            ])
            await update_main_menu(
                callback,
                state,
                text=ranking_text,
                reply_markup=ranking_keyboard
            )

        elif action == "search_game":
            # Показываем экран поиска игры с кнопкой назад
            search_text = (
                "🔍 Поиск игры\n\n"
                "Введите название игры для поиска:\n\n"
                "Примеры: Terraforming Mars, Wingspan, Каркассон, Ticket to Ride, Уно"
            )
            logger.info(f"Setting up game search - updating main menu to search screen")
            await update_main_menu(
                callback,
                state,
                text=search_text,
                reply_markup=create_back_to_menu_keyboard()
            )

            await state.set_state(GameSearchStates.waiting_for_game_name)

        elif action == "ranking_start":
            # Начинаем процесс ранжирования
            await cmd_start_ranking(callback.message, state)

        elif action == "import":
            # Проверяем, что пользователь админ
            if not config.is_admin(user_id):
                await update_main_menu(
                    callback,
                    state,
                    text="❌ У вас нет прав для выполнения этой команды.",
                    reply_markup=create_back_to_menu_keyboard()
                )
                return

            # Показываем статус импорта
            await update_main_menu(
                callback,
                state,
                text="🚀 Начинаю импорт данных из Google Sheets...",
                reply_markup=create_back_to_menu_keyboard()
            )

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
                await update_main_menu(
                    callback,
                    state,
                    text=error_text,
                    reply_markup=create_back_to_menu_keyboard()
                )
                logger.error("RATING_SHEET_CSV_URL is not configured")
                return

            logger.info(f"Using CSV URL: {config.RATING_SHEET_CSV_URL}")

            # Проверяем доступность backend
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{api_base_url}/health", timeout=5.0)
                    if response.status_code != 200:
                        error_text = f"❌ Backend недоступен: HTTP {response.status_code}"
                        await update_main_menu(
                            callback,
                            state,
                            text=error_text,
                            reply_markup=create_back_to_menu_keyboard()
                        )
                        return
            except Exception as exc:
                error_text = f"❌ Не удалось подключиться к backend: {exc}"
                await update_main_menu(
                    callback,
                    state,
                    text=error_text,
                    reply_markup=create_back_to_menu_keyboard()
                )
                return

            try:
                logger.info(f"Starting import with CSV URL: {config.RATING_SHEET_CSV_URL}")
                imported_count = await import_ratings_from_sheet(
                    api_base_url=api_base_url,
                    sheet_csv_url=config.RATING_SHEET_CSV_URL,
                )
                logger.info(f"Import completed: {imported_count} games processed")

                if imported_count == 0:
                    logger.warning("Import completed but no games were imported")
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

                await update_main_menu(
                    callback,
                    state,
                    text=result_text,
                    reply_markup=create_back_to_menu_keyboard()
                )

            except ValueError as exc:
                logger.error(f"Validation error during import: {exc}")
                error_text = f"❌ Ошибка валидации: {str(exc)}"
                await update_main_menu(
                    callback,
                    state,
                    text=error_text,
                    reply_markup=create_back_to_menu_keyboard()
                )
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Error during ratings import: {exc}", exc_info=True)
                error_text = f"❌ Ошибка при импорте данных: {type(exc).__name__}: {str(exc)}"
                await update_main_menu(
                    callback,
                    state,
                    text=error_text,
                    reply_markup=create_back_to_menu_keyboard()
                )

        elif action == "clear":
            # Проверяем, что пользователь админ
            if not config.is_admin(user_id):
                await update_main_menu(
                    callback,
                    state,
                    text="❌ У вас нет прав для выполнения этой команды.",
                    reply_markup=create_back_to_menu_keyboard()
                )
                return

            # Показываем статус очистки
            await update_main_menu(
                callback,
                state,
                text="🗑️ Очищаю базу данных...",
                reply_markup=create_back_to_menu_keyboard()
            )

            logger.info(f"Admin {user_name} (ID: {user_id}) started database clear via menu")

            try:
                result = await clear_database(api_base_url=api_base_url)

                games_deleted = result.get("games_deleted", 0)
                ratings_deleted = result.get("ratings_deleted", 0)
                sessions_deleted = result.get("sessions_deleted", 0)
                users_deleted = result.get("users_deleted", 0)

                logger.info(f"Database cleared successfully by admin {user_name}: games={games_deleted}, ratings={ratings_deleted}, sessions={sessions_deleted}, users={users_deleted}")

                result_text = (
                    "✅ База данных успешно очищена!\n\n"
                    f"Удалено:\n"
                    f"• Игр: {games_deleted}\n"
                    f"• Рейтингов: {ratings_deleted}\n"
                    f"• Сессий ранжирования: {sessions_deleted}\n\n"
                    f"👥 Пользователи сохранены ({users_deleted} удалено)"
                )

                await update_main_menu(
                    callback,
                    state,
                    text=result_text,
                    reply_markup=create_back_to_menu_keyboard()
                )

            except RuntimeError as exc:
                logger.error(f"Runtime error during database clear: {exc}")
                error_text = f"❌ Ошибка при очистке базы данных: {exc}"
                await update_main_menu(
                    callback,
                    state,
                    text=error_text,
                    reply_markup=create_back_to_menu_keyboard()
                )
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Unexpected error during database clear: {exc}", exc_info=True)
                error_text = f"❌ Неожиданная ошибка при очистке базы данных: {exc}"
                await update_main_menu(
                    callback,
                    state,
                    text=error_text,
                    reply_markup=create_back_to_menu_keyboard()
                )

        else:
            logger.warning(f"Unknown menu action: {action}")
            await callback.message.answer("❌ Неизвестная команда.")

    except Exception as exc:
        logger.error(f"Error handling menu action '{action}': {exc}", exc_info=True)
        await callback.message.answer(f"❌ Произошла ошибка при выполнении команды: {exc}")


@router.message(StateFilter(LoginStates.waiting_for_name))
async def process_menu_name_input(message: Message, state: FSMContext, api_base_url: str) -> None:
    """
    Обрабатывает введенное пользователем имя для регистрации или обновления через меню.
    """
    user_id = message.from_user.id
    user_name = message.text.strip()

    # Логируем текущий MAIN_MENU_MESSAGE_ID_KEY
    data = await state.get_data()
    current_menu_id = data.get(MAIN_MENU_MESSAGE_ID_KEY)
    logger.info(f"process_menu_name_input ENTRY: current MAIN_MENU_MESSAGE_ID_KEY = {current_menu_id}, user message_id = {message.message_id}")

    # Валидация имени
    if not user_name:
        # Удаляем старое главное меню и показываем ошибку
        data = await state.get_data()
        old_menu_id = data.get(MAIN_MENU_MESSAGE_ID_KEY)
        if old_menu_id:
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=old_menu_id
                )
                logger.info(f"Deleted old main menu message {old_menu_id} (empty name)")
            except Exception as e:
                # Неудачное удаление - нормально для старых сообщений
                pass

        error_text = "❌ Имя не может быть пустым. Введи своё имя:"
        new_menu = await message.answer(error_text, reply_markup=create_back_to_menu_keyboard())
        await state.update_data({MAIN_MENU_MESSAGE_ID_KEY: new_menu.message_id})

        # Пытаемся удалить сообщение пользователя
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=message.message_id
            )
            logger.info(f"Deleted user message {message.message_id} (empty name)")
        except Exception as delete_exc:
            # Неудачное удаление сообщения пользователя - нормально
            pass

        return

    if len(user_name) > 100:
        # Удаляем старое главное меню и показываем ошибку
        data = await state.get_data()
        old_menu_id = data.get(MAIN_MENU_MESSAGE_ID_KEY)
        if old_menu_id:
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=old_menu_id
                )
                logger.info(f"Deleted old main menu message {old_menu_id} (name too long)")
            except Exception as e:
                # Неудачное удаление - нормально для старых сообщений
                pass

        error_text = "❌ Имя слишком длинное (максимум 100 символов). Введи короче:"
        new_menu = await message.answer(error_text, reply_markup=create_back_to_menu_keyboard())
        await state.update_data({MAIN_MENU_MESSAGE_ID_KEY: new_menu.message_id})

        # Пытаемся удалить сообщение пользователя
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=message.message_id
            )
            logger.info(f"Deleted user message {message.message_id} (name too long)")
        except Exception as delete_exc:
            # Неудачное удаление сообщения пользователя - нормально
            pass

        return

    logger.info(f"Processing name input for user {user_id}: '{user_name}'")

    try:
        async with httpx.AsyncClient() as client:
            # Создаем или обновляем пользователя через API
            response = await client.post(
                f"{api_base_url}/api/users",
                json={
                    "telegram_id": user_id,
                    "name": user_name
                },
                timeout=10.0
            )
            response.raise_for_status()

            user_data = response.json()
            created = user_data.get("created", False)
            name_updated = user_data.get("name_updated", False)

            if created:
                # Новый пользователь
                logger.info(f"User {user_name} (telegram_id: {user_id}) successfully registered via menu")
                success_text = (
                    f"✅ Отлично, {user_name}!\n\n"
                    "Ты успешно зарегистрирован в системе."
                )
            elif name_updated:
                # Имя обновлено
                logger.info(f"User {user_name} (telegram_id: {user_id}) name updated via menu")
                success_text = (
                    f"✅ Имя успешно изменено на '{user_name}'!"
                )
            else:
                # Пользователь уже существует с таким же именем
                logger.info(f"User {user_name} (telegram_id: {user_id}) already exists with same name via menu")
                success_text = (
                    f"👋 Привет, {user_name}!\n\n"
                    "Ты уже зарегистрирован в системе с таким именем."
                )

            # Показываем результат напрямую
            logger.info(f"About to show success result: {success_text[:50]}...")

            # Пытаемся удалить или отредактировать старое главное меню
            data = await state.get_data()
            old_menu_id = data.get(MAIN_MENU_MESSAGE_ID_KEY)
            logger.info(f"Attempting to handle old main menu message {old_menu_id} for success case")

            menu_updated = False
            if old_menu_id:
                # Сначала пытаемся удалить
                try:
                    await message.bot.delete_message(
                        chat_id=message.chat.id,
                        message_id=old_menu_id
                    )
                    logger.info(f"SUCCESS: Deleted old main menu message {old_menu_id}")
                    menu_updated = True
                except Exception as delete_e:
                    logger.warning(f"FAILED to delete old main menu message {old_menu_id}: {delete_e}")
                    # Если не можем удалить, пытаемся отредактировать
                    try:
                        await message.bot.edit_message_text(
                            chat_id=message.chat.id,
                            message_id=old_menu_id,
                            text=success_text,
                            reply_markup=create_back_to_menu_keyboard()
                        )
                        logger.info(f"SUCCESS: Edited old main menu message {old_menu_id} instead of deleting")
                        menu_updated = True
                        # Обновляем MAIN_MENU_MESSAGE_ID_KEY, так как сообщение отредактировано
                        await state.update_data({MAIN_MENU_MESSAGE_ID_KEY: old_menu_id})  # Уже правильный
                    except Exception as edit_e:
                        logger.warning(f"FAILED to edit old main menu message {old_menu_id}: {edit_e}")

            # Пытаемся удалить сообщение пользователя с введенным именем
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=message.message_id
                )
                logger.info(f"Deleted user message {message.message_id}")
            except Exception as delete_exc:
                logger.warning(f"Failed to delete user message {message.message_id}: {delete_exc}")
                # Не критично, если не удалось удалить

            if not menu_updated:
                # Если не удалось ни удалить, ни отредактировать, отправляем новое сообщение
                new_menu = await message.answer(success_text, reply_markup=create_back_to_menu_keyboard())
                await state.update_data({MAIN_MENU_MESSAGE_ID_KEY: new_menu.message_id})
                logger.info(f"Sent new success message {new_menu.message_id} (fallback)")
            else:
                # Если удалили или отредактировали старое меню, отправляем сообщение с результатом
                new_menu = await message.answer(success_text, reply_markup=create_back_to_menu_keyboard())
                await state.update_data({MAIN_MENU_MESSAGE_ID_KEY: new_menu.message_id})
                logger.info(f"Sent new success message {new_menu.message_id} after handling old menu")

            # Очищаем состояние после успешной обработки
            await state.clear()

    except httpx.HTTPStatusError as exc:
        # Очищаем состояние даже при ошибке
        await state.clear()

        if exc.response.status_code == 400:
            try:
                error_data = exc.response.json()
                error_msg = error_data.get("detail", "Неизвестная ошибка")
            except:
                error_msg = "Ошибка валидации данных"
            error_text = f"❌ Ошибка: {error_msg}"
        else:
            logger.error(f"HTTP error during user registration: {exc.response.status_code}")
            error_text = f"❌ Ошибка сервера: {exc.response.status_code}"

        # Удаляем старое главное меню и показываем ошибку
        data = await state.get_data()
        old_menu_id = data.get(MAIN_MENU_MESSAGE_ID_KEY)
        if old_menu_id:
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=old_menu_id
                )
                logger.info(f"Deleted old main menu message {old_menu_id} (server error)")
            except Exception as e:
                # Неудачное удаление - нормально для старых сообщений
                pass

        new_menu = await message.answer(error_text, reply_markup=create_back_to_menu_keyboard())
        await state.update_data({MAIN_MENU_MESSAGE_ID_KEY: new_menu.message_id})

        # Пытаемся удалить сообщение пользователя
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=message.message_id
            )
            logger.info(f"Deleted user message {message.message_id} after error")
        except Exception as delete_exc:
            # Неудачное удаление сообщения пользователя - нормально
            pass

    except Exception as exc:
        # Очищаем состояние даже при ошибке
        await state.clear()

        logger.error(f"Error during user registration: {exc}", exc_info=True)
        error_text = f"❌ Не удалось зарегистрироваться: {exc}"

        # Удаляем старое главное меню и показываем ошибку
        data = await state.get_data()
        old_menu_id = data.get(MAIN_MENU_MESSAGE_ID_KEY)
        if old_menu_id:
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=old_menu_id
                )
                logger.info(f"Deleted old main menu message {old_menu_id} (registration error)")
            except Exception as e:
                # Неудачное удаление - нормально для старых сообщений
                pass

        new_menu = await message.answer(error_text, reply_markup=create_back_to_menu_keyboard())
        await state.update_data({MAIN_MENU_MESSAGE_ID_KEY: new_menu.message_id})