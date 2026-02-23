from __future__ import annotations

import logging
import httpx
from aiogram import Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import CallbackQuery, Message

# Импортируем функции из других хендлеров для прямого вызова
from .login import LoginStates

# Импортируем FSMContext для работы с состояниями
from aiogram.fsm.context import FSMContext

# Импортируем функции из модулей меню
from .menu_keyboards import create_main_menu_keyboard, create_back_to_menu_keyboard
from .menu_actions import (
    handle_menu_back_to_main,
    handle_menu_login,
    handle_menu_my_games,
    handle_menu_start_ranking,
    handle_menu_search_game,
    handle_menu_ranking_start,
    handle_menu_import,
    handle_menu_clear,
)

logger = logging.getLogger(__name__)

router = Router()


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

    # Отправляем сообщение с меню и сохраняем его message_id
    await message.answer(greeting_text, reply_markup=keyboard)



@router.callback_query(lambda c: c.data.startswith("menu_"))
async def handle_menu_callbacks(
    callback: CallbackQuery,
    state: FSMContext,
    api_base_url: str,
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
        # Маршрутизация действий меню
        if action == "back_to_main":
            await handle_menu_back_to_main(callback, state)
        elif action == "login":
            await handle_menu_login(callback, state, api_base_url)
        elif action == "my_games":
            await handle_menu_my_games(callback, user_id, user_name, api_base_url, state)
        elif action == "start_ranking":
            await handle_menu_start_ranking(callback, state)
        elif action == "search_game":
            await handle_menu_search_game(callback, state)
        elif action == "ranking_start":
            await handle_menu_ranking_start(callback, state)
        elif action == "import":
            await handle_menu_import(callback, state, user_id, api_base_url)
        elif action == "clear":
            await handle_menu_clear(callback, state, user_id, api_base_url)
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
    # Отслеживаем сообщение пользователя для потенциального удаления


    # Валидация имени
    if not user_name:
        # Показываем ошибку
        error_text = "❌ Имя не может быть пустым. Введи своё имя:"
        await message.answer(error_text, reply_markup=create_back_to_menu_keyboard())

        return

    if len(user_name) > 100:
        # Показываем ошибку
        error_text = "❌ Имя слишком длинное (максимум 100 символов). Введи короче:"
        await message.answer(error_text, reply_markup=create_back_to_menu_keyboard())

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
                success_text = (
                    f"👋 Привет, {user_name}!\n\n"
                    "Ты уже зарегистрирован в системе с таким именем."
                )

            # Отправляем сообщение об успехе
            try:
                await message.answer(success_text, reply_markup=create_back_to_menu_keyboard())
            except Exception as e:
                logger.error(f"Failed to send success message: {e}")
                # В случае ошибки просто обновляем состояние
                await state.clear()

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

        # Показываем ошибку
        await message.answer(error_text, reply_markup=create_back_to_menu_keyboard())

    except Exception as exc:
        # Очищаем состояние даже при ошибке
        await state.clear()

        logger.error(f"Error during user registration: {exc}", exc_info=True)
        error_text = f"❌ Не удалось зарегистрироваться: {exc}"

        # Показываем ошибку
        await message.answer(error_text, reply_markup=create_back_to_menu_keyboard())
