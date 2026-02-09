from flask import Blueprint, jsonify, request

from app.domain.models import FirstTier, Game, RankingRequest, SecondTier
from app.domain.services import rank_games
from app.infrastructure.db import SessionLocal
from app.infrastructure.repositories import replace_all_from_table
from app.services.ranking import RankingService

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.post("/rank")
def rank():
    payload = request.get_json(force=True) or {}
    games_payload = payload.get("games", [])
    top_n = int(payload.get("top_n", 50))

    games = [Game(id=item["id"], name=item["name"]) for item in games_payload]
    ranking_request = RankingRequest(games=games, top_n=top_n)

    result = rank_games(ranking_request)

    return jsonify(
        {
            "ranked_games": [
                {"id": rg.game.id, "name": rg.game.name, "rank": rg.rank}
                for rg in result.ranked_games
            ]
        }
    )


@api_bp.post("/import-table")
def import_table():
    """
    Импортирует данные из таблицы в БД.
    """
    payload = request.get_json(force=True) or {}
    rows = payload.get("rows") or []

    db = SessionLocal()
    try:
        replace_all_from_table(db, rows)
        db.commit()
        return jsonify({"status": "ok", "games_imported": len(rows)})
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        return (
            jsonify({"status": "error", "message": str(exc)}),
            400,
        )
    finally:
        db.close()


@api_bp.post("/ranking/start")
def ranking_start():
    """
    Стартует сессию ранжирования для пользователя.
    Ожидает: {"user_name": "Имя"}
    """
    payload = request.get_json(force=True) or {}
    user_name = payload.get("user_name")
    if not user_name:
        return jsonify({"error": "user_name is required"}), 400

    db = SessionLocal()
    service = RankingService(db)
    try:
        data = service.start_session(user_name=user_name)
        db.commit()
        return jsonify(data)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        return jsonify({"error": str(exc)}), 400
    finally:
        db.close()


@api_bp.post("/ranking/answer-first")
def ranking_answer_first():
    """
    Ответ пользователя на первом этапе (плохо / хорошо / отлично).
    Ожидает: {"session_id": int, "game_id": int, "tier": "bad|good|excellent"}
    """
    payload = request.get_json(force=True) or {}
    session_id = payload.get("session_id")
    game_id = payload.get("game_id")
    tier_str = payload.get("tier")

    if session_id is None or game_id is None or tier_str is None:
        return jsonify({"error": "session_id, game_id и tier обязательны"}), 400

    try:
        tier = FirstTier(tier_str)
    except ValueError:
        return jsonify({"error": f"Некорректное значение tier: {tier_str}"}), 400

    db = SessionLocal()
    service = RankingService(db)
    try:
        data = service.answer_first_tier(
            session_id=int(session_id),
            game_id=int(game_id),
            tier=tier,
        )
        db.commit()
        return jsonify(data)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        return jsonify({"error": str(exc)}), 400
    finally:
        db.close()


@api_bp.post("/ranking/answer-second")
def ranking_answer_second():
    """
    Ответ пользователя на втором этапе (супер круто / круто / отлично).
    Ожидает: {"session_id": int, "game_id": int, "tier": "super_cool|cool|excellent"}
    """
    payload = request.get_json(force=True) or {}
    session_id = payload.get("session_id")
    game_id = payload.get("game_id")
    tier_str = payload.get("tier")

    if session_id is None or game_id is None or tier_str is None:
        return jsonify({"error": "session_id, game_id и tier обязательны"}), 400

    try:
        tier = SecondTier(tier_str)
    except ValueError:
        return jsonify({"error": f"Некорректное значение tier: {tier_str}"}), 400

    db = SessionLocal()
    service = RankingService(db)
    try:
        data = service.answer_second_tier(
            session_id=int(session_id),
            game_id=int(game_id),
            tier=tier,
        )
        db.commit()
        return jsonify(data)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        return jsonify({"error": str(exc)}), 400
    finally:
        db.close()
