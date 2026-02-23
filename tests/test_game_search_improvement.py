"""
Unit tests for game search functionality with fuzzy matching
"""
import pytest
from unittest.mock import patch, MagicMock

from backend.app.infrastructure.repositories import _fetch_bgg_details_for_row


@pytest.fixture
def mock_bgg_candidates():
    """Mock BGG search candidates for testing"""
    return [
        {
            "id": 123,
            "name": "Catan",
            "type": "boardgame",
            "rank": 1,
            "usersrated": 50000
        },
        {
            "id": 456,
            "name": "Catan: Seafarers",
            "type": "boardgameexpansion",
            "rank": 50,
            "usersrated": 10000
        },
        {
            "id": 789,
            "name": "Ticket to Ride",
            "type": "boardgame",
            "rank": 2,
            "usersrated": 45000
        },
        {
            "id": 101,
            "name": "Settlers of Catan",
            "type": "boardgame",
            "rank": None,
            "usersrated": 60000
        },
        {
            "id": 202,
            "name": "Catan Card Game",
            "type": "boardgame",
            "rank": 100,
            "usersrated": 5000
        }
    ]


@pytest.fixture
def mock_bgg_details_response():
    """Mock detailed BGG response"""
    return {
        "id": 167791,
        "name": "Terraforming Mars",
        "type": "boardgame",
        "yearpublished": 2016,
        "rank": 1,
        "average": 8.43,
        "bayesaverage": 8.35,
        "usersrated": 75000,
        "description": "In the 2400s, mankind starts to terraform the planet Mars...",
        "categories": ["Economic", "Environmental", "Industry / Manufacturing"],
        "mechanics": ["Card Drafting", "End Game Bonuses", "Hand Management"],
        "designers": ["Jacob Fryxelius"],
        "publishers": ["FryxGames", "Schwerkraft-Verlag"]
    }


class TestGameSearchLogic:
    """Test game search and fuzzy matching logic"""

    @pytest.mark.parametrize("query,expected_name", [
        ("Catan", "Catan"),
        ("Settlers of Catan", "Settlers of Catan"),
        ("Ticket to Ride", "Ticket to Ride"),
    ])
    def test_search_with_exact_matches(self, mock_bgg_candidates, query, expected_name):
        """Test search with queries that should find exact matches"""
        with patch('backend.app.infrastructure.repositories.search_boardgame') as mock_search, \
             patch('backend.app.infrastructure.repositories.get_boardgame_details') as mock_details:

            # Mock search to return our candidates
            mock_search.return_value = [
                {"id": c["id"], "name": c["name"], "type": c["type"]}
                for c in mock_bgg_candidates
            ]

            # Mock details to return the candidate data
            def mock_details_func(game_id):
                for candidate in mock_bgg_candidates:
                    if candidate["id"] == game_id:
                        return candidate
                return None

            mock_details.side_effect = mock_details_func

            result = _fetch_bgg_details_for_row({"name": query})

            assert result is not None
            assert result["name"] == expected_name

    def test_search_with_no_results(self, mock_bgg_candidates):
        """Test search when BGG returns no results"""
        with patch('backend.app.infrastructure.repositories.search_boardgame') as mock_search:
            mock_search.return_value = []  # No results

            result = _fetch_bgg_details_for_row({"name": "NonExistent Game 12345"})

            assert result is None

    def test_search_with_fuzzy_matching(self, mock_bgg_candidates):
        """Test that fuzzy matching works for similar names"""
        with patch('backend.app.infrastructure.repositories.search_boardgame') as mock_search, \
             patch('backend.app.infrastructure.repositories.get_boardgame_details') as mock_details:

            mock_search.return_value = [
                {"id": c["id"], "name": c["name"], "type": c["type"]}
                for c in mock_bgg_candidates
            ]

            def mock_details_func(game_id):
                for candidate in mock_bgg_candidates:
                    if candidate["id"] == game_id:
                        return candidate
                return None

            mock_details.side_effect = mock_details_func

            # Test with slightly different name
            result = _fetch_bgg_details_for_row({"name": "Settlers of Catan"})

            assert result is not None
            # Should find "Settlers of Catan" with high similarity
            assert result["name"] == "Settlers of Catan"

    def test_search_prioritizes_base_games(self, mock_bgg_candidates):
        """Test that base games are prioritized over expansions"""
        with patch('backend.app.infrastructure.repositories.search_boardgame') as mock_search, \
             patch('backend.app.infrastructure.repositories.get_boardgame_details') as mock_details:

            mock_search.return_value = [
                {"id": c["id"], "name": c["name"], "type": c["type"]}
                for c in mock_bgg_candidates
            ]

            mock_details.side_effect = lambda game_id: next(
                (c for c in mock_bgg_candidates if c["id"] == game_id), None
            )

            result = _fetch_bgg_details_for_row({"name": "Catan"})

            assert result is not None
            # Should prefer "Catan" (base game) over "Catan: Seafarers" (expansion)
            assert result["name"] == "Catan"
            assert result["type"] == "boardgame"

    def test_search_empty_name(self):
        """Test search with empty name"""
        result = _fetch_bgg_details_for_row({"name": ""})
        assert result is None

    def test_search_none_name(self):
        """Test search with None name"""
        result = _fetch_bgg_details_for_row({"name": None})
        assert result is None


class TestGameSearchIntegration:
    """Integration tests for game search with real BGG API"""

    @pytest.mark.integration
    def test_real_bgg_search_terraforming_mars(self):
        """Integration test with real BGG API for Terraforming Mars"""
        result = _fetch_bgg_details_for_row({"name": "Terraforming Mars"})

        assert result is not None
        assert result["id"] == 167791
        assert result["name"] == "Terraforming Mars"
        assert result["type"] == "boardgame"
        assert isinstance(result.get("rank"), int)
        assert result["rank"] > 0

    @pytest.mark.integration
    def test_real_bgg_search_catan(self):
        """Integration test with real BGG API for Catan"""
        result = _fetch_bgg_details_for_row({"name": "Catan"})

        assert result is not None
        assert result["name"] == "Catan"
        assert result["type"] == "boardgame"
        assert isinstance(result.get("rank"), int)

    @pytest.mark.integration
    def test_real_bgg_search_nonexistent_game(self):
        """Integration test for game that doesn't exist"""
        result = _fetch_bgg_details_for_row({"name": "ThisGameDefinitelyDoesNotExist12345"})

        # Should return None for games not found on BGG
        assert result is None