# learn_flask

## What this file is

Context for coding agents. When I use an AI coding assistant on this repo, it reads
this file first, so it knows what the project is, how I like things explained, and
what's already been built — instead of me repeating it every session.

A learning project. I'm new to Flask, and to Python packaging/imports in general.

## How to explain things to me

- **Use simple English.** No jargon unless you define it first, in one plain sentence.
- **One concept at a time.** If an answer needs three new ideas, teach the one that
  unblocks me now and say the others can wait.
- **Keep it short.** A few sentences and a small code example beats a long essay.
  If I want more depth I'll ask.
- **Show me the actual thing.** Print the file, run the command, show the real error
  and the real output. Don't just describe what would happen.
- **Connect it to my code.** Explain using the files in this repo, not abstract
  `foo`/`bar` examples.
- If I sound confused or overwhelmed, stop adding information. Cut the scope down
  and re-explain the single thing I'm actually stuck on.

## Don't edit my code unless I ask

- **Explain first, then stop.** Show me the cause and show me the fix, but don't
  apply it. Wait until I say go.
- This includes "obvious" one-line fixes. I'm learning, and I learn by making the
  change myself.
- Investigating is always fine — read files, grep, run commands, run the app,
  reproduce the error. It's *writing to files* I want you to hold off on.
- If you think a change is urgent, say so in a sentence and still wait.

## Teaching me best practices

I want to learn good habits while I learn Flask, so:

- When there's a standard or idiomatic way to do something, mention it briefly and
  say **why** it's better — not just that it is.
- Always flag when something is **development-only vs safe for production**
  (for example, `app.run()` and `debug=True` are dev-only).
- **Don't push advanced structure before the code needs it.** Things like app
  factories (`create_app()`), blueprints, and config classes solve problems I
  haven't hit yet. Point out when I'm approaching the problem they solve, then
  teach the pattern.
- If I ask for something that isn't best practice, tell me in a sentence or two,
  then help me do what I asked. Don't refuse and don't repeat the warning.
- Prefer teaching me the fix over silently applying it. If you do make the change,
  explain what you changed and why.

## Project facts

- Managed with **uv**, `src/` layout, Python 3.14.
- Run the app in development: `uv run server`
- That command comes from `[project.scripts]` in `pyproject.toml`, which points at
  the `main()` function in `src/learn_flask/main.py`.
- After changing `[project.scripts]`, run `uv sync` — that section is only read at
  install time. Changes to `main.py` need no sync.
- Install a package: `uv add <package>` (this updates `pyproject.toml` for me).
- Docker: `docker compose up --build`. The container runs **gunicorn**, not
  `app.run()` — `uv run server` stays for local dev only.
- Postgres publishes on host port **5432**.
- The refactor described below lives on the `layered-architecture` branch, cut
  from `postgres-migrations-and-email`.

## Where this project came from, and what it is for

This project was built by following a Udemy course. The
`layered-architecture` branch is the part that is mine: a refactor I am
presenting at my internship. So the **point of that branch is the architecture,
not the feature count**. Adding another route is worth almost nothing here.
Making the existing code well-structured is worth everything.

Keeping it as a branch rather than a new repo is deliberate: `git diff main` is
the presentation. The before and the after sit side by side in one history.

The goal, in one line:

> Routes stay thin. Business rules live in services. Every design pattern in
> here is present because something real needed it.

The one-way rule, which is the whole idea:

```
resources/  ->  services/  ->  models/
   HTTP          rules        tables
```

A service never imports Flask. Only `resources/` knows what HTTP is. There is no
repository layer on purpose — see the plan table below.

## The plan, and where I am in it

One numbering, so there is no confusion. Steps 5 and 7 were skipped by choice,
not forgotten -- see the reasons below.

| # | Step | Status |
| - | ---- | ------ |
| 1 | Copy + rename from `learn_flask` | done |
| 2 | Config classes + app factory | done |
| 3 | Split into layers: `resources/` -> `services/` | done |
| 4 | Custom error types + one error handler | done |
| 5 | Repository layer | **skipped on purpose** |
| 6 | Email Strategy (`EmailSender` -> Brevo / Console / Null) | done |
| 7 | Orders feature (`quantity`, `POST /orders`) | **skipped** |
| 8 | Tests with pytest | **skipped** |
| 9 | `/health` + docker healthcheck | done |
| 10 | README, CI, pagination, rate limit | not started |

**Why no repository layer (5).** SQLAlchemy's `Session` already is a repository
plus a unit of work. Wrapping it in another layer for an app this size is the
classic over-engineered-Flask mistake. Services take a `session` in their
constructor, which keeps them injectable without the extra layer. Be ready to
say this out loud -- knowing when *not* to add a pattern is the point.

**Why no orders and no tests (7, 8).** My call, to keep the scope down. The
cost of skipping tests: `NullSender` and `RecordingSender` currently have no
caller, so they read as decorative. If there is time, six tests fix that.

## What is built so far

### The layers

```
resources/  ->  services/  ->  models/
   HTTP          rules         tables
```

Verified, not just claimed -- `grep` for a Flask import across the codebase
returns only `__init__.py`, `extensions.py` and `resources/`. Nothing in
`services/`, `notifications/` or `models/` has ever heard of Flask.

- `resources/` (renamed from `blueprints/`, the flask-smorest convention for
  `MethodView` classes) -- reads the request, calls one service method, returns.
  Every route is one or two lines now.
- `services/` -- all the rules. `UserService` takes a `session` and an
  `EmailSender` in its constructor; nothing is imported from a global.
- `services/__init__.py` -- `build_services()`, the composition root: the one
  place concrete objects get chosen and plugged together.

### Errors

- `errors.py` -- `StoreAPIError` and five subclasses, plus
  `register_error_handlers()`. Services `raise`, one handler translates to JSON.
  Shape matches flask-smorest's own errors, so clients see one format.
- Status codes shifted on purpose: duplicate name/store is now **409** (was 400)
  and broken domain rules are **422** (was 400).

### Email (the Strategy pattern)

- `notifications/base.py` -- `EmailSender` ABC with one method, and a frozen
  `Email` dataclass.
- `notifications/senders.py` -- `BrevoSender`, `ConsoleSender`, `NullSender`,
  `RecordingSender`.
- `notifications/queued.py` -- `QueuedSender`, a real GoF **Decorator**: it *is*
  an `EmailSender` and *has* an `EmailSender`, and adds "do this in a background
  worker". rq pickles the wrapped sender and the `Email` and runs `deliver()`
  in the worker process. Verified with a real pickle round-trip.
- `notifications/__init__.py` -- `build_email_sender()`, a Factory built from a
  lookup table, same shape as `get_config()`.

### Config and factory

- `config.py` -- `BaseConfig` / `DevConfig` / `TestConfig` / `ProdConfig`, chosen
  by `get_config()` from `APP_ENV`. Environment is read in `__init__`, never in
  a class body (class bodies run at import time, before `.env` loads).
  `ProdConfig` raises if `DATABASE_URL` or `JWT_SECRET_KEY` are missing.
- `extensions.py` -- `db`, `migrate`, `jwt` created once and shared. The
  **Singleton** pattern, free from Python's module system. No `__new__` tricks.
- `create_app()` is five wiring calls and nothing else.

### The API

`GET /health` reports 200 when the app can reach the database and 503 when it
cannot, and the `api` container's docker healthcheck calls it. Then stores,
items, tags, users. Marshmallow validation, JWT with a revoke list,
refresh-token rotation, fresh-token rules on dangerous actions, Alembic
migrations, and an rq worker for the welcome email. The item collections also
answer **QUERY** (RFC 10008) for filters too complex for a query string.
