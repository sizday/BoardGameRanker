import logging
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.bgg import search_boardgame, get_boardgame_details

logger = logging.getLogger(__name__)

router = APIRouter()


class BGGGameDetails(BaseModel):
    id: int | None
    name: str | None
    yearpublished: int | None
    minplayers: int | None = None
    maxplayers: int | None = None
    playingtime: int | None = None
    minplaytime: int | None = None
    maxplaytime: int | None = None
    minage: int | None = None
    rank: int | None
    average: float | None = None
    bayesaverage: float | None
    usersrated: int | None
    numcomments: int | None = None
    owned: int | None = None
    trading: int | None = None
    wanting: int | None = None
    wishing: int | None = None
    averageweight: float | None = None
    numweights: int | None = None
    image: str | None
    thumbnail: str | None
    description: str | None = None
    description_ru: str | None = None
    categories: list[str] | None = None
    mechanics: list[str] | None = None
    designers: list[str] | None = None
    publishers: list[str] | None = None


class BGGSearchResponse(BaseModel):
    games: List[BGGGameDetails]


@router.get("/bgg/search", response_model=BGGSearchResponse)
async def bgg_search(name: str, exact: bool = False, limit: int = 5) -> BGGSearchResponse:
    """
    Поиск игр на BGG по названию с возвратом подробной информации,
    включая мировой рейтинг и URL изображений.
    
    :param name: Название игры для поиска
    :param exact: Если True, ищет только точные совпадения
    :param limit: Максимальное количество игр, для которых загружаются детали (по умолчанию 5)
    """
    logger.info(f"API запрос на поиск игры: name='{name}', exact={exact}, limit={limit}")
    try:
        found = search_boardgame(name, exact=exact)
        if not found:
            logger.warning(f"Поиск не дал результатов для запроса: name='{name}', exact={exact}")
            return BGGSearchResponse(games=[])

        # Загружаем детали для большего количества игр, чтобы иметь данные для сортировки
        # Берем в 3 раза больше, чем нужно, для лучшей сортировки
        candidates_limit = min(len(found), limit * 3)
        logger.info(f"Найдено {len(found)} игр, загружаем детали для {candidates_limit} кандидатов для сортировки...")

        candidates: List[BGGGameDetails] = []
        for idx, item in enumerate(found[:candidates_limit], 1):
            try:
                game_id = item.get("id")
                if not game_id:
                    logger.warning(f"Пропущен item без id: {item}")
                    continue
                logger.debug(f"Загрузка деталей игры {idx}/{candidates_limit}: game_id={game_id}")
                details = get_boardgame_details(game_id)
                candidates.append(BGGGameDetails(**details))
            except Exception as e:
                logger.error(f"Ошибка при загрузке деталей игры game_id={item.get('id')}: {e}", exc_info=True)
                # Продолжаем обработку остальных игр

        # Сортируем результаты по релевантности:
        # 1. Сначала игры с точным совпадением названия (без учета регистра)
        # 2. Затем по мировому рейтингу (меньше число = выше рейтинг)
        # 3. Наконец по количеству голосов (больше = лучше)
        def sort_key(game: BGGGameDetails) -> tuple:
            game_name = (game.name or '').lower()
            query_name = name.lower()
            exact_match = game_name == query_name
            rank = game.rank or 999999  # Если нет рейтинга, ставим в конец
            users_rated = game.usersrated or 0
            return (0 if exact_match else 1, rank, -users_rated)  # exact_match первым, затем лучший рейтинг, затем больше голосов

        candidates_sorted = sorted(candidates, key=sort_key)
        logger.info(f"Результаты отсортированы по релевантности. Первый результат: '{candidates_sorted[0].name}' (rank: {candidates_sorted[0].rank})")

        # Возвращаем только запрошенное количество лучших результатов
        games = candidates_sorted[:limit]
        logger.info(f"Возвращаем {len(games)} лучших результатов из {len(candidates_sorted)} кандидатов")

        return BGGSearchResponse(games=games)
    except ValueError as exc:
        logger.error(f"Ошибка конфигурации BGG: {exc}")
        raise HTTPException(status_code=500, detail=f"Ошибка конфигурации BGG: {exc}")
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Ошибка при обращении к BGG API: {exc}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Ошибка при обращении к BGG: {exc}")



