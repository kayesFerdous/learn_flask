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
- Docker: `docker build -t learn-flask .` then `docker run --rm -p 3000:3000 learn-flask`.
  The container runs **gunicorn**, not `app.run()` — `uv run server` stays for local dev only.

## The API so far

An in-memory product list in `main.py` (a plain Python list — it resets every
restart). Routes:

- `GET /products` — filter by any field via query string, e.g. `?category=Audio`
- `GET /products/<id>` — one product
- `POST /products` — create; server assigns the id, returns `201`
- `PATCH /products/<id>` — partial update
- `DELETE /products/<id>` — remove

Known gaps, not yet done: `GET`/`DELETE` return `200` on a missing id instead of
`404`, errors return plain text instead of JSON, and neither `POST` nor `PATCH`
validates input (a missing or non-numeric field is a `500`).
