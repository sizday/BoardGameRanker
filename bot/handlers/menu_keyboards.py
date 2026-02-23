"""
Модуль для создания клавиатур меню бота.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import config


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


def create_ranking_start_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для экрана начала ранжирования"""
    return InlineKeyboardMarkup(inline_keyboard=[
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