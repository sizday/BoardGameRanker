from __future__ import annotations

import logging
import httpx
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("my_games"))
async def cmd_my_games(message: Message, api_base_url: str) -> None:
    """
    Команда /my_games - показывает список игр пользователя с ссылками на BGG.

    Показывает только игры с BGG ID, отсортированные лексикографически.
    """
    await _cmd_my_games_impl(message.from_user.id, message.from_user.full_name or str(message.from_user.id), message.answer, api_base_url)


async def _cmd_my_games_impl(user_id: int, user_name: str, answer_func, api_base_url: str) -> None:
    """
    Внутренняя реализация команды /my_games
    """

    logger.info(f"User {user_name} (ID: {user_id}) requested their games")

    try:
        # Сначала получаем информацию о пользователе
        async with httpx.AsyncClient() as client:
            # Проверяем, зарегистрирован ли пользователь
            user_response = await client.get(
                f"{api_base_url}/api/users/{user_id}/games",
                timeout=30.0  # Увеличиваем таймаут до 30 секунд
            )
            user_response.raise_for_status()

            data = user_response.json()
            games = data.get("games", [])

            if not games:
                await answer_func(
                    "📭 У тебя пока нет оцененных игр.\n\n"
                    "Чтобы добавить игры:\n"
                    "1. Зарегистрируйся командой /login\n"
                    "2. Дождись импорта данных администратором (/import)\n"
                    "3. Твои игры появятся в этом списке!"
                )
                return

            # Формируем сообщение со списком игр
            lines = [f"🎲 Твои игры ({len(games)}):\n"]

            for game in games:
                name = game.get("name", "Без названия")
                bgg_url = game.get("bgg_url", "")

                # Формируем строку с игрой
                game_line = f"• <a href=\"{bgg_url}\">{name}</a>"

                lines.append(game_line)

            # Разбиваем на части, если сообщение слишком длинное
            text = "\n".join(lines)
            if len(text) > 4000:  # Ограничение Telegram
                # Разбиваем на части по максимальному количеству игр, входящих в 4000 символов
                parts = []
                current_part = []
                current_length = 0

                for line in lines:
                    line_length = len(line) + 1  # +1 для символа новой строки

                    # Если добавление этой строки превысит лимит, сохраняем текущую часть
                    if current_length + line_length > 4000 and current_part:
                        parts.append("\n".join(current_part))
                        current_part = []
                        current_length = 0

                    current_part.append(line)
                    current_length += line_length

                # Добавляем последнюю часть, если она не пустая
                if current_part:
                    parts.append("\n".join(current_part))

                for part in parts:
                    await answer_func(part, disable_web_page_preview=True)
            else:
                await answer_func(text, disable_web_page_preview=True)

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            await answer_func(
                "❌ Ты не зарегистрирован в системе.\n\n"
                "Используй команду /login для регистрации."
            )
        else:
            logger.error(f"HTTP error getting user games: {exc.response.status_code}")
            await answer_func(f"❌ Ошибка сервера: {exc.response.status_code}")
    except Exception as exc:
        logger.error(f"Error getting user games: {exc}", exc_info=True)
        await answer_func(f"❌ Не удалось получить список игр: {exc}")