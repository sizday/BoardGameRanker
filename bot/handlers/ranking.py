from __future__ import annotations

import httpx
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message


router = Router()


def _first_tier_keyboard(session_id: int, game_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="😕 Плохо",
                    callback_data=f"first:{session_id}:{game_id}:bad",
                ),
                InlineKeyboardButton(
                    text="🙂 Хорошо",
                    callback_data=f"first:{session_id}:{game_id}:good",
                ),
                InlineKeyboardButton(
                    text="😍 Отлично",
                    callback_data=f"first:{session_id}:{game_id}:excellent",
                ),
            ]
        ]
    )


def _second_tier_keyboard(session_id: int, game_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🤩 Супер круто",
                    callback_data=f"second:{session_id}:{game_id}:super_cool",
                ),
                InlineKeyboardButton(
                    text="😎 Круто",
                    callback_data=f"second:{session_id}:{game_id}:cool",
                ),
                InlineKeyboardButton(
                    text="🙂 Отлично",
                    callback_data=f"second:{session_id}:{game_id}:excellent",
                ),
            ]
        ]
    )


async def _send_first_tier_question(
    message: Message,
    api_base_url: str,
    user_name: str,
) -> None:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{api_base_url}/api/ranking/start",
            json={"user_name": user_name},
            timeout=30.0,
        )
        resp.raise_for_status()

    data = resp.json()
    session_id = data["session_id"]
    game = data["game"]

    text = (
        f"Начинаем формировать твой рейтинг!\n\n"
        f"Игра: <b>{game['name']}</b>\n"
        f"Отметь, насколько она тебе понравилась."
    )
    await message.answer(
        text,
        reply_markup=_first_tier_keyboard(session_id=session_id, game_id=game["id"]),
    )


@router.message(Command("start_ranking"))
async def cmd_start_ranking(message: Message):
    api_base_url = message.bot["api_base_url"]
    user_name = message.from_user.full_name or str(message.from_user.id)

    try:
        await _send_first_tier_question(message, api_base_url, user_name)
    except Exception as exc:  # noqa: BLE001
        await message.answer(f"Не удалось начать ранжирование: {exc}")


@router.callback_query()
async def ranking_callbacks(callback: CallbackQuery):
    """
    Обрабатывает callback-данные для первого и второго этапов ранжирования.
    """
    api_base_url = callback.message.bot["api_base_url"]  # type: ignore[index]
    data = callback.data or ""

    try:
        kind, session_id_str, game_id_str, tier = data.split(":", 3)
        session_id = int(session_id_str)
        game_id = int(game_id_str)
    except Exception:  # noqa: BLE001
        await callback.answer("Некорректные данные.", show_alert=True)
        return

    await callback.answer()

    try:
        async with httpx.AsyncClient() as client:
            if kind == "first":
                resp = await client.post(
                    f"{api_base_url}/api/ranking/answer-first",
                    json={
                        "session_id": session_id,
                        "game_id": game_id,
                        "tier": tier,
                    },
                    timeout=30.0,
                )
            elif kind == "second":
                resp = await client.post(
                    f"{api_base_url}/api/ranking/answer-second",
                    json={
                        "session_id": session_id,
                        "game_id": game_id,
                        "tier": tier,
                    },
                    timeout=30.0,
                )
            else:
                await callback.message.answer("Неизвестный тип действия.")
                return

            resp.raise_for_status()

        payload = resp.json()
        phase = payload.get("phase")

        if phase == "first_tier":
            game = payload["next_game"]
            text = (
                f"Игра: <b>{game['name']}</b>\n"
                f"Отметь, насколько она тебе понравилась."
            )
            await callback.message.edit_text(
                text,
                reply_markup=_first_tier_keyboard(
                    session_id=session_id,
                    game_id=game["id"],
                ),
            )
        elif phase == "second_tier":
            game = payload["next_game"]
            text = (
                "Отлично! Теперь уточним, какие игры прямо топчик.\n\n"
                f"Игра: <b>{game['name']}</b>\n"
                f"Выбери, насколько она крутая."
            )
            await callback.message.edit_text(
                text,
                reply_markup=_second_tier_keyboard(
                    session_id=session_id,
                    game_id=game["id"],
                ),
            )
        elif phase == "final":
            top = payload.get("top", [])
            lines = [f"{item['rank']}. {item['name']}" for item in top]
            text = "Твой предварительный топ-50:\n\n" + "\n".join(lines)
            await callback.message.edit_text(text)
        elif phase == "completed":
            await callback.message.edit_text(payload.get("message", "Готово."))
        else:
            await callback.message.answer("Неожиданное состояние сессии.")
    except Exception as exc:  # noqa: BLE001
        await callback.message.answer(f"Ошибка при обновлении рейтинга: {exc}")


