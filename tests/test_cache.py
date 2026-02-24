"""
Tests for superhero_api.cache: file-backed cache get/set/get_hero_list/set_hero_list.
"""
from pathlib import Path
from unittest.mock import patch

import pytest

from superhero_api import cache as cache_module
from superhero_api.cache import get_cache


class TestJsonFileCache:
    """Tests for _JsonFileCache via get_cache(temp_path)."""

    def test_get_missing_returns_none(self, temp_cache_path):
        cache = get_cache(temp_cache_path)
        cache.clear()
        assert cache.get("missing") is None

    def test_set_and_get(self, temp_cache_path):
        cache = get_cache(temp_cache_path)
        cache.clear()
        cache.set("k", {"a": 1})
        assert cache.get("k") == {"a": 1}

    def test_get_hero_list_returns_none_when_empty(self, temp_cache_path):
        cache = get_cache(temp_cache_path)
        cache.clear()
        assert cache.get_hero_list() is None

    def test_set_hero_list_and_get_hero_list(self, temp_cache_path):
        cache = get_cache(temp_cache_path)
        cache.clear()
        heroes = [{"id": "1", "name": "A-Bomb", "appearance": {}}]
        cache.set_hero_list(heroes)
        assert cache.get_hero_list() == heroes

    def test_persistence(self, temp_cache_path):
        cache = get_cache(temp_cache_path)
        cache.clear()
        cache.set("x", "y")
        cache2 = get_cache(temp_cache_path)
        assert cache2.get("x") == "y"

    def test_clear_removes_file(self, temp_cache_path):
        cache = get_cache(temp_cache_path)
        cache.clear()
        cache.set("k", "v")
        assert temp_cache_path.exists()
        cache.clear()
        assert not temp_cache_path.exists()

    def test_load_from_existing_file(self, temp_cache_path, monkeypatch):
        """Cover _ensure_loaded when cache_path.exists() and valid JSON."""
        temp_cache_path.write_text('{"k": "v"}', encoding="utf-8")
        monkeypatch.setattr(cache_module, "_loaded", False)
        monkeypatch.setattr(cache_module, "_memory", {})
        cache = get_cache(temp_cache_path)
        assert cache.get("k") == "v"

    def test_load_when_path_does_not_exist(self, temp_cache_path, monkeypatch):
        """Cover _ensure_loaded else branch (path does not exist) -> _memory = {}."""
        assert not temp_cache_path.exists()
        monkeypatch.setattr(cache_module, "_loaded", False)
        monkeypatch.setattr(cache_module, "_memory", {"old": "data"})
        cache = get_cache(temp_cache_path)
        assert cache.get("old") is None
        assert cache.get("any") is None

    def test_load_handles_invalid_json_and_os_error(self, temp_cache_path, monkeypatch):
        """Cover _ensure_loaded except (JSONDecodeError, OSError) -> _memory = {}."""
        temp_cache_path.write_text("not json {", encoding="utf-8")
        monkeypatch.setattr(cache_module, "_loaded", False)
        monkeypatch.setattr(cache_module, "_memory", {})
        cache = get_cache(temp_cache_path)
        assert cache.get("any") is None

    def test_save_handles_os_error(self, temp_cache_path, monkeypatch):
        """Cover _save except OSError (e.g. write fails)."""
        cache = get_cache(temp_cache_path)
        cache.clear()
        with patch("builtins.open", side_effect=OSError("write failed")):
            cache.set("k", "v")  # should not raise
        assert cache.get("k") == "v"

    def test_clear_handles_unlink_os_error(self, temp_cache_path, monkeypatch):
        """Cover clear() when path.unlink() raises OSError."""
        cache = get_cache(temp_cache_path)
        cache.clear()
        cache.set("k", "v")
        with patch.object(Path, "unlink", side_effect=OSError("unlink failed")):
            cache.clear()
        assert cache.get("k") is None
