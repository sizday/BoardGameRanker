import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID
from sqlalchemy.orm import Session

from app.domain.models import FirstTier, Game, RankingRequest, SecondTier
from app.domain.services import rank_games
from app.infrastructure.db import get_db
from app.services.ranking import RankingService

logger = logging.getLogger(__name__)

router = APIRouter()


class GameItem(BaseModel):
    id: UUID
    name: str
    usersrated: int | None = None
    yearpublished: int | None = None
    bgg_rank: int | None = None
    average: float | None = None
    bayesaverage: float | None = None
    averageweight: float | None = None
    minplayers: int | None = None
    maxplayers: int | None = None
    playingtime: int | None = None
    minage: int | None = None
    image: str | None = None
    thumbnail: str | None = None


class RankGamesRequest(BaseModel):
    games: List[GameItem]
    top_n: int = 50


class RankGamesResponse(BaseModel):
    ranked_games: List[GameItem]


class RankingStartRequest(BaseModel):
    user_id: str


class RankingStartResponse(BaseModel):
    session_id: int
    game: GameItem


class RankingAnswerRequest(BaseModel):
    session_id: int
    game_id: int
    tier: str


class RankingAnswerResponse(BaseModel):
    phase: str
    next_game: GameItem | None = None
    top: List[GameItem] | None = None
    message: str = ""


@router.post("/rank", response_model=RankGamesResponse, tags=["ranking"])
async def rank_games_endpoint(request: RankGamesRequest):
    """
    Rank games based on provided list using comparison algorithm.

    Returns top N games from the provided list, ranked by preference.
    """
    logger.info(f"Ranking request received: {len(request.games)} games, top_n={request.top_n}")
    games = [Game(id=item.id, name=item.name) for item in request.games]
    ranking_request = RankingRequest(games=games, top_n=request.top_n)

    result = rank_games(ranking_request)
    logger.info(f"Ranking completed: {len(result.ranked_games)} games ranked")

    return RankGamesResponse(
        ranked_games=[
            GameItem(
                id=rg.game.id,
                name=rg.game.name,
                usersrated=rg.game.usersrated,
                yearpublished=getattr(rg.game, "yearpublished", None),
                bgg_rank=getattr(rg.game, "bgg_rank", None),
                average=getattr(rg.game, "average", None),
                bayesaverage=getattr(rg.game, "bayesaverage", None),
                averageweight=getattr(rg.game, "averageweight", None),
                minplayers=getattr(rg.game, "minplayers", None),
                maxplayers=getattr(rg.game, "maxplayers", None),
                playingtime=getattr(rg.game, "playingtime", None),
                minage=getattr(rg.game, "minage", None),
                image=getattr(rg.game, "image", None),
                thumbnail=getattr(rg.game, "thumbnail", None),
            )
            for rg in result.ranked_games
        ]
    )


@router.post("/ranking/start", response_model=RankingStartResponse, tags=["ranking"])
async def ranking_start(request: RankingStartRequest, db: Session = Depends(get_db)):
    """
    Start an interactive ranking session for a user.

    Initializes a new ranking session and returns the first set of games
    to compare for tier classification.
    """
    logger.info(f"Starting ranking session for user_id: {request.user_id}")
    if not request.user_id:
        logger.warning("Ranking start request without user_id")
        raise HTTPException(status_code=400, detail="user_id is required")

    service = RankingService(db)
    try:
        # Получаем имя пользователя по user_id для обратной совместимости с RankingService
        from app.infrastructure.models import UserModel
        from uuid import UUID
        user = db.query(UserModel).filter(UserModel.id == UUID(request.user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        data = service.start_session(user_name=user.name)
        db.commit()
        logger.info(f"Ranking session started: session_id={data['session_id']}, total_games={data.get('total_games', 0)}")
        return RankingStartResponse(
            session_id=data["session_id"],
            game=GameItem(
                id=data["game"]["id"],
                name=data["game"]["name"],
                usersrated=data["game"].get("usersrated"),
                yearpublished=data["game"].get("yearpublished"),
                bgg_rank=data["game"].get("bgg_rank"),
                average=data["game"].get("average"),
                bayesaverage=data["game"].get("bayesaverage"),
                averageweight=data["game"].get("averageweight"),
                minplayers=data["game"].get("minplayers"),
                maxplayers=data["game"].get("maxplayers"),
                playingtime=data["game"].get("playingtime"),
                minage=data["game"].get("minage"),
                image=data["game"].get("image"),
                thumbnail=data["game"].get("thumbnail"),
            ),
        )
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.error(f"Error starting ranking session for user_id {request.user_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/ranking/answer-first", response_model=RankingAnswerResponse, tags=["ranking"])
async def ranking_answer_first(
    request: RankingAnswerRequest, db: Session = Depends(get_db)
):
    """
    Submit user answer for first tier ranking.

    Records user's tier classification (bad/good/excellent) for a game
    in the current ranking session.
    """
    logger.debug(f"First tier answer: session_id={request.session_id}, game_id={request.game_id}, tier={request.tier}")
    if request.session_id is None or request.game_id is None or request.tier is None:
        logger.warning("First tier answer request with missing required fields")
        raise HTTPException(
            status_code=400, detail="session_id, game_id, and tier are required"
        )

    try:
        tier = FirstTier(request.tier)
    except ValueError:
        logger.warning(f"Invalid tier value: {request.tier}")
        raise HTTPException(
            status_code=400, detail=f"Некорректное значение tier: {request.tier}"
        )

    service = RankingService(db)
    try:
        data = service.answer_first_tier(
            session_id=request.session_id,
            game_id=request.game_id,
            tier=tier,
        )
        db.commit()
        logger.info(f"First tier answer processed: session_id={request.session_id}, phase={data.get('phase')}, answered={data.get('answered', 0)}/{data.get('total', 0)}")

        # Build response
        response_data: dict = {"phase": data.get("phase")}

        if data.get("phase") in ["first_tier", "second_tier"] and "next_game" in data:
            response_data["next_game"] = GameItem(
                id=data["next_game"]["id"],
                name=data["next_game"]["name"],
                usersrated=data["next_game"].get("usersrated"),
                yearpublished=data["next_game"].get("yearpublished"),
                bgg_rank=data["next_game"].get("bgg_rank"),
                average=data["next_game"].get("average"),
                bayesaverage=data["next_game"].get("bayesaverage"),
                averageweight=data["next_game"].get("averageweight"),
                minplayers=data["next_game"].get("minplayers"),
                maxplayers=data["next_game"].get("maxplayers"),
                playingtime=data["next_game"].get("playingtime"),
                minage=data["next_game"].get("minage"),
                image=data["next_game"].get("image"),
                thumbnail=data["next_game"].get("thumbnail"),
            )

        if data.get("phase") == "final" and "top" in data:
            response_data["top"] = [
                GameItem(
                    id=item["id"],
                    name=item["name"],
                    usersrated=item.get("usersrated"),
                    yearpublished=item.get("yearpublished"),
                    bgg_rank=item.get("bgg_rank"),
                    average=item.get("average"),
                    bayesaverage=item.get("bayesaverage"),
                    averageweight=item.get("averageweight"),
                    image=item.get("image"),
                    thumbnail=item.get("thumbnail"),
                )
                for item in data["top"]
            ]

        if data.get("phase") == "completed" and "message" in data:
            response_data["message"] = data["message"]

        return RankingAnswerResponse(**response_data)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.error(f"Error processing first tier answer: session_id={request.session_id}, game_id={request.game_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/ranking/answer-second", response_model=RankingAnswerResponse, tags=["ranking"])
async def ranking_answer_second(
    request: RankingAnswerRequest, db: Session = Depends(get_db)
):
    """
    Submit user answer for second tier ranking.

    Records user's refined tier classification (super_cool/cool/excellent)
    for a game in the current ranking session.
    """
    logger.debug(f"Second tier answer: session_id={request.session_id}, game_id={request.game_id}, tier={request.tier}")
    if request.session_id is None or request.game_id is None or request.tier is None:
        logger.warning("Second tier answer request with missing required fields")
        raise HTTPException(
            status_code=400, detail="session_id, game_id, and tier are required"
        )

    try:
        tier = SecondTier(request.tier)
    except ValueError:
        logger.warning(f"Invalid tier value: {request.tier}")
        raise HTTPException(
            status_code=400, detail=f"Некорректное значение tier: {request.tier}"
        )

    service = RankingService(db)
    try:
        data = service.answer_second_tier(
            session_id=request.session_id,
            game_id=request.game_id,
            tier=tier,
        )
        db.commit()
        logger.info(f"Second tier answer processed: session_id={request.session_id}, phase={data.get('phase')}, answered={data.get('answered', 0)}/{data.get('total', 0)}")

        # Build response
        response_data: dict = {"phase": data.get("phase")}

        if data.get("phase") in ["first_tier", "second_tier"] and "next_game" in data:
            response_data["next_game"] = GameItem(
                id=data["next_game"]["id"],
                name=data["next_game"]["name"],
                usersrated=data["next_game"].get("usersrated"),
                yearpublished=data["next_game"].get("yearpublished"),
                bgg_rank=data["next_game"].get("bgg_rank"),
                average=data["next_game"].get("average"),
                bayesaverage=data["next_game"].get("bayesaverage"),
                averageweight=data["next_game"].get("averageweight"),
                minplayers=data["next_game"].get("minplayers"),
                maxplayers=data["next_game"].get("maxplayers"),
                playingtime=data["next_game"].get("playingtime"),
                minage=data["next_game"].get("minage"),
                image=data["next_game"].get("image"),
                thumbnail=data["next_game"].get("thumbnail"),
            )

        if data.get("phase") == "final" and "top" in data:
            response_data["top"] = [
                GameItem(
                    id=item["id"],
                    name=item["name"],
                    usersrated=item.get("usersrated"),
                    yearpublished=item.get("yearpublished"),
                    bgg_rank=item.get("bgg_rank"),
                    average=item.get("average"),
                    bayesaverage=item.get("bayesaverage"),
                    averageweight=item.get("averageweight"),
                    image=item.get("image"),
                    thumbnail=item.get("thumbnail"),
                )
                for item in data["top"]
            ]

        if data.get("phase") == "completed" and "message" in data:
            response_data["message"] = data["message"]

        return RankingAnswerResponse(**response_data)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.error(f"Error processing second tier answer: session_id={request.session_id}, game_id={request.game_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc))



