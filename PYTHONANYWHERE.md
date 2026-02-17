# Deploy Super Heroes on PythonAnywhere (free, no card)

Follow these steps in order. Replace **caeserlondon** with your PythonAnywhere username if different.

---

## Step 1: Create account and get a project on the server

1. Go to **[pythonanywhere.com](https://www.pythonanywhere.com)** and **Register** (free account).
2. Log in. You’ll see the **Dashboard**.
3. Open the **Consoles** tab and click **$ Bash** to open a Linux console. You’ll use this for the next steps.

---

## Step 2: Upload your project

**Option A – Upload a zip (easiest if you don’t use GitHub)**

1. On your own computer, zip the project **without** `.venv` and without `.env`:
   - Mac/Linux: in the project folder run  
     `zip -r super-heros.zip . -x ".venv/*" -x ".env" -x ".git/*" -x "*.pyc" -x "__pycache__/*"`
   - Or create a zip by hand excluding `.venv`, `.env`, and `.git`.
2. In PythonAnywhere: **Files** tab → go to `/home/caeserlondon/` → **Upload a file** → choose `super-heros.zip`.
3. In the **Bash** console run:
   ```bash
   cd ~
   unzip -o super-heros.zip -d super-heros
   cd super-heros
   ls
   ```
   You should see `manage.py`, `config`, `heroes`, `superhero_api`, etc.

**Option B – Clone from GitHub**

1. In the **Bash** console:
   ```bash
   cd ~
   git clone https://github.com/YOUR_USERNAME/super-heros.git
   cd super-heros
   ```
   (Use your real GitHub repo URL. If the repo is private, use a personal access token in the URL.)

---

## Step 3: Create virtualenv and install dependencies

In the **same Bash console** (you should be in `~/super-heros` or `~/super-heros`):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Wait until everything installs. Then check:

```bash
python -c "import django; print(django.get_version())"
python -c "import requests; print('requests OK')"
```

---

## Step 4: Set environment variables (API token, etc.)

Still in Bash, create a `.env` file so the app can find your token and settings:

```bash
cd ~/super-heros
nano .env
```

Add these lines (change the values as needed):

```text
ALLOWED_HOSTS=caeserlondon.pythonanywhere.com
DEBUG=0
DJANGO_SECRET_KEY=put-a-long-random-string-here
SUPERHERO_API_TOKEN=your-superhero-api-token
```

Save and exit: **Ctrl+O**, Enter, then **Ctrl+X**.

(If you don’t set `SUPERHERO_API_TOKEN`, the app still runs using fallback data.)

---

## Step 5: Create the web app and set the document root

1. Open the **Web** tab.
2. Click **Add a new web app** → **Next** → choose **Manual configuration** (not Django) → **Next** → pick **Python 3.10** (or the highest 3.x offered) → **Finish**.
3. In **Code**:
   - **Source code:** `/home/caeserlondon/super-heros`  
     (or `/home/caeserlondon/super-heros` if you cloned into `super-heros` – use the path where `manage.py` lives).
   - **Working directory:** leave empty or set to `/home/caeserlondon/super-heros` (same as source).

---

## Step 6: Point the app to your virtualenv

Still on the **Web** tab, in **Virtualenv**:

1. Click the red text **Enter path to a virtualenv, if desired**.
2. Type: `/home/caeserlondon/super-heros/.venv`
3. Click the green check. The virtualenv should show as set.

---

## Step 7: Edit the WSGI configuration file

1. On the **Web** tab, find **WSGI configuration file** and click the link (e.g. `/var/www/caeserlondon_pythonanywhere_com_wsgi.py`).
2. **Delete all the default content** and paste this, then **change the two paths** if yours are different (e.g. folder name `super-heros` vs `super-heros`):

```python
import os
import sys

# Your project folder (where manage.py is)
path = '/home/caeserlondon/super-heros'
if path not in sys.path:
    sys.path.insert(0, path)

# So Django can load .env from project root
os.chdir(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
os.environ['ALLOWED_HOSTS'] = 'caeserlondon.pythonanywhere.com'
# Optional: set token here if you didn't create .env
# os.environ['SUPERHERO_API_TOKEN'] = 'your-token'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

3. **Save** (Ctrl+S).

Important: the `path` must be the **exact** directory that contains `manage.py` (e.g. `/home/caeserlondon/super-heros`). If you used a different folder name, fix both `path` and **Source code** in Step 5.

---

## Step 8: Static files (if you add any later)

This project uses inline CSS, so you may not need this now. If you add static files later:

- **Static files** (Web tab):  
  URL: `/static/`  
  Directory: `/home/caeserlondon/super-heros/static` (create that folder if needed, then run `python manage.py collectstatic --noinput` if you use collectstatic).

For the current app you can skip this.

---

## Step 9: Reload the web app

On the **Web** tab, click the green **Reload** button.

Then open: **https://caeserlondon.pythonanywhere.com**

The first load might take a few seconds while hero data is fetched and cached.

---

## If you see an error

- **500 or “something went wrong”**  
  - **Web** tab → **Error log** (and **Server log**). The error log usually shows the Python traceback (e.g. wrong path, missing module, bad env var).
  - Double-check: path in WSGI file = folder that contains `manage.py`; virtualenv = `.../super-heros/.venv`; `ALLOWED_HOSTS` = `caeserlondon.pythonanywhere.com`.

- **“DisallowedHost”**  
  - In the WSGI file, set `os.environ['ALLOWED_HOSTS'] = 'caeserlondon.pythonanywhere.com'` and reload.

- **“No module named 'requests'” or “No module named 'django'”**  
  - Virtualenv is wrong or not set. Set virtualenv to `/home/caeserlondon/super-heros/.venv` and reload.

- **Path / import errors**  
  - In WSGI, `path` must be the directory that contains the `config` folder (the same as **Source code** on the Web tab).

---

## Quick checklist

- [ ] Project is in `/home/caeserlondon/super-heros` (or your path).
- [ ] Virtualenv created and packages installed (`pip install -r requirements.txt`).
- [ ] `.env` created with `ALLOWED_HOSTS`, `DEBUG=0`, optional `SUPERHERO_API_TOKEN`.
- [ ] Web app: Manual configuration, Source code = project folder.
- [ ] Virtualenv on Web tab = `.../super-heros/.venv`.
- [ ] WSGI file: correct `path`, `os.environ['DJANGO_SETTINGS_MODULE']`, `os.environ['ALLOWED_HOSTS']`, then `get_wsgi_application()`.
- [ ] Reload pressed; then open https://caeserlondon.pythonanywhere.com

Your live link to share: **https://caeserlondon.pythonanywhere.com**
