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
RUN uv sync --frozen --no-dev

# Put the venv's bin/ on PATH so `gunicorn` is found without `uv run`.
ENV PATH="/app/.venv/bin:$PATH"

# Documentation only — it does not publish the port. You still need -p.
EXPOSE 3000

# Gunicorn, not app.run() — that one is Flask's development server.
CMD ["gunicorn", "--bind", "0.0.0.0:3000", "learn_flask:create_app()"]
