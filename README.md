# Super Heroes – Defaqto Technical Challenge

A small Python project that integrates with the [Superhero API](https://superheroapi.com/), caches responses, and provides a Django UI to browse superheroes and their appearance details.

### [Live on https://caeserlondon.pythonanywhere.com/](https://caeserlondon.pythonanywhere.com)

## Features

- **API integration**: Fetches superhero data (name and appearance) from the Superhero API. If `SUPERHERO_API_TOKEN` is not set, the app falls back to the same dataset from [akabab/superhero-api](https://github.com/akabab/superhero-api) so it runs without a token.
- **Caching**: Django’s built-in cache framework (`django.core.cache`) stores API responses so repeated list/detail views do not hit the API unnecessarily. Default backend is in-memory; you can switch to Redis, Memcached, or database cache in `config/settings.py`.
- **Django UI**:
  - List view of superheroes with thumbnails.
  - Detail view per hero showing appearance: image, gender, race, height, weight, eye colour, hair colour.
- **Images**: Uses the alternative image source (`cdn.jsdelivr.net/gh/akabab/superhero-api@0.3.0/api/images/...`) because the API’s image URLs are protected by Cloudflare. Format: `[hero_id]-[hero-name].jpg` (lowercase, spaces as hyphens).

## Setup

1. **Clone and enter the project**

   ```bash
   cd super-heroes
   ```

2. **Create a virtual environment and install dependencies**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Superhero API token**  
   For the official API, get a token at [superheroapi.com](https://superheroapi.com/) (GitHub login). Then either:
   - Create a `.env` file in the project root (copy from `.env.example`) and set `SUPERHERO_API_TOKEN=your-token`, or
   - Run `export SUPERHERO_API_TOKEN=your-token` in your shell.  
     Without a token, the app uses the fallback dataset and still works.

## Run

```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser. The first load may take a few seconds while data is fetched and cached; later requests are served from the cache.

- **`superhero_api/`** – API client (and optional file cache for non-Django use):
  - `client.py`: `SuperheroAPIClient` (list, character, appearance, biography, powerstats) and `hero_image_url()`.
  - `cache.py`: Optional JSON file cache used only if no cache is passed to the client (e.g. in scripts).
- **`heroes/superhero_cache.py`** – Django cache adapter used by the app so the client uses `django.core.cache`.
- **`config/`** – Django settings and URLs.
- **`heroes/`** – Django app: views, URLs, templates for list and detail.
- **Cache**: Configured in `config/settings.py` under `CACHES`; by default in-memory. Hero list and per-character data are stored with a 24-hour timeout.

## Design notes

- **Cache**: The Django app uses Django’s cache (see `heroes/superhero_cache.py`). You can change the backend in `CACHES` (e.g. Redis or database) so cache survives restarts.
- **Fallback**: When no token is set, the client fetches `all.json` from the akabab CDN (same data source as the challenge’s image backup), normalises it to the same shape as the API, and caches it. This keeps the app runnable for demos without a token.
- **Images**: All image URLs are built with `hero_image_url(id, name)` using the CDN and slug format to avoid Cloudflare blocking.
