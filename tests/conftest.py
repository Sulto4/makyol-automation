"""
Pytest configuration and shared fixtures

Provides test client, authentication helpers, and common test utilities.
"""

import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings


@pytest.fixture(scope="session")
def test_api_key():
    """
    Provide a valid test API key.

    Returns:
        str: A valid API key for testing
    """
    return "test-api-key-12345"


@pytest.fixture(scope="session")
def invalid_api_key():
    """
    Provide an invalid API key for testing authentication failures.

    Returns:
        str: An invalid API key
    """
    return "invalid-key-xyz"


@pytest.fixture(scope="session")
def setup_test_environment(test_api_key):
    """
    Setup test environment with test API key.

    Temporarily modifies environment to use test API key.
    """
    # Store original API keys
    original_api_keys = settings.api_keys

    # Set test API keys
    settings.api_keys = test_api_key

    yield

    # Restore original API keys
    settings.api_keys = original_api_keys


@pytest.fixture(scope="function")
def client(setup_test_environment):
    """
    Create a TestClient instance for making API requests.

    Note: Function-scoped to ensure rate limits don't carry over between tests.

    Returns:
        TestClient: FastAPI test client
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(test_api_key):
    """
    Provide authentication headers with valid API key.

    Returns:
        dict: Headers dictionary with X-API-Key
    """
    return {"X-API-Key": test_api_key}


@pytest.fixture
def invalid_auth_headers(invalid_api_key):
    """
    Provide authentication headers with invalid API key.

    Returns:
        dict: Headers dictionary with invalid X-API-Key
    """
    return {"X-API-Key": invalid_api_key}


@pytest.fixture
def no_auth_headers():
    """
    Provide headers without authentication.

    Returns:
        dict: Empty headers dictionary
    """
    return {}
