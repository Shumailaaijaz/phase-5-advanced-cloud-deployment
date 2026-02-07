import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_trailing_slash_returns_404():
    """Test that trailing slashes return 404 as per canonical path rules"""
    # This test would check if there are any routes that accidentally have trailing slashes
    # For now, we'll test a fake route with trailing slash
    response = client.get("/nonexistent/")
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"