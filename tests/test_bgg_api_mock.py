"""
Unit tests for BGG API interactions with mocked responses
"""
import pytest
from unittest.mock import patch, MagicMock


class TestBGGApiMock:
    """Test BGG API calls with mocked responses"""

    @patch('backend.app.services.bgg.requests.get')
    def test_search_boardgame_success(self, mock_get):
        """Test successful boardgame search"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '''<?xml version="1.0" encoding="utf-8"?>
<items>
    <item type="boardgame" id="167791">
        <name value="Terraforming Mars"/>
        <yearpublished value="2016"/>
    </item>
    <item type="boardgame" id="123456">
        <name value="Some Other Game"/>
        <yearpublished value="2020"/>
    </item>
</items>'''
        mock_get.return_value = mock_response

        from backend.app.services.bgg import search_boardgame
        results = search_boardgame("Terraforming Mars")

        assert len(results) == 2
        assert results[0]["id"] == 167791
        assert results[0]["name"] == "Terraforming Mars"
        assert results[0]["yearpublished"] == 2016

    @patch('backend.app.services.bgg.requests.get')
    def test_get_boardgame_details_success(self, mock_get):
        """Test successful boardgame details retrieval"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '''<?xml version="1.0" encoding="utf-8"?>
<items>
    <item type="boardgame" id="167791">
        <name value="Terraforming Mars"/>
        <yearpublished value="2016"/>
        <minplayers value="1"/>
        <maxplayers value="5"/>
        <playingtime value="120"/>
        <description>This is a description</description>
        <statistics>
            <ratings>
                <usersrated value="75000"/>
                <average value="8.43"/>
                <bayesaverage value="8.35"/>
                <ranks>
                    <rank type="subtype" name="boardgame" value="1"/>
                </ranks>
            </ratings>
        </statistics>
    </item>
</items>'''
        mock_get.return_value = mock_response

        from backend.app.services.bgg import get_boardgame_details
        result = get_boardgame_details(167791)

        assert result is not None
        assert result["id"] == 167791
        assert result["name"] == "Terraforming Mars"
        assert result["yearpublished"] == 2016
        assert result["rank"] == 1
        assert result["usersrated"] == 75000
        assert result["average"] == 8.43

    @patch('backend.app.services.bgg.requests.get')
    def test_search_boardgame_no_results(self, mock_get):
        """Test search with no results"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '''<?xml version="1.0" encoding="utf-8"?>
<items>
</items>'''
        mock_get.return_value = mock_response

        from backend.app.services.bgg import search_boardgame
        results = search_boardgame("NonExistentGame12345")

        assert len(results) == 0

    @patch('backend.app.services.bgg.requests.get')
    def test_get_boardgame_details_not_found(self, mock_get):
        """Test getting details for non-existent game"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '''<?xml version="1.0" encoding="utf-8"?>
<items>
</items>'''
        mock_get.return_value = mock_response

        from backend.app.services.bgg import get_boardgame_details
        result = get_boardgame_details(999999)

        assert result is None

    @patch('backend.app.services.bgg.requests.get')
    def test_search_boardgame_exact_match(self, mock_get):
        """Test exact match search"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '''<?xml version="1.0" encoding="utf-8"?>
<items>
    <item type="boardgame" id="167791">
        <name value="Terraforming Mars"/>
        <yearpublished value="2016"/>
    </item>
</items>'''
        mock_get.return_value = mock_response

        from backend.app.services.bgg import search_boardgame
        results = search_boardgame("Terraforming Mars", exact=True)

        # exact=True should still work the same way in our implementation
        assert len(results) == 1
        assert results[0]["name"] == "Terraforming Mars"


class TestBGGApiErrorHandling:
    """Test error handling in BGG API calls"""

    @patch('backend.app.services.bgg.requests.get')
    def test_search_boardgame_http_error(self, mock_get):
        """Test HTTP error handling in search"""
        mock_get.side_effect = Exception("Connection failed")

        from backend.app.services.bgg import search_boardgame

        with pytest.raises(RuntimeError, match="Ошибка обращения к BGG API"):
            search_boardgame("Test Game")

    @patch('backend.app.services.bgg.requests.get')
    def test_get_boardgame_details_http_error(self, mock_get):
        """Test HTTP error handling in details retrieval"""
        mock_get.side_effect = Exception("Connection failed")

        from backend.app.services.bgg import get_boardgame_details

        with pytest.raises(RuntimeError, match="Ошибка обращения к BGG API"):
            get_boardgame_details(12345)

    @patch('backend.app.services.bgg.requests.get')
    def test_search_boardgame_empty_response(self, mock_get):
        """Test handling of empty response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = ""
        mock_get.return_value = mock_response

        from backend.app.services.bgg import search_boardgame

        with pytest.raises(RuntimeError, match="Пустой ответ от BGG"):
            search_boardgame("Test Game")