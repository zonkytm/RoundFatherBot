FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY bot/ bot/
COPY web/ web/
COPY alembic/ alembic/
COPY alembic.ini .

CMD ["python", "-m", "bot.main"]
