from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from sqlalchemy.orm import Session

from app.domain.models import FirstTier, Game, SecondTier
from app.domain import services as domain_services
from app.infrastructure.models import GameModel, RatingModel, RankingSessionModel


class RankingService:
    """
    Прикладной сервис ранжирования.

    Оркеструет шаги алгоритма, используя:
    - доменные функции (чистая логика) из app.domain.services;
    - инфраструктурные модели для доступа к БД.
    """

    def __init__(self, db: Session):
        self.db = db

    # ---------- Вспомогательные методы ----------

    def _load_games_for_user(self, user_name: str) -> List[Game]:
        games: List[Game] = []

        q = (
            self.db.query(GameModel)
            .join(RatingModel, RatingModel.game_id == GameModel.id)
            .filter(RatingModel.user_name == user_name)
            .order_by(GameModel.id)
        )

        for gm in q.all():
            games.append(
                Game(
                    id=gm.id,
                    name=gm.name,
                    bgg_rank=gm.bgg_rank,
                    niza_games_rank=gm.niza_games_rank,
                    genre=gm.genre,
                )
            )
        return games

    def _get_session(self, session_id: int) -> RankingSessionModel:
        session = self.db.get(RankingSessionModel, session_id)
        if session is None:
            raise ValueError(f"Ranking session {session_id} not found")
        return session

    def _games_by_id(self, game_ids: Sequence[int]) -> Dict[int, Game]:
        if not game_ids:
            return {}
        rows = self.db.query(GameModel).filter(GameModel.id.in_(list(game_ids))).all()
        return {
            gm.id: Game(
                id=gm.id,
                name=gm.name,
                bgg_rank=gm.bgg_rank,
                niza_games_rank=gm.niza_games_rank,
                genre=gm.genre,
            )
            for gm in rows
        }

    # ---------- Публичные методы ----------

    def start_session(self, user_name: str) -> Dict:
        """
        Создаёт новую сессию ранжирования для пользователя и возвращает первую игру.
        """
        games = self._load_games_for_user(user_name)
        if not games:
            raise ValueError("Для пользователя нет ни одной сыгранной игры.")

        games_ids = [g.id for g in games]

        session = RankingSessionModel(
            user_name=user_name,
            state="first_tier",
            games=games_ids,
            first_tiers={},
            second_tiers={},
            candidate_ids=None,
            group_orders=None,
            final_order=None,
            current_index_first=0,
            current_index_second=0,
        )
        self.db.add(session)
        self.db.flush()

        first_game = games[0]
        return {
            "session_id": session.id,
            "game": {"id": first_game.id, "name": first_game.name},
            "total_games": len(games),
        }

    def _next_unrated_game_first(
        self, session: RankingSessionModel, games: List[Game]
    ) -> Optional[Game]:
        rated_ids = set(int(k) for k in (session.first_tiers or {}).keys())

        for idx in range(session.current_index_first, len(games)):
            game = games[idx]
            if game.id not in rated_ids:
                session.current_index_first = idx
                return game
        return None

    def answer_first_tier(
        self,
        session_id: int,
        game_id: int,
        tier: FirstTier,
        top_n: int = 50,
    ) -> Dict:
        """
        Сохраняет ответ пользователя на первом проходе и возвращает следующую игру
        либо информацию о переходе ко второму этапу.
        """
        session = self._get_session(session_id)
        if session.state not in ("first_tier", "second_tier"):
            raise ValueError("Сессия уже прошла этап первого ранжирования.")

        games = self._games_by_id(session.games)
        ordered_games = [games[g_id] for g_id in session.games if g_id in games]

        tiers: Dict[int, str] = dict(session.first_tiers or {})
        tiers[game_id] = tier.value
        session.first_tiers = tiers

        next_game = self._next_unrated_game_first(session, ordered_games)
        if next_game is not None:
            return {
                "phase": "first_tier",
                "next_game": {"id": next_game.id, "name": next_game.name},
                "answered": len(tiers),
                "total": len(ordered_games),
            }

        # Первый проход завершён — выбираем пул кандидатов
        first_tiers_enum: Dict[int, FirstTier] = {
            int(g_id): FirstTier(value)
            for g_id, value in (session.first_tiers or {}).items()
        }
        candidate_ids = domain_services.select_candidate_game_ids(
            ordered_games, first_tiers_enum, top_n=top_n
        )

        session.candidate_ids = candidate_ids
        session.state = "second_tier"
        session.current_index_second = 0

        if not candidate_ids:
            return {
                "phase": "completed",
                "message": "Не удалось набрать кандидатов для топа.",
            }

        candidate_games = [games[g_id] for g_id in candidate_ids if g_id in games]
        first_candidate = candidate_games[0]

        return {
            "phase": "second_tier",
            "next_game": {"id": first_candidate.id, "name": first_candidate.name},
            "candidates": len(candidate_games),
        }

    def _next_unrated_game_second(
        self, session: RankingSessionModel, candidate_games: List[Game]
    ) -> Optional[Game]:
        rated_ids = set(int(k) for k in (session.second_tiers or {}).keys())

        for idx in range(session.current_index_second, len(candidate_games)):
            game = candidate_games[idx]
            if game.id not in rated_ids:
                session.current_index_second = idx
                return game
        return None

    def answer_second_tier(
        self,
        session_id: int,
        game_id: int,
        tier: SecondTier,
        top_n: int = 50,
    ) -> Dict:
        """
        Сохраняет ответ пользователя на втором проходе и,
        если все игры оценены, формирует финальный топ.
        """
        session = self._get_session(session_id)
        if session.state != "second_tier":
            raise ValueError("Сессия не находится на этапе второго ранжирования.")

        if not session.candidate_ids:
            raise ValueError("Для сессии нет списка кандидатов.")

        games = self._games_by_id(session.candidate_ids)
        candidate_games = [games[g_id] for g_id in session.candidate_ids if g_id in games]

        tiers: Dict[int, str] = dict(session.second_tiers or {})
        tiers[game_id] = tier.value
        session.second_tiers = tiers

        next_game = self._next_unrated_game_second(session, candidate_games)
        if next_game is not None:
            return {
                "phase": "second_tier",
                "next_game": {"id": next_game.id, "name": next_game.name},
                "answered": len(tiers),
                "total": len(candidate_games),
            }

        # Второй проход завершён — формируем финальный топ
        second_tiers_enum: Dict[int, SecondTier] = {
            int(g_id): SecondTier(value)
            for g_id, value in (session.second_tiers or {}).items()
        }
        final_ids = domain_services.build_final_top_ids(
            session.candidate_ids,
            second_tiers_enum,
            top_n=top_n,
        )

        session.final_order = final_ids
        session.state = "final"

        ranked_games = domain_services.build_ranked_games(games, final_ids)

        return {
            "phase": "final",
            "top": [
                {"id": rg.game.id, "name": rg.game.name, "rank": rg.rank}
                for rg in ranked_games
            ],
        }


