"""
Pytest fixtures and configuration for testing
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.infrastructure.db import Base
from backend.app.infrastructure.models import GameModel, RatingModel, RankingSessionModel


@pytest.fixture
def test_db():
    """Create in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_game_data():
    """Sample game data for testing"""
    return {
        "id": 1,
        "name": "Test Game",
        "bgg_id": 12345,
        "bgg_rank": 100,
        "yearpublished": 2020,
        "average": 7.5,
        "bayesaverage": 7.2,
        "usersrated": 1500,
        "description": "This is a test game description.",
        "description_ru": "Это тестовое описание игры.",
        "image": "https://example.com/image.jpg",
        "thumbnail": "https://example.com/thumb.jpg"
    }


@pytest.fixture
def sample_bgg_response():
    """Sample BGG API response"""
    return {
        "id": 12345,
        "name": "Test Game",
        "yearpublished": 2020,
        "rank": 100,
        "average": 7.5,
        "bayesaverage": 7.2,
        "usersrated": 1500,
        "description": "This is a test game description.",
        "description_ru": None,
        "image": "https://example.com/image.jpg",
        "thumbnail": "https://example.com/thumb.jpg",
        "categories": ["Strategy"],
        "mechanics": ["Worker Placement"]
    }


@pytest.fixture
def mock_bgg_search_response():
    """Mock response from BGG search API"""
    return [
        {"id": 167791, "name": "Terraforming Mars", "type": "boardgame"},
        {"id": 13, "name": "Catan", "type": "boardgame"},
        {"id": 266192, "name": "Wingspan", "type": "boardgame"},
    ]


@pytest.fixture
def mock_bgg_details_response():
    """Mock detailed response from BGG thing API"""
    return {
        "id": 167791,
        "name": "Terraforming Mars",
        "type": "boardgame",
        "yearpublished": 2016,
        "rank": 1,
        "average": 8.43,
        "bayesaverage": 8.35,
        "usersrated": 75000,
        "description": "In the 2400s, mankind begins to terraform the planet Mars...",
        "categories": ["Economic", "Environmental", "Industry / Manufacturing"],
        "mechanics": ["Card Drafting", "End Game Bonuses", "Hand Management"],
        "designers": ["Jacob Fryxelius"],
        "publishers": ["FryxGames", "Schwerkraft-Verlag"]
    }


@pytest.fixture
def sample_import_row():
    """Sample import data row"""
    return {
        "name": "Terraforming Mars",
        "genre": "экономическая",
        "niza_games_rank": 1,
        "bgg_id": 167791,  # This should be ignored in new logic
        "description_ru": "Игра о терраформировании Марса",
        "ratings": {
            "user1": 9,
            "user2": 8,
            "user3": 10
        }
    }


@pytest.fixture
def client_app():
    """FastAPI test client fixture"""
    from fastapi.testclient import TestClient
    from backend.app.main import app

    # Override dependencies for testing
    from backend.app.infrastructure.db import get_db

    def override_get_db():
        # Return test database session
        pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)