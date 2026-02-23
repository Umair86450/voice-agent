# syntax=docker/dockerfile:1

# Use the official UV Python base image with Python 3.13 on Debian Bookworm
ARG PYTHON_VERSION=3.13
FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim AS base

ENV PYTHONUNBUFFERED=1

ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/app" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

# Install build dependencies and Caddy web server
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    curl \
    gnupg \
  && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg \
  && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list \
  && apt-get update \
  && apt-get install -y caddy \
  && rm -rf /var/lib/apt/lists/*

# Create Caddy configuration BEFORE switching to appuser
RUN echo ':8081 {\n  root * /app\n  file_server\n}' > /etc/caddy/Caddyfile \
  && chown appuser:appuser /etc/caddy/Caddyfile

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src/ src/

RUN uv sync --locked

COPY . .

RUN chown -R appuser:appuser /app

USER appuser

RUN uv run src/agent.py download-files

# Expose ports: 8080 for agent logs, 8081 for frontend
EXPOSE 8080 8081

# Run both agent and Caddy web server
CMD ["sh", "-c", "uv run src/agent.py start & caddy run --config /etc/caddy/Caddyfile"]
