"""
Integration tests for the complete import workflow
"""
import pytest
from unittest.mock import patch, MagicMock


class TestImportWorkflowIntegration:
    """Test the complete import workflow from API to database"""

    @patch('backend.app.infrastructure.repositories.search_boardgame')
    @patch('backend.app.infrastructure.repositories.get_boardgame_details')
    def test_import_with_bgg_lookup(self, mock_details, mock_search, test_db, sample_import_row):
        """Test import workflow that fetches data from BGG"""
        from backend.app.infrastructure.repositories import replace_all_from_table

        # Mock BGG API responses
        mock_search.return_value = [
            {"id": 167791, "name": "Terraforming Mars", "type": "boardgame"}
        ]

        mock_details.return_value = {
            "id": 167791,
            "name": "Terraforming Mars",
            "type": "boardgame",
            "yearpublished": 2016,
            "rank": 1,
            "average": 8.43,
            "usersrated": 75000,
            "description": "Terraform Mars description",
            "categories": ["Economic"],
            "mechanics": ["Card Drafting"],
            "designers": ["Jacob Fryxelius"],
            "publishers": ["FryxGames"]
        }

        # Perform import
        games_imported = replace_all_from_table(test_db, [sample_import_row])

        assert games_imported == 1

        # Verify game was created in database
        from backend.app.infrastructure.models import GameModel
        game = test_db.query(GameModel).filter(GameModel.name == "Terraforming Mars").first()

        assert game is not None
        assert game.bgg_id == 167791  # Should be set from BGG lookup
        assert game.bgg_rank == 1
        assert game.yearpublished == 2016
        assert game.average == 8.43

    @patch('backend.app.infrastructure.repositories.search_boardgame')
    def test_import_with_no_bgg_results(self, mock_search, test_db, sample_import_row):
        """Test import when BGG returns no results"""
        from backend.app.infrastructure.repositories import replace_all_from_table

        # Mock empty BGG search results
        mock_search.return_value = []

        # Modify sample data to have no bgg_id
        import_data = sample_import_row.copy()
        import_data["name"] = "Unknown Game That Does Not Exist"

        # Perform import
        games_imported = replace_all_from_table(test_db, [import_data])

        assert games_imported == 1

        # Verify game was created but without BGG data
        from backend.app.infrastructure.models import GameModel
        game = test_db.query(GameModel).filter(GameModel.name == "Unknown Game That Does Not Exist").first()

        assert game is not None
        assert game.bgg_id is None  # Should remain None
        assert game.bgg_rank is None

    def test_import_data_validation(self, test_db):
        """Test validation of import data structure"""
        from backend.app.infrastructure.repositories import replace_all_from_table

        # Test with invalid data
        invalid_data = [
            {"name": "", "genre": "test"},  # Empty name
            {"genre": "test", "ratings": {}},  # Missing name
            {"name": "Valid Game", "genre": "test", "ratings": {"user1": 11}},  # Invalid rating
        ]

        # Should handle invalid data gracefully
        games_imported = replace_all_from_table(test_db, invalid_data)

        # Only the valid game should be imported
        assert games_imported == 0  # All invalid

    @patch('backend.app.infrastructure.repositories.search_boardgame')
    @patch('backend.app.infrastructure.repositories.get_boardgame_details')
    def test_import_with_ratings(self, mock_details, mock_search, test_db):
        """Test import with user ratings"""
        from backend.app.infrastructure.repositories import replace_all_from_table
        from backend.app.infrastructure.models import UserModel, RatingModel

        # Create test users
        user1 = UserModel(name="user1", telegram_id=123456)
        user2 = UserModel(name="user2", telegram_id=789012)
        test_db.add_all([user1, user2])
        test_db.commit()

        # Mock BGG responses
        mock_search.return_value = [{"id": 167791, "name": "Terraforming Mars", "type": "boardgame"}]
        mock_details.return_value = {
            "id": 167791,
            "name": "Terraforming Mars",
            "type": "boardgame",
            "yearpublished": 2016,
            "rank": 1
        }

        import_data = {
            "name": "Terraforming Mars",
            "genre": "экономическая",
            "ratings": {
                "user1": 9,
                "user2": 8,
                "nonexistent_user": 7  # Should be ignored
            }
        }

        games_imported = replace_all_from_table(test_db, [import_data])

        assert games_imported == 1

        # Verify ratings were created
        game = test_db.query(GameModel).filter(GameModel.name == "Terraforming Mars").first()
        assert game is not None

        ratings = test_db.query(RatingModel).filter(RatingModel.game_id == game.id).all()
        assert len(ratings) == 2  # Only valid users

        rating_values = {r.rank for r in ratings}
        assert 8 in rating_values
        assert 9 in rating_values

    def test_import_updates_existing_game(self, test_db):
        """Test that import updates existing games"""
        from backend.app.infrastructure.repositories import replace_all_from_table
        from backend.app.infrastructure.models import GameModel

        # Create existing game
        existing_game = GameModel(
            name="Existing Game",
            genre="старое",
            niza_games_rank=10
        )
        test_db.add(existing_game)
        test_db.commit()

        # Import updated data
        import_data = {
            "name": "Existing Game",
            "genre": "новое",
            "niza_games_rank": 5,
            "ratings": {"user1": 8}
        }

        games_imported = replace_all_from_table(test_db, [import_data])

        assert games_imported == 1

        # Verify game was updated
        updated_game = test_db.query(GameModel).filter(GameModel.name == "Existing Game").first()
        assert updated_game.genre == "новое"
        assert updated_game.niza_games_rank == 5