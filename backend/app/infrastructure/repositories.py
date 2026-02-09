from typing import Dict, List, Any

from sqlalchemy.orm import Session

from .models import GameModel, RatingModel


def replace_all_from_table(session: Session, rows: List[Dict[str, Any]]) -> None:
    """
    Полностью пересоздает данные об играх и оценках на основе табличных данных.

    Ожидаемый формат rows:
    [
        {
            "name": str,
            "bgg_rank": int | None,
            "niza_games_rank": int | None,
            "genre": str | None,
            "ratings": { "user_name": int, ... }
        },
        ...
    ]
    """
    # Сначала очищаем старые данные
    session.query(RatingModel).delete()
    session.query(GameModel).delete()

    for row in rows:
        game = GameModel(
            name=row.get("name"),
            bgg_rank=row.get("bgg_rank"),
            niza_games_rank=row.get("niza_games_rank"),
            genre=row.get("genre"),
        )
        session.add(game)
        session.flush()  # чтобы получить game.id

        ratings = row.get("ratings") or {}
        for user_name, rank in ratings.items():
            rating = RatingModel(
                user_name=user_name,
                game_id=game.id,
                rank=int(rank),
            )
            session.add(rating)


