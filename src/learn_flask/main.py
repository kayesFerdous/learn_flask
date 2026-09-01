"""Development entry point -- `uv run server`.

Production does NOT use this file. The Dockerfile runs gunicorn against
`learn_flask:create_app()` directly, so app.run() (Flask's development server,
single-threaded and not built for real traffic) never runs there.
"""

from dotenv import load_dotenv

from learn_flask import create_app


def main():
    # The `flask` CLI loads .env by itself, but app.run() does not. Without
    # this line `uv run server` would never see DATABASE_URL, JWT_SECRET_KEY
    # or REDIS_URL, and would silently fall back to sqlite every time.
    #
    # It has to run BEFORE create_app(), because that is the moment the config
    # object is built and the environment is read.
    load_dotenv()

    app = create_app()
    app.run(host="0.0.0.0", port=3000, debug=True)
