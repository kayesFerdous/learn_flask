# learn_flask

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
- Run the app: `uv run server`
- That command comes from `[project.scripts]` in `pyproject.toml`, which points at
  the `main()` function in `src/learn_flask/main.py`.
- After changing `[project.scripts]`, run `uv sync` — that section is only read at
  install time. Changes to `main.py` need no sync.
- Install a package: `uv add <package>` (this updates `pyproject.toml` for me).

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
