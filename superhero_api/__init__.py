"""
Superhero API client with caching.

Fetches hero data from https://superheroapi.com/ and caches responses
to minimise API calls.
"""

from superhero_api.client import SuperheroAPIClient, hero_image_url
from superhero_api.cache import get_cache

__all__ = ["SuperheroAPIClient", "get_cache", "hero_image_url"]
