Weekend Events API — Render deployment notes

This project is deployed on Render. Use these recommended settings and commands.

- **Build Command**: pip install -r requirements.txt && python manage.py migrate
- **Start Command (web)**: gunicorn config.wsgi:application
- **Start Command (worker)**: celery -A config worker --loglevel=info --concurrency=2

Environment variables (minimum):

- **DJANGO_SETTINGS_MODULE**: config.settings
- **SECRET_KEY**: (set or generate)
- **DATABASE_URL**: provided by Render Postgres service
- **REDIS_URL**: provided by Render Redis service (if using Celery)
- **ALLOWED_HOSTS**: .onrender.com

Notes:

- This repo uses `requirements.txt`. Render may try to use Poetry if a `pyproject.toml` is present or if the service is configured to use Poetry. To avoid Poetry errors, ensure the Build Command is the `pip install` line above and remove any `POETRY_VERSION` environment variable from your Render service settings.
- Python version: Render uses Python 3.14 by default for this instance. This project is pinned to Django 5.0.6, which is not compatible with Python 3.14 in the admin templating layer. Set `pythonVersion: 3.12.0` in `render.yaml` (and avoid any `POETRY_VERSION` env var) to keep Render running this app with the existing Django version.

Local development:

Install dependencies and run locally using a virtualenv:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Optional: run the startup script locally on Linux/Render environments:

```bash
bash startup.sh
```

On Windows, `gunicorn` may fail because it depends on Unix-only modules like `fcntl`. Use Django's built-in development server instead:

```bash
python manage.py runserver
```
