from typing import Dict, Iterable, List, Sequence, Tuple

from .models import (
    FirstTier,
    Game,
    RankingRequest,
    RankingResult,
    RankedGame,
    SecondTier,
)


def rank_games(request: RankingRequest) -> RankingResult:
    """
    Высокоуровневая обертка над алгоритмом.
    Сейчас оставлена как простая заглушка, чтобы не ломать существующий API /rank.
    Основной алгоритм реализован в вспомогательных функциях ниже и будет вызываться
    из бот-/API-специфичных use-case-ов.
    """
    return RankingResult(ranked_games=[])


def select_candidate_game_ids(
    games: Sequence[Game],
    first_tiers: Dict[int, FirstTier],
    top_n: int = 50,
) -> List[int]:
    """
    Этап 2 и 3: по результатам первого прохода (плохо/хорошо/отлично)
    выбираем пул кандидатов для дальнейшего уточнения.

    Логика:
    - если в группе "отлично" больше top_n игр — работаем только с ней;
    - иначе берём "отлично" + "хорошо", обрезая до top_n.
    Порядок игр в результирующем списке сохраняет исходный порядок `games`.
    """
    excellent_ids: List[int] = []
    good_ids: List[int] = []

    for game in games:
        tier = first_tiers.get(game.id)
        if tier is None:
            continue
        if tier == FirstTier.EXCELLENT:
            excellent_ids.append(game.id)
        elif tier == FirstTier.GOOD:
            good_ids.append(game.id)

    if len(excellent_ids) > top_n:
        return excellent_ids[:top_n]

    pool = excellent_ids + good_ids
    return pool[:top_n]


def build_final_top_ids(
    candidate_ids: Iterable[int],
    second_tiers: Dict[int, SecondTier],
    top_n: int = 50,
) -> List[int]:
    """
    Этап 4: по результатам второго прохода (супер круто / круто / отлично)
    собираем финальный список id игр в приоритетном порядке.

    Логика:
    - сначала идут все игры из "супер круто",
    - затем из "круто",
    - затем из "отлично";
    - если каких-то игр нет во втором проходе, считаем их "отлично".
    """
    super_cool: List[int] = []
    cool: List[int] = []
    excellent: List[int] = []

    for game_id in candidate_ids:
        tier = second_tiers.get(game_id, SecondTier.EXCELLENT)
        if tier == SecondTier.SUPER_COOL:
            super_cool.append(game_id)
        elif tier == SecondTier.COOL:
            cool.append(game_id)
        else:
            excellent.append(game_id)

    ordered = super_cool + cool + excellent
    return ordered[:top_n]


def merge_ordered_groups(
    group_orders: Dict[SecondTier, List[int]],
    group_priority: Sequence[SecondTier],
    top_n: int = 50,
) -> List[int]:
    """
    Этап 5: объединяем мини-группы, уже отсортированные пользователем внутри,
    в один общий список id игр.

    group_orders: словарь tier -> список id игр в нужном порядке.
    group_priority: порядок приоритета групп (сильная -> слабая).
    """
    result: List[int] = []

    for tier in group_priority:
        ids = group_orders.get(tier) or []
        for game_id in ids:
            if game_id in result:
                # избегаем дубликатов, если игра случайно попала в две группы
                continue
            result.append(game_id)
            if len(result) >= top_n:
                return result

    return result[:top_n]


def apply_swaps(order: List[int], swaps: Iterable[Tuple[int, int]]) -> List[int]:
    """
    Этап 6: применяет список обменов позиций к уже сформированному топу.

    swaps: список пар (i, j), где i и j — позиции (1-based),
           которые пользователь попросил поменять местами.
    """
    result = list(order)

    for i, j in swaps:
        i_idx = i - 1
        j_idx = j - 1
        if (
            i_idx < 0
            or j_idx < 0
            or i_idx >= len(result)
            or j_idx >= len(result)
        ):
            continue
        result[i_idx], result[j_idx] = result[j_idx], result[i_idx]

    return result


def build_ranked_games(
    games_by_id: Dict[int, Game],
    ordered_ids: Sequence[int],
) -> List[RankedGame]:
    """
    Вспомогательная функция: превращает упорядоченный список id игр
    в список RankedGame с расставленными номерами мест.
    """
    ranked: List[RankedGame] = []

    for idx, game_id in enumerate(ordered_ids, start=1):
        game = games_by_id.get(game_id)
        if game is None:
            continue
        ranked.append(RankedGame(game=game, rank=idx))

    return ranked
