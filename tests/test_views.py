"""
Tests for heroes.views: hero_list, hero_detail, favicon.
"""
from unittest.mock import patch

import pytest
from django.test import Client, RequestFactory

from heroes.views import _safe_int, hero_list, hero_detail, favicon, health


class TestHealth:
    """Test health check view."""

    def test_health_returns_200_ok(self):
        response = Client().get("/health/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestSafeInt:
    """Test _safe_int helper."""

    def test_valid_int(self):
        assert _safe_int(42) == 42
        assert _safe_int("100") == 100

    def test_none_and_empty(self):
        assert _safe_int(None) is None
        assert _safe_int("") is None

    def test_invalid_returns_none(self):
        assert _safe_int("nope") is None
        assert _safe_int([]) is None


class TestHeroList:
    """Test hero_list view (call view directly to avoid template engine issues on Python 3.14)."""

    @patch("heroes.views.render")
    @patch("heroes.views.get_superhero_cache")
    def test_hero_list_uses_real_client_with_mocked_cache(self, mock_get_cache, mock_render):
        """Cover _client() by mocking get_superhero_cache instead of _client."""
        mock_cache = type("C", (), {"get_hero_list": lambda self: [{"id": "1", "name": "A-Bomb", "appearance": {}}]})()
        mock_get_cache.return_value = mock_cache
        from django.http import HttpResponse
        mock_render.return_value = HttpResponse()
        request = RequestFactory().get("/")
        response = hero_list(request)
        assert response.status_code == 200
        mock_get_cache.assert_called()
        ctx = mock_render.call_args[0][2]
        assert ctx["heroes"][0]["name"] == "A-Bomb"

    @patch("heroes.views.render")
    @patch("heroes.views._client")
    def test_hero_list_returns_200_and_context(self, mock_client, mock_render):
        mock_client.return_value.get_hero_list.return_value = [
            {"id": "1", "name": "A-Bomb", "appearance": {"race": "Human"}},
        ]
        from django.http import HttpResponse
        mock_render.return_value = HttpResponse()
        request = RequestFactory().get("/")
        response = hero_list(request)
        assert response.status_code == 200
        mock_render.assert_called_once()
        # render(request, template, context)
        ctx = mock_render.call_args[0][2]
        assert "heroes" in ctx
        assert "hero_count" in ctx
        heroes = ctx["heroes"]
        assert len(heroes) == 1
        assert heroes[0]["name"] == "A-Bomb"
        assert heroes[0]["race"] == "Human"
        assert ctx["hero_count"] == 1


class TestHeroDetail:
    """Test hero_detail view."""

    @patch("heroes.views.render")
    @patch("heroes.views._client")
    def test_hero_detail_200_when_found(self, mock_client, mock_render):
        mock_client.return_value.get_appearance.return_value = {
            "id": "70",
            "name": "Batman",
            "gender": "Male",
            "race": "Human",
            "eye-color": "blue",
            "hair-color": "black",
            "height": [],
            "weight": [],
        }
        mock_client.return_value.get_biography.return_value = {"full-name": "Bruce Wayne"}
        mock_client.return_value.get_powerstats.return_value = {
            "intelligence": "100",
            "strength": "26",
            "speed": "27",
            "durability": "50",
            "power": "47",
            "combat": "100",
        }
        from django.http import HttpResponse
        mock_render.return_value = HttpResponse()
        request = RequestFactory().get("/70/")
        response = hero_detail(request, "70")
        assert response.status_code == 200
        mock_render.assert_called_once()
        ctx = mock_render.call_args[0][2]
        hero = ctx["hero"]
        assert hero["name"] == "Batman"
        assert hero["eye_color"] == "blue"
        assert hero["intelligence"] == 100

    @patch("heroes.views._client")
    def test_hero_detail_404_when_not_found(self, mock_client):
        mock_client.return_value.get_appearance.return_value = None
        request = RequestFactory().get("/99999/")
        response = hero_detail(request, "99999")
        assert response.status_code == 404


class TestFavicon:
    """Test favicon view."""

    def test_favicon_returns_200_or_404(self):
        """Favicon is 200 when file exists, 404 when missing."""
        response = Client().get("/favicon.png")
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            assert response.get("Content-Type", "").startswith("image/")

    @patch("heroes.views.FAVICON_PATH")
    def test_favicon_200_when_file_exists(self, mock_path):
        """When favicon file exists, view returns 200 and image content."""
        from io import BytesIO
        mock_path.exists.return_value = True
        mock_path.open.return_value.__enter__ = lambda self: BytesIO(b"\x89PNG\r\n\x1a\n")
        mock_path.open.return_value.__exit__ = lambda self, *a: None
        from heroes.views import favicon
        from django.http import HttpRequest
        request = HttpRequest()
        response = favicon(request)
        assert response.status_code == 200
        assert response.get("Content-Type") == "image/png"

    @patch("heroes.views.FAVICON_PATH")
    def test_favicon_404_when_file_missing(self, mock_path):
        """When favicon file does not exist, view raises Http404."""
        mock_path.exists.return_value = False
        from heroes.views import favicon
        from django.http import HttpRequest
        from django.http import Http404
        request = HttpRequest()
        with pytest.raises(Http404):
            favicon(request)
