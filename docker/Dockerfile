# Stage 1: Build React frontend
FROM node:20-slim AS frontend-build

WORKDIR /app/web/frontend
COPY web/frontend/package.json web/frontend/package-lock.json* ./
RUN npm ci
COPY web/frontend/ ./
RUN npm run build

# Stage 2: Python backend
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

# Copy built frontend
COPY --from=frontend-build /app/web/static/dist/ web/static/dist/

CMD ["python", "-m", "bot.main"]
