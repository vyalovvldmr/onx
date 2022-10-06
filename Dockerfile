FROM python:3.10-slim as builder
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*
ENV POETRY_HOME=/opt/poetry \
    PYTHONUNBUFFERED=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN python -c 'from urllib.request import urlopen; print(urlopen("https://install.python-poetry.org").read().decode())' | python -
COPY . ./
RUN poetry install --no-interaction

FROM python:3.10-slim
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
    LOCALHOST="0.0.0.0" \
    PORT=8888
COPY --from=builder /app /app
EXPOSE 8888
