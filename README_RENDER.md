Weekend Events API — Render deployment notes

This project is deployed on Render. Use these recommended settings and commands.

- **Build Command**: pip install -r requirements.txt
- **Start Command (web)**: bash startup.sh
- **Start Command (worker)**: celery -A config worker --loglevel=info --concurrency=2

Environment variables (minimum):
- **DJANGO_SETTINGS_MODULE**: config.settings
- **SECRET_KEY**: (set or generate)
- **DATABASE_URL**: provided by Render Postgres service
- **REDIS_URL**: provided by Render Redis service (if using Celery)
- **ALLOWED_HOSTS**: .onrender.com

Notes:
- This repo uses `requirements.txt`. Render may try to use Poetry if a `pyproject.toml` is present or if the service is configured to use Poetry. To avoid Poetry errors, ensure the Build Command is the `pip install` line above.
- Python version: Render uses Python 3.14 by default for this instance. The project now depends on `psycopg[binary]==3.2.1` (psycopg v3) which supports Python 3.14.

Local development:

Install dependencies and run locally using a virtualenv:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Optional: run the startup script locally (Linux/macOS):

```bash
bash startup.sh
```
