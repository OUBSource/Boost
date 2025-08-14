FROM python:3.12 AS builder

WORKDIR /app
RUN python3 -m venv .venv
COPY requirements.txt .
RUN ./.venv/bin/pip3 install -r requirements.txt

FROM python:3.12-slim

RUN useradd -ms /bin/bash app && \
    mkdir -p /app && \
    mkdir -p /app/instance && \
    chown -R app /app
USER app
WORKDIR /app
COPY --chown=app . .
COPY --from=builder --chown=app /app/.venv .venv

EXPOSE 8200
ENTRYPOINT ["./.venv/bin/python3", "main.py"]