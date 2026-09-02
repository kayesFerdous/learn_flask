# Store API

A REST API for stores, items and tags, built with Flask while learning it.
Stores and items, tags you can attach to items, user signup with JWT login,
and a welcome email sent by a background worker.

Built with Flask, flask-smorest, SQLAlchemy, Postgres and rq.

## Running it

With Docker (Postgres, Redis, the API and the worker):

```bash
cp .env.example .env
docker compose up --build
```

Without Docker, just the API on SQLite:

```bash
cp .env.example .env
uv sync
uv run server
```

Both run on http://localhost:3000. Swagger docs are at `/docs`.

`uv run server` uses Flask's dev server, so it is for local work only. Docker
runs gunicorn.

## Endpoints

| | |
| --- | --- |
| `/health` | 200 if the database answers, 503 if it doesn't |
| `/stores`, `/stores/<id>` | GET, POST, PATCH, DELETE |
| `/stores/<id>/items`, `/items` | GET, POST, PATCH, DELETE, and QUERY for filtered search |
| `/tags`, `/stores/<id>/tags` | tags, plus link and unlink them to items |
| `/users`, `/users/login`, `/users/me` | signup, login, refresh, logout |

Anything that changes a user needs a JWT in the `Authorization` header.

## How the code is arranged

```
resources/  ->  services/  ->  models/
   HTTP          rules         tables
```

Routes live in `resources/` and only read the request and call one service
method. The rules live in `services/`, and those files don't import Flask.

The rest:

- `config.py` — all the settings in one class
- `errors.py` — the exception classes services raise, and the handler for them
- `notifications.py` — sending email
- `extensions.py` — `db`, `migrate`, `jwt`
- `schemas/` — marshmallow, for validating input and shaping output

`REFACTOR.md` explains why it is split this way.

## Settings

Everything goes in `.env`. `.env.example` lists all of it with comments.
The ones you need: `DATABASE_URL`, `JWT_SECRET_KEY`, and `BREVO_API_KEY` if
you want real emails instead of printed ones.

## Migrations

```bash
uv run flask db migrate -m "what changed"
uv run flask db upgrade
```
