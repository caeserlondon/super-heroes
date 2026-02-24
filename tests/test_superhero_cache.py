"""
Tests for heroes.superhero_cache: Django cache adapter.
"""
from unittest.mock import patch

from django.core.cache import cache

from heroes.superhero_cache import (
    CACHE_PREFIX,
    _key,
    get_superhero_cache,
)


class TestDjangoCacheAdapter:
    """Test the adapter with Django's default cache (LocMem in tests)."""

    def setup_method(self):
        try:
            cache.clear()
        except AttributeError:
            pass

    def test_key_prefix(self):
        assert _key("char_70") == f"{CACHE_PREFIX}:char_70"
        assert _key("__hero_list__") == f"{CACHE_PREFIX}:__hero_list__"

    def test_get_set(self):
        adapter = get_superhero_cache()
        assert adapter.get("foo") is None
        adapter.set("foo", {"x": 1})
        assert adapter.get("foo") == {"x": 1}

    def test_get_hero_list_set_hero_list(self):
        adapter = get_superhero_cache()
        assert adapter.get_hero_list() is None
        heroes = [{"id": "1", "name": "Test", "appearance": {}}]
        adapter.set_hero_list(heroes)
        assert adapter.get_hero_list() == heroes

    def test_clear_handles_attribute_error(self):
        """Cover clear() when cache backend has no clear() (except AttributeError)."""
        adapter = get_superhero_cache()
        with patch.object(cache, "clear", side_effect=AttributeError("no clear")):
            adapter.clear()  # does not raise
