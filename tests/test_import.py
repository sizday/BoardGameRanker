"""
Unit and integration tests for import functionality
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, Mock

from backend.app.api.import_table import ImportTableRequest


@pytest.fixture
def test_data_path():
    """Path to test data file"""
    return Path(__file__).parent / "test_payload.json"


@pytest.fixture
def sample_import_data(test_data_path):
    """Load sample import data"""
    with open(test_data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


class TestImportDataValidation:
    """Test validation of import data structure"""

    def test_sample_data_structure(self, sample_import_data):
        """Test that sample import data has correct structure"""
        assert "rows" in sample_import_data
        assert isinstance(sample_import_data["rows"], list)
        assert len(sample_import_data["rows"]) > 0

        # Check first row structure
        first_row = sample_import_data["rows"][0]
        required_fields = ['name', 'genre', 'ratings']

        for field in required_fields:
            assert field in first_row, f"Missing required field '{field}' in test data"

    def test_sample_data_content(self, sample_import_data):
        """Test sample data content"""
        rows = sample_import_data["rows"]

        for row in rows:
            # Name should be non-empty string
            assert isinstance(row["name"], str)
            assert len(row["name"].strip()) > 0

            # Genre should be string
            assert isinstance(row["genre"], str)

            # Ratings should be dict
            assert isinstance(row["ratings"], dict)
            assert len(row["ratings"]) > 0

    def test_sample_data_ratings(self, sample_import_data):
        """Test ratings data in sample import"""
        rows = sample_import_data["rows"]

        for row in rows:
            ratings = row["ratings"]
            assert isinstance(ratings, dict)

            # Check that ratings are integers 0-50
            for user, rating in ratings.items():
                assert isinstance(user, str)
                assert isinstance(rating, int)
                assert 0 <= rating <= 50


class TestImportAPIRequest:
    """Test import API request validation"""

    def test_import_request_creation(self, sample_import_data):
        """Test creating ImportTableRequest object"""
        request = ImportTableRequest(
            rows=sample_import_data["rows"],
            is_forced_update=False
        )

        assert len(request.rows) == len(sample_import_data["rows"])
        assert request.is_forced_update is False

    def test_import_request_with_force_update(self, sample_import_data):
        """Test import request with forced update"""
        request = ImportTableRequest(
            rows=sample_import_data["rows"],
            is_forced_update=True
        )

        assert request.is_forced_update is True

    def test_import_request_validation_empty_rows(self):
        """Test validation with empty rows"""
        with pytest.raises(ValueError):
            ImportTableRequest(rows=[], is_forced_update=False)

    def test_import_request_validation_invalid_ratings(self, sample_import_data):
        """Test validation with invalid ratings data"""
        invalid_data = sample_import_data["rows"].copy()
        invalid_data[0]["ratings"] = "invalid_ratings"  # Should be dict

        with pytest.raises(ValueError):
            ImportTableRequest(rows=invalid_data, is_forced_update=False)


class TestImportIntegration:
    """Integration tests for import functionality"""

    @patch("backend.app.infrastructure.repositories.replace_all_from_table")
    def test_import_endpoint_success(self, mock_replace, client, sample_import_data):
        """Test successful import endpoint call"""
        mock_replace.return_value = 2  # Mock successful import of 2 games

        response = client.post(
            "/api/import-table",
            json={
                "rows": sample_import_data["rows"],
                "is_forced_update": False
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["games_imported"] == 2
        assert "Translation started in background" in data["message"]

    def test_import_endpoint_invalid_data(self, client):
        """Test import endpoint with invalid data"""
        response = client.post(
            "/api/import-table",
            json={
                "rows": [{"invalid": "data"}],
                "is_forced_update": False
            }
        )

        assert response.status_code == 400

    @patch("backend.app.infrastructure.repositories.replace_all_from_table")
    def test_import_endpoint_forced_update(self, mock_replace, client, sample_import_data):
        """Test import with forced update flag"""
        mock_replace.return_value = 1

        response = client.post(
            "/api/import-table",
            json={
                "rows": sample_import_data["rows"],
                "is_forced_update": True
            }
        )

        assert response.status_code == 200
        # Verify that replace_all_from_table was called with is_forced_update=True
        mock_replace.assert_called_once()
        args, kwargs = mock_replace.call_args
        assert kwargs["is_forced_update"] is True
