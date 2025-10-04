"""
FastAPI endpoint tests for the RAG chatbot system.

Tests the main API endpoints: /api/query and /api/courses
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestQueryEndpoint:
    """Tests for the /api/query endpoint."""

    def test_query_endpoint_exists(self, client):
        """Test that the query endpoint exists and accepts POST requests."""
        response = client.post("/api/query", json={"query": "test"})
        # Should not be 404 or 405
        assert response.status_code != 404
        assert response.status_code != 405

    def test_query_requires_query_field(self, client):
        """Test that query field is required."""
        response = client.post("/api/query", json={})
        assert response.status_code == 422  # Validation error

    def test_query_returns_session_id(self, client):
        """Test that query response includes session_id."""
        response = client.post(
            "/api/query",
            json={"query": "What is MCP?"}
        )
        data = response.json()
        assert "session_id" in data

    def test_query_returns_answer(self, client):
        """Test that query response includes an answer."""
        response = client.post(
            "/api/query",
            json={"query": "What courses are available?"}
        )
        data = response.json()
        assert "answer" in data
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 0

    def test_query_with_session_id(self, client):
        """Test that existing session_id is preserved."""
        # First request
        response1 = client.post(
            "/api/query",
            json={"query": "First question"}
        )
        session_id = response1.json()["session_id"]

        # Second request with same session_id
        response2 = client.post(
            "/api/query",
            json={
                "query": "Follow-up question",
                "session_id": session_id
            }
        )
        assert response2.json()["session_id"] == session_id

    def test_query_handles_empty_string(self, client):
        """Test that empty query string is handled properly."""
        response = client.post(
            "/api/query",
            json={"query": ""}
        )
        # Should either validate (422) or handle gracefully (200)
        assert response.status_code in [200, 422]


class TestCoursesEndpoint:
    """Tests for the /api/courses endpoint."""

    def test_courses_endpoint_exists(self, client):
        """Test that the courses endpoint exists."""
        response = client.get("/api/courses")
        assert response.status_code == 200

    def test_courses_returns_total_count(self, client):
        """Test that courses response includes total count."""
        response = client.get("/api/courses")
        data = response.json()
        assert "total_courses" in data
        assert isinstance(data["total_courses"], int)
        assert data["total_courses"] >= 0

    def test_courses_returns_titles_list(self, client):
        """Test that courses response includes list of titles."""
        response = client.get("/api/courses")
        data = response.json()
        assert "course_titles" in data
        assert isinstance(data["course_titles"], list)

    def test_courses_titles_are_strings(self, client):
        """Test that all course titles are strings."""
        response = client.get("/api/courses")
        data = response.json()
        if data["course_titles"]:
            for title in data["course_titles"]:
                assert isinstance(title, str)
                assert len(title) > 0


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_serves_frontend(self, client):
        """Test that root endpoint serves the frontend."""
        response = client.get("/")
        assert response.status_code == 200
        # Should return HTML
        assert "text/html" in response.headers.get("content-type", "")

    def test_frontend_files_accessible(self, client):
        """Test that frontend static files are accessible."""
        # Test CSS file
        response = client.get("/style.css")
        assert response.status_code == 200

        # Test JS file
        response = client.get("/script.js")
        assert response.status_code == 200


class TestAPIValidation:
    """Tests for API input validation."""

    def test_query_rejects_invalid_json(self, client):
        """Test that invalid JSON is rejected."""
        response = client.post(
            "/api/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_query_validates_query_type(self, client):
        """Test that query must be a string."""
        response = client.post(
            "/api/query",
            json={"query": 123}  # Should be string
        )
        assert response.status_code == 422

    def test_query_validates_session_id_type(self, client):
        """Test that session_id must be a string if provided."""
        response = client.post(
            "/api/query",
            json={
                "query": "test",
                "session_id": 123  # Should be string
            }
        )
        assert response.status_code == 422


class TestCORS:
    """Tests for CORS configuration."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present."""
        response = client.options("/api/query")
        # CORS should allow the request
        assert response.status_code in [200, 204]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
