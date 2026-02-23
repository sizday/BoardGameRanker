from __future__ import annotations

import logging
import httpx
from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

logger = logging.getLogger(__name__)

router = Router()


class GameSearchStates(StatesGroup):
    waiting_for_game_name = State()


async def _search_game_impl(
    message_or_callback,
    query: str,
    api_base_url: str,
    default_language: str,
    state: FSMContext = None,
    use_menu_editing: bool = False,
) -> None:
    """
    Вспомогательная функция для поиска игры по названию.
    Используется как из команды /game, так и из меню.
    """
    # Определяем user_id и user_name в зависимости от типа объекта
    if hasattr(message_or_callback, 'from_user'):
        # Это Message или CallbackQuery
        user_id = message_or_callback.from_user.id
        user_name = message_or_callback.from_user.full_name or str(user_id)
    else:
        # Fallback, если вдруг другой тип объекта
        user_id = getattr(message_or_callback, 'from_user', {}).get('id', 'unknown')
        user_name = getattr(message_or_callback, 'from_user', {}).get('full_name', 'unknown')

    logger.info(f"User {user_name} (ID: {user_id}) searching for game: {query}")

    game = None
    search_source = ""

    try:
        async with httpx.AsyncClient() as client:
            # Сначала ищем в базе данных
            resp = await client.get(
                f"{api_base_url}/api/games/search",
                params={"name": query, "exact": False, "limit": 1},
                timeout=10.0,
            )
            resp.raise_for_status()

            data = resp.json()
            games_db = data.get("games") or []

            if games_db:
                # Нашли в базе данных
                game = games_db[0]
                search_source = "database"
                logger.info(f"Found game in database: {game.get('name')}")
            else:
                # Не нашли в БД, ищем на BGG
                resp = await client.get(
                    f"{api_base_url}/api/bgg/search",
                    params={"name": query, "exact": False, "limit": 1},
                    timeout=30.0,
                )
                resp.raise_for_status()

                data = resp.json()
                games_bgg = data.get("games") or []

                if games_bgg:
                    game = games_bgg[0]
                    search_source = "bgg"
                    logger.info(f"Found game on BGG: {game.get('name')} (rank: #{game.get('rank')})")

                    # Сохраняем игру в базу данных для будущих запросов
                    try:
                        # Добавляем пользовательский запрос в данные игры для сохранения оригинального названия
                        game_data = dict(game)
                        game_data['user_query'] = query

                        async with httpx.AsyncClient() as client:
                            save_resp = await client.post(
                                f"{api_base_url}/api/games/save-from-bgg",
                                json=game_data,
                                timeout=15.0,  # Увеличиваем таймаут для перевода
                            )
                            save_resp.raise_for_status()
                            saved_game_data = save_resp.json()

                            # Обновляем локальные данные игры данными из базы (с переводом)
                            game.update(saved_game_data)
                            logger.info(f"Game saved with translation: {game.get('description_ru') is not None}")
                    except Exception as save_exc:
                        logger.warning(f"Failed to save game to database: {save_exc}")
                        # Продолжаем работу, даже если сохранение не удалось
                else:
                    logger.info(f"No games found for query: {query}")
                    if use_menu_editing and state:
                        from .menu_keyboards import create_back_to_menu_keyboard
                        back_keyboard = create_back_to_menu_keyboard()
                        error_text = "Не нашёл игр с таким названием 😔"
                        if isinstance(message_or_callback, CallbackQuery):
                            await message_or_callback.message.answer(error_text, reply_markup=back_keyboard)
                        else:
                            await message_or_callback.answer(error_text, reply_markup=back_keyboard)
                    else:
                        # Определяем, как отправить сообщение в зависимости от типа объекта
                        if isinstance(message_or_callback, CallbackQuery):
                            await message_or_callback.message.answer("Не нашёл игр с таким названием 😔")
                        else:
                            await message_or_callback.answer("Не нашёл игр с таким названием 😔")
                    return

    except httpx.HTTPStatusError as exc:
        logger.error(f"HTTP error searching for game '{query}': {exc.response.status_code}")
        if use_menu_editing and state:
            from .menu_keyboards import create_back_to_menu_keyboard
            back_keyboard = create_back_to_menu_keyboard()
            error_text = f"Ошибка при запросе к backend: {exc.response.status_code}"
            if isinstance(message_or_callback, CallbackQuery):
                await message_or_callback.message.answer(error_text, reply_markup=back_keyboard)
            else:
                await message_or_callback.answer(error_text, reply_markup=back_keyboard)
        else:
            # Определяем, как отправить сообщение в зависимости от типа объекта
            if isinstance(message_or_callback, CallbackQuery):
                await message_or_callback.message.answer(f"Ошибка при запросе к backend: {exc.response.status_code}")
            else:
                await message_or_callback.answer(f"Ошибка при запросе к backend: {exc.response.status_code}")
        return
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Error searching for game '{query}': {exc}", exc_info=True)
        if use_menu_editing and state:
            from .menu_keyboards import create_back_to_menu_keyboard
            back_keyboard = create_back_to_menu_keyboard()
            error_text = f"Не удалось получить данные об игре: {exc}"
            if isinstance(message_or_callback, CallbackQuery):
                await message_or_callback.message.answer(error_text, reply_markup=back_keyboard)
            else:
                await message_or_callback.answer(error_text, reply_markup=back_keyboard)
        else:
            # Определяем, как отправить сообщение в зависимости от типа объекта
            if isinstance(message_or_callback, CallbackQuery):
                await message_or_callback.message.answer(f"Не удалось получить данные об игре: {exc}")
            else:
                await message_or_callback.answer(f"Не удалось получить данные об игре: {exc}")
        return

    # Извлекаем данные игры (работает для обоих источников)
    # Приоритет: русское название из BGG > английское название
    name = game.get("name_ru") or game.get("name") or "Без названия"
    bgg_id = game.get("bgg_id") or game.get("id")
    year = game.get("yearpublished")
    minplayers = game.get("minplayers")
    maxplayers = game.get("maxplayers")
    playingtime = game.get("playingtime")
    minage = game.get("minage")
    # Для игр из БД используем bgg_rank, для BGG API - rank
    rank = game.get("bgg_rank") or game.get("rank")
    avg = game.get("average")
    bayes = game.get("bayesaverage")
    users = game.get("usersrated")
    weight = game.get("averageweight")
    categories = game.get("categories") or []
    mechanics = game.get("mechanics") or []
    image = game.get("image")
    description = game.get("description")

    # Выбираем описание в зависимости от языка
    if default_language == "ru":
        description_ru = game.get("description_ru")
        if description_ru:
            description = description_ru
        else:
            # Если русского описания нет, добавляем пометку к английскому
            if description:
                description = f"🇬🇧 {description}\n\n<i>Русское описание появится после автоматического перевода</i>"

    logger.info(f"📖 Displaying game '{name}' from {search_source} (rank: #{rank})")

    # Формируем название с ссылкой на BGG, если есть bgg_id
    if bgg_id:
        bgg_url = f"https://boardgamegeek.com/boardgame/{bgg_id}"
        game_title = f'<b><a href="{bgg_url}">{name}</a></b>'
    else:
        game_title = f"<b>{name}</b>"

    lines = [game_title]
    if year:
        lines.append(f"Год: {year}")
    if minplayers or maxplayers:
        if minplayers and maxplayers and minplayers != maxplayers:
            lines.append(f"Игроки: {minplayers}–{maxplayers}")
        else:
            lines.append(f"Игроки: {minplayers or maxplayers}")
    if playingtime:
        lines.append(f"Время: ~{playingtime} мин")
    if minage:
        lines.append(f"Возраст: {minage}+")
    if rank:
        lines.append(f"Мировой рейтинг BGG: #{rank}")
    if avg is not None:
        try:
            lines.append(f"Оценка (avg): {avg:.2f}")
        except Exception:  # noqa: BLE001
            pass
    if bayes is not None:
        lines.append(f"Оценка (Bayes avg): {bayes:.2f}")
    if users:
        lines.append(f"Голосов: {users}")
    if weight is not None:
        try:
            lines.append(f"Сложность (weight): {weight:.2f}/5")
        except Exception:  # noqa: BLE001
            pass
    if categories:
        short = ", ".join(categories[:5])
        lines.append(f"Категории: {short}" + ("…" if len(categories) > 5 else ""))
    if mechanics:
        short = ", ".join(mechanics[:5])
        lines.append(f"Механики: {short}" + ("…" if len(mechanics) > 5 else ""))
    if description:
        # Telegram ограничивает длину сообщения; даём короткий фрагмент
        snippet = description[:350]
        if len(description) > 350:
            snippet += "…"
        lines.append(f"\nОписание: {snippet}")

    text = "\n".join(lines)

    # Импортируем функции меню для редактирования
    from .menu_keyboards import create_back_to_menu_keyboard

    if use_menu_editing and state:
        # Отправляем новое сообщение с результатом
        back_keyboard = create_back_to_menu_keyboard()
        if isinstance(message_or_callback, CallbackQuery):
            # Отправляем новое сообщение вместо редактирования
            if image:
                await message_or_callback.message.answer_photo(photo=image, caption=text, reply_markup=back_keyboard)
            else:
                await message_or_callback.message.answer(text, reply_markup=back_keyboard)
        else:
            # Отправляем новое сообщение
            if image:
                await message_or_callback.answer_photo(photo=image, caption=text, reply_markup=back_keyboard)
            else:
                await message_or_callback.answer(text, reply_markup=back_keyboard)
    else:
        # Обычная отправка сообщений
        if isinstance(message_or_callback, CallbackQuery):
            message = message_or_callback.message
        else:
            message = message_or_callback

        if image:
            await message.answer_photo(photo=image, caption=text)
        else:
            await message.answer(text)


@router.message(Command("game"))
async def cmd_game(message: Message, api_base_url: str, default_language: str) -> None:
    """
    Команда /game <название игры>

    Сначала ищет игру в базе данных, если не найдена - обращается к BGG API.
    Возвращает полную информацию и картинку.
    """

    # Ожидаем, что пользователь напишет: /game Название игры
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Пожалуйста, укажи название игры. Пример:\n/game Terraforming Mars")
        return

    query = parts[1].strip()
    if not query:
        await message.answer("Название игры не должно быть пустым.")
        return

    # Вызываем вспомогательную функцию поиска (для команды используем обычные сообщения)
    await _search_game_impl(message, query, api_base_url, default_language)


@router.message(StateFilter(GameSearchStates.waiting_for_game_name))
async def process_game_name_input(
    message: Message,
    state: FSMContext,
    api_base_url: str,
    default_language: str
) -> None:
    """
    Обрабатывает введенное пользователем название игры при поиске через меню.
    """
    user_id = message.from_user.id
    user_name = message.from_user.full_name or str(user_id)
    query = message.text.strip()

    logger.info(f"User {user_name} (ID: {user_id}) entered game name via menu: {query}")

    # Валидация названия игры
    if not query:
        # Отправляем новое сообщение
        from .menu_keyboards import create_back_to_menu_keyboard
        error_text = "❌ Название игры не должно быть пустым. Введите название игры:"
        back_keyboard = create_back_to_menu_keyboard()
        await message.answer(error_text, reply_markup=back_keyboard)

        return

    if len(query) > 200:
        # Отправляем новое сообщение
        from .menu_keyboards import create_back_to_menu_keyboard
        error_text = "❌ Название игры слишком длинное (максимум 200 символов). Введите короче:"
        back_keyboard = create_back_to_menu_keyboard()
        await message.answer(error_text, reply_markup=back_keyboard)

        return

    # Выполняем поиск игры
    await _search_game_impl(message, query, api_base_url, default_language, state, use_menu_editing=True)

    await state.clear()
    return