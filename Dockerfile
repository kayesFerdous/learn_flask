# Base image: already contains Python 3.14 AND uv.
FROM ghcr.io/astral-sh/uv:0.12.5-python3.14-trixie-slim

WORKDIR /app

# Dependencies first, on their own layer. Docker caches this step and only
# re-runs it when pyproject.toml or uv.lock actually change — so editing
# main.py doesn't reinstall Flask.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Then your code, which changes on nearly every build.
COPY README.md ./
COPY src/ ./src/
COPY migrations/ ./migrations/
RUN uv sync --frozen --no-dev

# Put the venv's bin/ on PATH so `gunicorn` is found without `uv run`.
ENV PATH="/app/.venv/bin:$PATH"

# Documentation only — it does not publish the port. You still need -p.
EXPOSE 3000

# `flask db upgrade` needs to know which app to load.
ENV FLASK_APP=learn_flask

# Picks ProdConfig in config.py, which refuses to start if DATABASE_URL or
# JWT_SECRET_KEY are missing. Better a crash here than a live app signing
# tokens with the dev secret that is committed to git.
ENV APP_ENV=production

# Apply any pending migrations, THEN serve. Gunicorn, not app.run() —
# that one is Flask's development server.
CMD ["sh", "-c", "flask db upgrade && gunicorn --bind 0.0.0.0:3000 'learn_flask:create_app()'"]
