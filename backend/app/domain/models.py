from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID


@dataclass
class Game:
    id: UUID
    name: str
    bgg_rank: Optional[int] = None
    niza_games_rank: Optional[int] = None
    genre: Optional["GameGenre"] = None
    usersrated: Optional[int] = None
    yearpublished: Optional[int] = None
    average: Optional[float] = None
    bayesaverage: Optional[float] = None
    averageweight: Optional[float] = None
    minplayers: Optional[int] = None
    maxplayers: Optional[int] = None
    playingtime: Optional[int] = None
    minage: Optional[int] = None


class GameGenre(str, Enum):
    STRATEGY = "strategy"
    FAMILY = "family"
    PARTY = "party"
    COOP = "coop"
    AMERITRASH = "ameri"
    EURO = "euro"
    ABSTRACT = "abstract"


class FirstTier(str, Enum):
    BAD = "bad"
    GOOD = "good"
    EXCELLENT = "excellent"


class SecondTier(str, Enum):
    SUPER_COOL = "super_cool"
    COOL = "cool"
    EXCELLENT = "excellent"


@dataclass
class Rating:
    user_name: str
    game_id: UUID
    rank: int


@dataclass
class RankedGame:
    game: Game
    rank: int


@dataclass
class RankingRequest:
    games: List[Game]
    top_n: int = 50


@dataclass
class RankingResult:
    ranked_games: List[RankedGame]


@dataclass
class FirstTieringState:
    """
    Результат первого прохода (плохо / хорошо / отлично).
    Ключи словаря tiers — это id игры, значения — FirstTier.
    """
    games: List[Game]
    tiers: Dict[UUID, FirstTier]


@dataclass
class SecondTieringState:
    """
    Результат второго прохода (супер круто / круто / отлично) по подмножеству игр.
    """
    candidate_game_ids: List[UUID]
    tiers: Dict[UUID, SecondTier]
