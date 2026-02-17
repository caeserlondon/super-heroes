"""
Django cache adapter for the Superhero API client.

Uses Django's built-in cache framework (django.core.cache) so cached
API responses are stored in the configured cache backend (LocMem, Redis, etc.)
instead of a JSON file.
"""
from django.conf import settings
from django.core.cache import cache


CACHE_PREFIX = getattr(settings, "SUPERHERO_CACHE_PREFIX", "superhero_api")
CACHE_TIMEOUT = getattr(settings, "SUPERHERO_CACHE_TIMEOUT", 60 * 60 * 24)  # 24h


def _key(name: str) -> str:
    return f"{CACHE_PREFIX}:{name}"


def get_superhero_cache():
    """
    Return a cache adapter that implements the interface expected by
    superhero_api.client.SuperheroAPIClient: get(key), set(key, value),
    get_hero_list(), set_hero_list(heroes).
    """
    return _DjangoCacheAdapter()


class _DjangoCacheAdapter:
    """Adapter that wraps django.core.cache for use with SuperheroAPIClient."""

    def get(self, key: str):
        return cache.get(_key(key))

    def set(self, key: str, value) -> None:
        cache.set(_key(key), value, timeout=CACHE_TIMEOUT)

    def get_hero_list(self):
        return cache.get(_key("__hero_list__"))

    def set_hero_list(self, heroes: list) -> None:
        cache.set(_key("__hero_list__"), heroes, timeout=CACHE_TIMEOUT)

    def clear(self) -> None:
        # Django's default cache doesn't support clear(); we'd need to track keys.
        # For LocMemCache we could use cache.clear() but it's backend-specific.
        try:
            cache.clear()
        except AttributeError:
            pass
