# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is **噗浪表符庫** (Plurk Emoji House) — a Django web app for searching, adding, and tagging Plurk emojis. Single Django project, no monorepo.

### Tech stack

- **Python 3.12** (managed by uv via `.python-version`; verify the security patch version)
- **Django 5.2 LTS** with SQLite3 (dev) / PostgreSQL 17.9 (prod via `DATABASE_URL`)
- **uv** as the package manager (`pyproject.toml` + `uv.lock`)
- **pytest** + pytest-django for testing

### Key commands

On Windows, read the `.code-workspace` environment setting and set
`UV_PROJECT_ENVIRONMENT` to its external environment before any `uv sync` or
`uv run`. The upgrade worktree uses `C:\Users\pappl\venvs\plurkEmojiHouse_upgrade312`;
do not create or use a project-local `.venv`. See `docs/upgrade-2026.md`.

| Task | Command |
|------|---------|
| Install deps (with test extras) | `uv sync --extra test` |
| Run migrations | `uv run python manage.py migrate` |
| Run dev server | `uv run python manage.py runserver 0.0.0.0:8000` |
| Run tests | `uv run pytest` |
| Django system check | `uv run python manage.py check` |

### Caveats

- `.python-version` selects Python 3.12. Verify the actual patch with `python --version`; Heroku selects its latest supported 3.12 security patch on each build.
- The database is SQLite3 in dev — no external DB setup needed. The `db.sqlite3` file is auto-created on `migrate`.
- Integration tests (marked `@pytest.mark.integration`) require network access to Plurk APIs. They run by default; to skip them: `uv run pytest -m "not integration"`.
- The `templates/` directory contains `.py` files that are **Brython** (Python-in-browser) frontend code, not backend Python — do not treat them as server-side code.
- Firebase (Google login) config is embedded in `templates/base.html` — login features require external Firebase setup and won't work in a dev-only environment.
- After installing new dependencies, the dev server's file watcher will auto-reload; no restart needed.
- Production migrations must first pass against a restored PostgreSQL copy, including duplicate association cleanup and old-code rollback compatibility. Never run pytest against the production `DATABASE_URL`.
