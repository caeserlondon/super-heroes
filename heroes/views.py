"""
Views for the Super Heroes UI.

All data is fetched via the superhero_api client, which uses the cache layer
so repeated requests do not hit the API unnecessarily.
"""
from django.shortcuts import render

from superhero_api import SuperheroAPIClient, hero_image_url

from heroes.superhero_cache import get_superhero_cache


def _safe_int(value):
    """Convert value to int, return None if invalid."""
    if value is None or value == "":
        return None
    try:
        return int(str(value))
    except (ValueError, TypeError):
        return None


def _client():
    """Shared client instance using Django's cache framework."""
    return SuperheroAPIClient(cache=get_superhero_cache())


def hero_list(request):
    """
    List all superheroes. Data is served from cache when available;
    only the first load (or cache miss) triggers API/fallback requests.
    """
    client = _client()
    heroes = client.get_hero_list()
    # Attach image URL for each hero (alternative source, not Cloudflare-blocked)
    for h in heroes:
        h["image_url"] = hero_image_url(h.get("id", ""), h.get("name", ""))
        h["race"] = (h.get("appearance") or {}).get("race")
    return render(
        request,
        "heroes/hero_list.html",
        {"heroes": heroes, "hero_count": len(heroes)},
    )


def hero_detail(request, hero_id):
    """
    Show a single hero's appearance and biography details. Uses cache; no extra API call
    if the hero was already loaded (e.g. from the list).
    """
    client = _client()
    appearance = client.get_appearance(hero_id)
    if not appearance:
        return render(request, "heroes/hero_not_found.html", {"hero_id": hero_id}, status=404)
    
    biography = client.get_biography(hero_id) or {}
    powerstats = client.get_powerstats(hero_id) or {}
    
    appearance["image_url"] = hero_image_url(
        appearance.get("id", ""), appearance.get("name", "")
    )
    # Normalise keys for template (Django can't do hero.eye-color)
    hero = {
        "id": appearance.get("id"),
        "name": appearance.get("name"),
        "image_url": appearance.get("image_url"),
        "gender": appearance.get("gender"),
        "race": appearance.get("race"),
        "height": appearance.get("height"),
        "weight": appearance.get("weight"),
        "eye_color": appearance.get("eye-color"),
        "hair_color": appearance.get("hair-color"),
        # Biography fields
        "full_name": biography.get("full-name"),
        "alter_egos": biography.get("alter-egos"),
        "aliases": biography.get("aliases") if isinstance(biography.get("aliases"), list) else [],
        "place_of_birth": biography.get("place-of-birth"),
        "first_appearance": biography.get("first-appearance"),
        "publisher": biography.get("publisher"),
        "alignment": biography.get("alignment"),
        # Powerstats fields (convert to int for percentage display)
        "intelligence": _safe_int(powerstats.get("intelligence")),
        "strength": _safe_int(powerstats.get("strength")),
        "speed": _safe_int(powerstats.get("speed")),
        "durability": _safe_int(powerstats.get("durability")),
        "power": _safe_int(powerstats.get("power")),
        "combat": _safe_int(powerstats.get("combat")),
    }
    return render(request, "heroes/hero_detail.html", {"hero": hero})
