"""
Unit tests for application configuration
"""
import pytest
from unittest.mock import patch, MagicMock

from backend.app.config import config as backend_config


class TestBackendConfig:
    """Test backend configuration loading and validation"""

    def test_backend_config_has_required_attributes(self):
        """Test that backend config has all required attributes"""
        required_attrs = [
            'DATABASE_URL', 'DB_HOST', 'DB_USER', 'APP_ENV',
            'DEBUG', 'DEFAULT_LANGUAGE', 'GAME_UPDATE_DAYS',
            'BGG_REQUEST_DELAY', 'BGG_BEARER_TOKEN'
        ]

        for attr in required_attrs:
            assert hasattr(backend_config, attr), f"Missing required config attribute: {attr}"

    def test_backend_config_game_update_days(self):
        """Test GAME_UPDATE_DAYS configuration"""
        assert isinstance(backend_config.GAME_UPDATE_DAYS, int)
        assert backend_config.GAME_UPDATE_DAYS > 0

    def test_backend_config_bgg_request_delay(self):
        """Test BGG_REQUEST_DELAY configuration"""
        assert isinstance(backend_config.BGG_REQUEST_DELAY, (int, float))
        assert backend_config.BGG_REQUEST_DELAY >= 0

    @patch.dict('os.environ', {'DATABASE_URL': 'postgresql://test:test@localhost:5432/test'})
    def test_backend_config_database_url(self):
        """Test DATABASE_URL configuration"""
        # Reload config to pick up environment changes
        from importlib import reload
        import backend.app.config
        reload(backend.app.config)
        from backend.app.config import config as reloaded_config

        assert reloaded_config.DATABASE_URL is not None
        assert 'postgresql://' in reloaded_config.DATABASE_URL

    def test_backend_config_debug_mode(self):
        """Test DEBUG configuration"""
        assert isinstance(backend_config.DEBUG, bool)

    def test_backend_config_default_language(self):
        """Test DEFAULT_LANGUAGE configuration"""
        assert isinstance(backend_config.DEFAULT_LANGUAGE, str)
        assert len(backend_config.DEFAULT_LANGUAGE) == 2  # ISO language code


class TestBotConfig:
    """Test bot configuration loading and validation"""

    @patch('bot.config.os.getenv')
    def test_bot_config_loading(self, mock_getenv):
        """Test bot config loading"""
        mock_getenv.side_effect = lambda key, default=None: {
            'BOT_TOKEN': 'test_token_123',
            'ADMIN_USER_ID': '123456789',
            'API_BASE_URL': 'http://localhost:8000',
            'RATING_SHEET_CSV_URL': 'https://example.com/sheet.csv',
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test'
        }.get(key, default)

        from bot.config import config as bot_config

        assert bot_config.BOT_TOKEN == 'test_token_123'
        assert bot_config.ADMIN_USER_ID == 123456789
        assert bot_config.API_BASE_URL == 'http://localhost:8000'

    @patch('bot.config.os.getenv')
    def test_bot_config_validation_success(self, mock_getenv):
        """Test successful config validation"""
        mock_getenv.side_effect = lambda key, default=None: {
            'BOT_TOKEN': 'test_token_123',
            'ADMIN_USER_ID': '123456789',
            'API_BASE_URL': 'http://localhost:8000',
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test'
        }.get(key, default)

        from bot.config import config as bot_config

        # Should not raise exception
        bot_config.validate()

    @patch('bot.config.os.getenv')
    def test_bot_config_validation_missing_token(self, mock_getenv):
        """Test config validation with missing BOT_TOKEN"""
        mock_getenv.side_effect = lambda key, default=None: {
            'ADMIN_USER_ID': '123456789',
            'API_BASE_URL': 'http://localhost:8000',
        }.get(key, default)

        from bot.config import config as bot_config

        with pytest.raises(ValueError, match="BOT_TOKEN не задан"):
            bot_config.validate()

    @patch('bot.config.os.getenv')
    def test_bot_config_validation_missing_admin_id(self, mock_getenv):
        """Test config validation with missing ADMIN_USER_ID"""
        mock_getenv.side_effect = lambda key, default=None: {
            'BOT_TOKEN': 'test_token_123',
            'API_BASE_URL': 'http://localhost:8000',
        }.get(key, default)

        from bot.config import config as bot_config

        with pytest.raises(ValueError, match="ADMIN_USER_ID не задан"):
            bot_config.validate()

    @patch('bot.config.os.getenv')
    def test_bot_config_admin_user_id_type(self, mock_getenv):
        """Test that ADMIN_USER_ID is converted to int"""
        mock_getenv.side_effect = lambda key, default=None: {
            'BOT_TOKEN': 'test_token_123',
            'ADMIN_USER_ID': '123456789',
        }.get(key, default)

        from bot.config import config as bot_config

        assert isinstance(bot_config.ADMIN_USER_ID, int)
        assert bot_config.ADMIN_USER_ID == 123456789

    @patch('bot.config.os.getenv')
    def test_bot_config_token_masking(self, mock_getenv):
        """Test that BOT_TOKEN is properly masked in string representation"""
        mock_getenv.side_effect = lambda key, default=None: {
            'BOT_TOKEN': 'very_long_token_123456789',
            'ADMIN_USER_ID': '123456789',
        }.get(key, default)

        from bot.config import config as bot_config

        config_str = str(bot_config)
        assert 'very_long_token_123456789' not in config_str
        assert '***6789' in config_str  # Last 5 characters should be visible
