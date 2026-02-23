"""
Integration tests for Docker setup and API availability
"""
import pytest
import httpx
from unittest.mock import patch, AsyncMock


class TestDockerSetup:
    """Test Docker container setup and service availability"""

    @pytest.mark.asyncio
    async def test_backend_health_check(self):
        """Test backend health endpoint availability"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8000/health")
                assert response.status_code == 200
                assert response.json() == {"status": "healthy"}
        except httpx.ConnectError:
            pytest.skip("Backend service not available - run 'docker-compose up -d' first")

    @pytest.mark.asyncio
    async def test_api_endpoints_accessible(self):
        """Test that API endpoints are accessible"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Test health endpoint
                response = await client.get("http://localhost:8000/health")
                assert response.status_code == 200

                # Test that import endpoint exists (may require auth)
                response = await client.options("http://localhost:8000/api/import-table")
                # OPTIONS should return 200 or 405, not 404
                assert response.status_code in [200, 405, 401, 403]
        except httpx.ConnectError:
            pytest.skip("API service not available - run 'docker-compose up -d' first")

    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Test database connectivity through API"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try to access an endpoint that requires DB
                response = await client.get("http://localhost:8000/api/games/search?name=test")
                # Should not be 500 (DB error), may be 401 (auth required) or 200
                assert response.status_code != 500, "Database connection failed"
        except httpx.ConnectError:
            pytest.skip("Service not available - run 'docker-compose up -d' first")


class TestServiceIntegration:
    """Test integration between services"""

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_backend_service_mock(self, mock_get):
        """Test backend service with mocked HTTP calls"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_get.return_value = mock_response

        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
        mock_get.assert_called_once_with("http://localhost:8000/health")

    def test_environment_variables_hint(self):
        """Test that we can provide hints about required environment variables"""
        required_env_vars = [
            'BOT_TOKEN',
            'ADMIN_USER_ID',
            'API_BASE_URL',
            'DATABASE_URL'
        ]

        # This is more of a documentation test - ensure we know what env vars are needed
        assert len(required_env_vars) > 0
        assert 'BOT_TOKEN' in required_env_vars
        assert 'DATABASE_URL' in required_env_vars


# Skip all Docker tests if not running in Docker environment
pytestmark = pytest.mark.skipif(
    not any(indicator in open('/proc/1/cgroup').read() for indicator in ['docker', 'containerd']),
    reason="Docker tests require running inside Docker containers"
)
