# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --no-editable

ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# Final image
FROM python:3.12-slim-bookworm

# Install git, Node.js (for pyright), and cleanup
RUN apt-get update && \
    apt-get install -y curl git ca-certificates gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g pyright && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed Python environment from build stage
COPY --from=uv /root/.local /root/.local
COPY --from=uv --chown=app:app /app/.venv /app/.venv

# Ensure our virtualenv Python tools are on the path
ENV PATH="/app/.venv/bin:/usr/local/bin:$PATH"

# Entry point for the LSP server
ENTRYPOINT ["lsp-mcp-server"]
