from dotenv import load_dotenv

from learn_flask import create_app


def main():
    # The flask CLI loads .env by itself, but app.run() does not. Without this
    # the app silently falls back to sqlite every time.
    load_dotenv()

    app = create_app()
    app.run(host="0.0.0.0", port=3000, debug=True)
