"""
Integration tests: full stack (view → real client → real Django cache).
Only external HTTP is mocked (CDN fallback); no mocking of views, client, or cache.
Uses RequestFactory + view directly to avoid Django test client template instrumentation
on Python 3.14; still exercises the full request path through real views and cache.
"""
import requests_mock

from django.core.cache import cache
from django.test import Client, RequestFactory

from heroes.views import hero_list, hero_detail


# CDN URL used when no SUPERHERO_API_TOKEN (fallback list)
AKABAB_ALL_JSON = "https://cdn.jsdelivr.net/gh/akabab/superhero-api@0.3.0/api/all.json"


def _sample_heroes():
    """Minimal hero list as returned by the CDN (akabab format)."""
    return [
        {
            "id": 70,
            "name": "Batman",
            "appearance": {
                "gender": "Male",
                "race": "Human",
                "eyeColor": "blue",
                "hairColor": "black",
                "height": ["6'2\"", "188 cm"],
                "weight": ["210 lb", "95 kg"],
            },
            "biography": {"full-name": "Bruce Wayne", "publisher": "DC Comics"},
            "powerstats": {"intelligence": "100", "strength": "26", "speed": "27", "durability": "50", "power": "47", "combat": "100"},
        },
        {
            "id": 1,
            "name": "A-Bomb",
            "appearance": {"gender": "Male", "race": "Human", "eyeColor": "Yellow", "hairColor": "No Hair"},
            "biography": {},
            "powerstats": {},
        },
    ]


class TestIntegrationListAndDetail:
    """Full-stack tests: real views, real client, real Django cache; only CDN mocked."""

    def setup_method(self):
        try:
            cache.clear()
        except AttributeError:
            pass

    def test_list_page_returns_200_and_heroes_from_mocked_cdn(self, monkeypatch):
        """hero_list uses real client → real cache; CDN is mocked."""
        monkeypatch.setenv("SUPERHERO_API_TOKEN", "")
        factory = RequestFactory()
        with requests_mock.Mocker() as m:
            m.get(AKABAB_ALL_JSON, json=_sample_heroes())
            request = factory.get("/")
            response = hero_list(request)
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Batman" in content
        assert "A-Bomb" in content

    def test_detail_page_returns_200_after_list_loads(self, monkeypatch):
        """Load list from mocked CDN, then hero_detail(70) uses cached hero (full stack)."""
        monkeypatch.setenv("SUPERHERO_API_TOKEN", "")
        factory = RequestFactory()
        with requests_mock.Mocker() as m:
            m.get(AKABAB_ALL_JSON, json=_sample_heroes())
            list_resp = hero_list(factory.get("/"))
            assert list_resp.status_code == 200
            detail_resp = hero_detail(factory.get("/70/"), "70")
        assert detail_resp.status_code == 200
        content = detail_resp.content.decode("utf-8")
        assert "Batman" in content
        assert "Bruce Wayne" in content

    def test_detail_page_returns_404_for_unknown_hero(self, monkeypatch):
        """List has no hero 99999; hero_detail(99999) returns 404."""
        monkeypatch.setenv("SUPERHERO_API_TOKEN", "")
        factory = RequestFactory()
        with requests_mock.Mocker() as m:
            m.get(AKABAB_ALL_JSON, json=_sample_heroes())
            hero_list(factory.get("/"))
            response = hero_detail(factory.get("/99999/"), "99999")
        assert response.status_code == 404

    def test_health_endpoint_returns_200_ok(self):
        """GET /health/ via test client (no template rendering)."""
        response = Client().get("/health/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_list_served_from_cache_on_second_request(self, monkeypatch):
        """Second hero_list() does not hit CDN again (cache)."""
        monkeypatch.setenv("SUPERHERO_API_TOKEN", "")
        factory = RequestFactory()
        with requests_mock.Mocker() as m:
            m.get(AKABAB_ALL_JSON, json=_sample_heroes())
            hero_list(factory.get("/"))
            hero_list(factory.get("/"))
        assert m.call_count == 1
