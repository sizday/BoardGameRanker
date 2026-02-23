"""
Утилитарные функции для работы с меню бота.
"""

import logging
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from .menu_keyboards import create_main_menu_keyboard

logger = logging.getLogger(__name__)


async def update_main_menu(
    callback: CallbackQuery,
    text: str = None,
    reply_markup: InlineKeyboardMarkup = None
) -> None:
    """Отправляет новое сообщение с главным меню"""

    greeting_text = (
        "Привет! 👋\n\n"
        "Я помогу составить топ-50 твоих настольных игр.\n"
        "Выбери действие из меню ниже:"
    )

    if text is None:
        text = greeting_text
    if reply_markup is None:
        reply_markup = create_main_menu_keyboard(callback.from_user.id)

    # Всегда отправляем новое сообщение
    await callback.message.answer(text, reply_markup=reply_markup)