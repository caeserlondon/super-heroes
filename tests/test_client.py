"""
Tests for superhero_api.client: hero_image_url, _slug, SuperheroAPIClient.
"""
from typing import cast

import pytest
import requests
import requests_mock

from superhero_api.client import (
    SuperheroAPIClient,
    hero_image_url,
    get_client,
)
from superhero_api.client import _slug  # noqa: F401 - used in tests


class TestSlug:
    """Tests for _slug (module-private but we test via hero_image_url or import)."""

    def test_slug_lowercase_and_hyphens(self):
        from superhero_api.client import _slug
        assert _slug("Iron Man") == "iron-man"
        assert _slug("Spider-Man") == "spider-man"

    def test_slug_empty_returns_unknown(self):
        from superhero_api.client import _slug
        assert _slug("") == "unknown"
        # runtime accepts None via (name or "")
        assert _slug(cast(str, None)) == "unknown"

    def test_slug_strips_and_collapses(self):
        from superhero_api.client import _slug
        assert _slug("  Captain   America  ") == "captain-america"


class TestHeroImageUrl:
    """Tests for hero_image_url."""

    def test_hero_image_url_format(self):
        url = hero_image_url(70, "Batman")
        assert "70-batman.jpg" in url
        assert url.startswith("https://cdn.jsdelivr.net")

    def test_hero_image_url_complex_name(self):
        url = hero_image_url(1, "A-Bomb")
        assert "1-a-bomb.jpg" in url


class TestSuperheroAPIClient:
    """Tests for SuperheroAPIClient with mocked HTTP and cache."""

    def test_init_uses_provided_token_and_cache(self, mock_cache):
        client = SuperheroAPIClient(token="fake-token", cache=mock_cache)
        assert client.token == "fake-token"
        assert client.cache is mock_cache

    def test_url_builds_correctly_with_token(self, mock_cache):
        client = SuperheroAPIClient(token="abc123", cache=mock_cache)
        assert client._url("70") == "https://superheroapi.com/api/abc123/70"
        assert client._url(
            "/70/biography") == "https://superheroapi.com/api/abc123/70/biography"

    def test_url_raises_without_token(self, mock_cache, monkeypatch):
        monkeypatch.setenv("SUPERHERO_API_TOKEN", "")
        client = SuperheroAPIClient(token="", cache=mock_cache)
        with pytest.raises(ValueError, match="SUPERHERO_API_TOKEN"):
            client._url("70")

    def test_get_character_returns_cached(self, mock_cache):
        mock_cache.set(
            "char_70", {"id": "70", "name": "Batman", "appearance": {"gender": "Male"}})
        client = SuperheroAPIClient(token="x", cache=mock_cache)
        with requests_mock.Mocker() as m:
            result = client.get_character(70)
        assert result is not None
        assert result["name"] == "Batman"
        assert m.call_count == 0

    def test_get_character_fetches_and_caches_on_miss(self, mock_cache):
        client = SuperheroAPIClient(token="x", cache=mock_cache)
        with requests_mock.Mocker() as m:
            m.get(
                "https://superheroapi.com/api/x/70",
                json={"id": "70", "name": "Batman",
                      "appearance": {"gender": "Male"}},
            )
            result = client.get_character(70)
        assert result is not None
        assert result["name"] == "Batman"
        assert mock_cache.get("char_70") == result
        assert m.call_count == 1

    def test_get_character_returns_none_on_api_error(self, mock_cache):
        client = SuperheroAPIClient(token="x", cache=mock_cache)
        with requests_mock.Mocker() as m:
            m.get("https://superheroapi.com/api/x/99999", status_code=404)
            result = client.get_character(99999)
        assert result is None

    def test_get_appearance_from_full_character(self, mock_cache):
        full = {
            "id": "70",
            "name": "Batman",
            "appearance": {
                "gender": "Male",
                "race": "Human",
                "height": ["6'2\"", "188 cm"],
                "weight": ["210 lb", "95 kg"],
                "eye-color": "blue",
                "hair-color": "black",
            },
        }
        mock_cache.set("char_70", full)
        client = SuperheroAPIClient(token="x", cache=mock_cache)
        result = client.get_appearance(70)
        assert result is not None
        assert result["name"] == "Batman"
        assert result["gender"] == "Male"
        assert result["race"] == "Human"
        assert result["eye-color"] == "blue"

    def test_get_hero_list_returns_cached(self, mock_cache):
        heroes = [{"id": "1", "name": "A-Bomb", "appearance": {}}]
        mock_cache.set_hero_list(heroes)
        client = SuperheroAPIClient(token="x", cache=mock_cache)
        with requests_mock.Mocker() as m:
            result = client.get_hero_list()
        assert result == heroes
        assert m.call_count == 0

    def test_get_hero_list_fetches_fallback_when_no_cache(self, mock_cache):
        client = SuperheroAPIClient(token="", cache=mock_cache)
        fallback_json = [
            {
                "id": 1,
                "name": "A-Bomb",
                "appearance": {"gender": "Male", "race": "Human", "eyeColor": "Yellow", "hairColor": "No Hair"},
            },
        ]
        with requests_mock.Mocker() as m:
            m.get(
                "https://cdn.jsdelivr.net/gh/akabab/superhero-api@0.3.0/api/all.json",
                json=fallback_json,
            )
            result = client.get_hero_list()
        assert len(result) == 1
        assert result[0]["name"] == "A-Bomb"
        assert result[0]["appearance"]["eye-color"] == "Yellow"
        assert mock_cache.get_hero_list() == result

    def test_get_hero_list_fallback_returns_empty_on_network_error(self, mock_cache):
        client = SuperheroAPIClient(token="", cache=mock_cache)
        with requests_mock.Mocker() as m:
            m.get(
                "https://cdn.jsdelivr.net/gh/akabab/superhero-api@0.3.0/api/all.json",
                exc=requests.exceptions.ConnectionError(),
            )
            result = client.get_hero_list()
        assert result == []

    def test_get_biography_from_full_character(self, mock_cache):
        full = {
            "id": "70",
            "name": "Batman",
            "appearance": {},
            "biography": {
                "full-name": "Bruce Wayne",
                "place-of-birth": "Gotham City",
                "publisher": "DC Comics",
            },
        }
        mock_cache.set("char_70", full)
        client = SuperheroAPIClient(token="x", cache=mock_cache)
        result = client.get_biography(70)
        assert result is not None
        assert result["name"] == "Batman"
        assert result["full-name"] == "Bruce Wayne"
        assert result["place-of-birth"] == "Gotham City"

    def test_get_powerstats_from_full_character(self, mock_cache):
        full = {
            "id": "70",
            "name": "Batman",
            "appearance": {},
            "powerstats": {"intelligence": "100", "strength": "26", "combat": "100"},
        }
        mock_cache.set("char_70", full)
        client = SuperheroAPIClient(token="x", cache=mock_cache)
        result = client.get_powerstats(70)
        assert result is not None
        assert result["name"] == "Batman"
        assert result["intelligence"] == "100"
        assert result["combat"] == "100"

    def test_get_returns_none_when_no_token(self, mock_cache, monkeypatch):
        monkeypatch.setenv("SUPERHERO_API_TOKEN", "")
        client = SuperheroAPIClient(token="", cache=mock_cache)
        assert client._get("70") is None

    def test_get_returns_none_on_response_error(self, mock_cache):
        client = SuperheroAPIClient(token="x", cache=mock_cache)
        with requests_mock.Mocker() as m:
            m.get("https://superheroapi.com/api/x/70",
                  json={"response": "error"})
            assert client._get("70") is None

    def test_get_character_no_token_returns_cached_when_present(self, mock_cache, monkeypatch):
        monkeypatch.setenv("SUPERHERO_API_TOKEN", "")
        mock_cache.set(
            "char_70", {"id": "70", "name": "Batman", "appearance": {}})
        client = SuperheroAPIClient(token="", cache=mock_cache)
        result = client.get_character(70)
        assert result is not None
        assert result["name"] == "Batman"

    def test_get_character_no_token_fetches_fallback_then_returns_from_cache(self, mock_cache, monkeypatch):
        monkeypatch.setenv("SUPERHERO_API_TOKEN", "")
        # CDN returns one hero; get_character(70) should trigger fallback, then return that hero from cache
        fallback_json = [{
            "id": 70,
            "name": "Batman",
            "appearance": {"gender": "Male", "race": "Human", "eyeColor": "Blue", "hairColor": "Black"},
        }]
        client = SuperheroAPIClient(token="", cache=mock_cache)
        with requests_mock.Mocker() as m:
            m.get(
                "https://cdn.jsdelivr.net/gh/akabab/superhero-api@0.3.0/api/all.json",
                json=fallback_json,
            )
            result = client.get_character(70)
        assert result is not None
        assert result["name"] == "Batman"

    def test_get_appearance_from_full_character_via_api(self, mock_cache):
        """When get_character returns full data, get_appearance builds from it."""
        client = SuperheroAPIClient(token="x", cache=mock_cache)
        with requests_mock.Mocker() as m:
            m.get("https://superheroapi.com/api/x/70", json={
                "id": "70", "name": "Batman", "appearance": {
                    "gender": "Male", "race": "Human",
                    "eye-color": "blue", "hair-color": "black",
                    "height": [], "weight": [],
                },
            })
            result = client.get_appearance(70)
        assert result is not None
        assert result["name"] == "Batman"
        assert result["eye-color"] == "blue"

    def test_get_appearance_returns_cached_when_character_missing(self, mock_cache):
        """When get_character returns None but appearance_70 is cached, return cached."""
        mock_cache.set("appearance_70", {
                       "id": "70", "name": "Batman", "eye-color": "blue"})
        client = SuperheroAPIClient(token="x", cache=mock_cache)
        with requests_mock.Mocker() as m:
            m.get("https://superheroapi.com/api/x/70",
                  json={"response": "error"})
            result = client.get_appearance(70)
        assert result is not None
        assert result["name"] == "Batman"
        assert result["eye-color"] == "blue"

    def test_get_appearance_via_appearance_endpoint_when_character_missing(self, mock_cache):
        """When get_character returns None, get_appearance uses appearance endpoint."""
        client = SuperheroAPIClient(token="x", cache=mock_cache)
        with requests_mock.Mocker() as m:
            m.get("https://superheroapi.com/api/x/70",
                  json={"response": "error"})
            m.get("https://superheroapi.com/api/x/70/appearance", json={
                "response": "success", "id": "70", "name": "Batman",
                "gender": "Male", "race": "Human", "eye-color": "blue", "hair-color": "black",
                "height": [], "weight": [],
            })
            result = client.get_appearance(70)
        assert result is not None
        assert result["name"] == "Batman"
        assert result["eye-color"] == "blue"

    def test_get_biography_from_full_character_via_api(self, mock_cache):
        client = SuperheroAPIClient(token="x", cache=mock_cache)
        with requests_mock.Mocker() as m:
            m.get("https://superheroapi.com/api/x/70", json={
                "id": "70", "name": "Batman", "biography": {"full-name": "Bruce Wayne"},
            })
            result = client.get_biography(70)
        assert result is not None
        assert result["full-name"] == "Bruce Wayne"

    def test_get_biography_returns_cached_when_character_missing(self, mock_cache):
        """When get_character returns None but biography_70 is cached, return cached."""
        mock_cache.set("biography_70", {
                       "id": "70", "name": "Batman", "full-name": "Bruce Wayne"})
        client = SuperheroAPIClient(token="x", cache=mock_cache)
        with requests_mock.Mocker() as m:
            m.get("https://superheroapi.com/api/x/70",
                  json={"response": "error"})
            result = client.get_biography(70)
        assert result is not None
        assert result["full-name"] == "Bruce Wayne"

    def test_get_biography_via_biography_endpoint_when_character_missing(self, mock_cache):
        client = SuperheroAPIClient(token="x", cache=mock_cache)
        with requests_mock.Mocker() as m:
            m.get("https://superheroapi.com/api/x/70",
                  json={"response": "error"})
            m.get("https://superheroapi.com/api/x/70/biography", json={
                "response": "success", "id": "70", "name": "Batman", "full-name": "Bruce Wayne",
            })
            result = client.get_biography(70)
        assert result is not None
        assert result["full-name"] == "Bruce Wayne"

    def test_get_powerstats_from_full_character_via_api(self, mock_cache):
        client = SuperheroAPIClient(token="x", cache=mock_cache)
        with requests_mock.Mocker() as m:
            m.get("https://superheroapi.com/api/x/70", json={
                "id": "70", "name": "Batman",
                "powerstats": {"intelligence": "100", "strength": "26", "speed": "27",
                               "durability": "50", "power": "47", "combat": "100"},
            })
            result = client.get_powerstats(70)
        assert result is not None
        assert result["intelligence"] == "100"
        assert result["combat"] == "100"

    def test_get_powerstats_returns_cached_when_character_missing(self, mock_cache):
        """When get_character returns None but powerstats_70 is cached, return cached."""
        mock_cache.set("powerstats_70", {
                       "id": "70", "name": "Batman", "intelligence": "100", "combat": "100"})
        client = SuperheroAPIClient(token="x", cache=mock_cache)
        with requests_mock.Mocker() as m:
            m.get("https://superheroapi.com/api/x/70",
                  json={"response": "error"})
            result = client.get_powerstats(70)
        assert result is not None
        assert result["intelligence"] == "100"
        assert result["combat"] == "100"

    def test_get_powerstats_via_powerstats_endpoint_when_character_missing(self, mock_cache):
        client = SuperheroAPIClient(token="x", cache=mock_cache)
        with requests_mock.Mocker() as m:
            m.get("https://superheroapi.com/api/x/70",
                  json={"response": "error"})
            m.get("https://superheroapi.com/api/x/70/powerstats", json={
                "response": "success", "id": "70", "name": "Batman",
                "intelligence": "100", "strength": "26", "speed": "27",
                "durability": "50", "power": "47", "combat": "100",
            })
            result = client.get_powerstats(70)
        assert result is not None
        assert result["intelligence"] == "100"
        assert result["combat"] == "100"

    def test_get_returns_none_on_http_error_and_invalid_json(self, mock_cache):
        """Cover _get except (RequestException, ValueError) -> return None."""
        client = SuperheroAPIClient(token="x", cache=mock_cache)
        with requests_mock.Mocker() as m:
            m.get("https://superheroapi.com/api/x/70", status_code=500)
            assert client._get("70") is None
            m.get("https://superheroapi.com/api/x/71", text="not json")
            assert client._get("71") is None


class TestGetClient:
    """Tests for get_client factory."""

    def test_get_client_returns_client_with_token(self, mock_cache):
        client = get_client(token="t")
        assert isinstance(client, SuperheroAPIClient)
        assert client.token == "t"
