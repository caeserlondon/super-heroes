"""
Cache layer for Superhero API responses.

Uses a persistent JSON file so cached data survives process restarts
and reduces repetitive requests to the API.
"""

import json
import threading
from pathlib import Path

# Default cache file in project root (or user's home if not writable)
_CACHE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CACHE_PATH = _CACHE_DIR / ".superhero_cache.json"

_lock = threading.Lock()
_memory: dict = {}
_loaded = False


def _ensure_loaded(cache_path: Path) -> None:
    """Load cache from disk if not already in memory."""
    global _memory, _loaded
    with _lock:
        if _loaded:
            return
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    _memory = json.load(f)
            except (json.JSONDecodeError, OSError):
                _memory = {}
        else:
            _memory = {}
        _loaded = True


def _save(cache_path: Path) -> None:
    """Persist in-memory cache to disk."""
    with _lock:
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(_memory, f, indent=0, ensure_ascii=False)
        except OSError:
            pass


def get_cache(cache_path: Path | None = None):
    """
    Return a cache instance. Uses DEFAULT_CACHE_PATH if cache_path is None.
    """
    path = cache_path or DEFAULT_CACHE_PATH
    return _JsonFileCache(path)


class _JsonFileCache:
    """Simple key-value cache backed by a JSON file."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def get(self, key: str):
        """Return value for key or None if missing."""
        _ensure_loaded(self.path)
        with _lock:
            return _memory.get(key)

    def set(self, key: str, value) -> None:
        """Store value for key and persist to disk."""
        _ensure_loaded(self.path)
        with _lock:
            _memory[key] = value
        _save(self.path)

    def get_hero_list(self):
        """Return cached list of hero summaries (id, name, appearance) or None."""
        return self.get("__hero_list__")

    def set_hero_list(self, heroes: list) -> None:
        """Store the full hero list in cache."""
        self.set("__hero_list__", heroes)

    def clear(self) -> None:
        """Clear all cached entries (for testing)."""
        global _memory, _loaded
        with _lock:
            _memory = {}
            _loaded = True
        if self.path.exists():
            try:
                self.path.unlink()
            except OSError:
                pass
