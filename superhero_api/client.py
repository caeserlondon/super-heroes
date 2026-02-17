"""
Client for https://superheroapi.com/

Fetches character data and appearance, with a cache layer to minimise
repetitive API calls. If SUPERHERO_API_TOKEN is not set, falls back to
the same dataset from akabab/superhero-api (used for images) so the app
can run without a token.
"""

import os
import re
from typing import Any

import requests

from superhero_api.cache import get_cache

# Base URL for superheroapi.com (token is inserted after /api/)
SUPERHERO_API_BASE = "https://superheroapi.com/api"
# Fallback: same dataset as official API, no token (akabab/superhero-api)
AKABAB_ALL_JSON = "https://cdn.jsdelivr.net/gh/akabab/superhero-api@0.3.0/api/all.json"
# Alternative image base (Cloudflare blocks API images on other domains)
IMAGE_BASE = "https://cdn.jsdelivr.net/gh/akabab/superhero-api@0.3.0/api/images/md"


def _slug(name: str) -> str:
    """Convert hero name to image slug: lowercase, spaces to hyphens."""
    s = (name or "").lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s).strip("-")
    return s or "unknown"


def hero_image_url(hero_id: str | int, name: str) -> str:
    """
    Build image URL using the alternative source (akabab backup).
    Format: [hero_id]-[hero-name].jpg
    """
    slug = _slug(name)
    return f"{IMAGE_BASE}/{hero_id}-{slug}.jpg"


class SuperheroAPIClient:
    """
    Fetches superhero data from superheroapi.com with caching.

    Requires SUPERHERO_API_TOKEN in the environment (get one via
    https://superheroapi.com/ with GitHub login).
    """

    def __init__(self, token: str | None = None, cache=None):
        self.token = token or os.environ.get("SUPERHERO_API_TOKEN", "").strip()
        self.cache = cache or get_cache()
        self._session = requests.Session()
        self._session.headers["Accept"] = "application/json"

    def _url(self, path: str) -> str:
        if not self.token:
            raise ValueError(
                "SUPERHERO_API_TOKEN is not set. "
                "Get a token at https://superheroapi.com/ (GitHub login)."
            )
        path = path.lstrip("/")
        return f"{SUPERHERO_API_BASE}/{self.token}/{path}"

    def _get(self, path: str) -> dict[str, Any] | None:
        if not self.token:
            return None
        url = self._url(path)
        try:
            r = self._session.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            if data.get("response") == "error":
                return None
            return data
        except (requests.RequestException, ValueError):
            return None

    def _fetch_all_fallback(self) -> list[dict[str, Any]]:
        """Fetch full list from akabab when no API token (same data source)."""
        cached = self.cache.get_hero_list()
        if cached is not None:
            return cached
        try:
            r = self._session.get(AKABAB_ALL_JSON, timeout=15)
            r.raise_for_status()
            raw = r.json()
        except (requests.RequestException, ValueError):
            return []
        # Normalise to same shape as superheroapi.com (id, name, appearance)
        heroes = []
        for item in raw:
            app = item.get("appearance") or {}
            # akabab uses eyeColor/hairColor; API uses eye-color/hair-color
            norm = {
                "gender": app.get("gender"),
                "race": app.get("race"),
                "height": app.get("height") or [],
                "weight": app.get("weight") or [],
                "eye-color": app.get("eyeColor") or app.get("eye-color"),
                "hair-color": app.get("hairColor") or app.get("hair-color"),
            }
            hero = {
                "id": str(item.get("id", "")),
                "name": item.get("name", "Unknown"),
                "appearance": norm,
            }
            heroes.append(hero)
            # Cache each character for get_character/get_appearance
            self.cache.set(f"char_{item.get('id')}", item)
        if heroes:
            self.cache.set_hero_list(heroes)
        return heroes

    def get_character(self, character_id: int | str) -> dict[str, Any] | None:
        """
        Fetch full character data by ID. Uses cache; only calls API on miss.
        If no token, ensures fallback list is loaded so cache may have the hero.
        """
        key = f"char_{character_id}"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        if self.token:
            data = self._get(str(character_id))
            if data is not None:
                self.cache.set(key, data)
            return data
        # No token: ensure we have fallback data, then re-check cache
        self._fetch_all_fallback()
        return self.cache.get(key)

    def get_appearance(self, character_id: int | str) -> dict[str, Any] | None:
        """
        Fetch appearance data for a character. Uses full character when
        available and extracts appearance to avoid extra request.
        """
        full = self.get_character(character_id)
        if full:
            app = full.get("appearance") or {}
            # Normalise keys (akabab: eyeColor/hairColor, API: eye-color/hair-color)
            return {
                "response": "success",
                "id": full.get("id"),
                "name": full.get("name"),
                "gender": app.get("gender"),
                "race": app.get("race"),
                "height": app.get("height") or [],
                "weight": app.get("weight") or [],
                "eye-color": app.get("eyeColor") or app.get("eye-color"),
                "hair-color": app.get("hairColor") or app.get("hair-color"),
            }
        key = f"appearance_{character_id}"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        if self.token:
            data = self._get(f"{character_id}/appearance")
            if data is not None:
                self.cache.set(key, data)
            return data
        return None

    def get_biography(self, character_id: int | str) -> dict[str, Any] | None:
        """
        Fetch biography data for a character. Uses full character when
        available and extracts biography to avoid extra request.
        """
        full = self.get_character(character_id)
        if full:
            bio = full.get("biography") or {}
            return {
                "response": "success",
                "id": full.get("id"),
                "name": full.get("name"),
                "full-name": bio.get("full-name") or bio.get("fullName"),
                "alter-egos": bio.get("alter-egos") or bio.get("alterEgos"),
                "aliases": bio.get("aliases") or [],
                "place-of-birth": bio.get("place-of-birth") or bio.get("placeOfBirth"),
                "first-appearance": bio.get("first-appearance") or bio.get("firstAppearance"),
                "publisher": bio.get("publisher"),
                "alignment": bio.get("alignment"),
            }
        key = f"biography_{character_id}"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        if self.token:
            data = self._get(f"{character_id}/biography")
            if data is not None:
                self.cache.set(key, data)
            return data
        return None

    def get_powerstats(self, character_id: int | str) -> dict[str, Any] | None:
        """
        Fetch powerstats data for a character. Uses full character when
        available and extracts powerstats to avoid extra request.
        Returns stats: intelligence, strength, speed, durability, power, combat.
        """
        full = self.get_character(character_id)
        if full:
            stats = full.get("powerstats") or {}
            return {
                "response": "success",
                "id": full.get("id"),
                "name": full.get("name"),
                "intelligence": stats.get("intelligence") or stats.get("Intelligence"),
                "strength": stats.get("strength") or stats.get("Strength"),
                "speed": stats.get("speed") or stats.get("Speed"),
                "durability": stats.get("durability") or stats.get("Durability"),
                "power": stats.get("power") or stats.get("Power"),
                "combat": stats.get("combat") or stats.get("Combat"),
            }
        key = f"powerstats_{character_id}"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        if self.token:
            data = self._get(f"{character_id}/powerstats")
            if data is not None:
                self.cache.set(key, data)
            return data
        return None

    def get_hero_list(self, id_range: range | None = None) -> list[dict[str, Any]]:
        """
        Return a list of heroes with at least id, name, and appearance.
        Uses cache; on miss, uses API (with token) or fallback dataset (no token).
        id_range: used only when using official API (default 1..100).
        """
        cached_list = self.cache.get_hero_list()
        if cached_list is not None:
            return cached_list
        if not self.token:
            return self._fetch_all_fallback()
        if id_range is None:
            id_range = range(1, 101)
        heroes = []
        for i in id_range:
            char = self.get_character(i)
            if not char:
                continue
            hero = {
                "id": char.get("id"),
                "name": char.get("name", "Unknown"),
                "appearance": char.get("appearance") or {},
            }
            heroes.append(hero)
        if heroes:
            self.cache.set_hero_list(heroes)
        return heroes


def get_client(token: str | None = None) -> SuperheroAPIClient:
    """Return a SuperheroAPIClient using optional token or SUPERHERO_API_TOKEN."""
    return SuperheroAPIClient(token=token)
