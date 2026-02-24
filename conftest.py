"""
Pytest configuration and shared fixtures.
"""
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def mock_cache():
    """In-memory cache implementing the client's expected interface."""
    storage = {}

    class MockCache:
        def get(self, key):
            return storage.get(key)

        def set(self, key, value):
            storage[key] = value

        def get_hero_list(self):
            return storage.get("__hero_list__")

        def set_hero_list(self, heroes):
            storage["__hero_list__"] = heroes

    return MockCache()


@pytest.fixture
def temp_cache_path(tmp_path):
    """Unique temp path for file cache tests (avoids touching real cache)."""
    return tmp_path / "test_cache.json"
