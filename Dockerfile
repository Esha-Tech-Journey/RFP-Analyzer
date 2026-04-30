# ──────────────────────────────────────────────
# Stage 1: frontend
# ──────────────────────────────────────────────
FROM node:20-alpine AS frontend

WORKDIR /app/frontend

COPY frontend/package.json .
RUN npm install

COPY frontend/ .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


# ──────────────────────────────────────────────
# Stage 2: backend  (also used for the Celery worker)
# ──────────────────────────────────────────────
FROM python:3.12-slim AS backend

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -Ls https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy dependency files first for layer caching
COPY backend/pyproject.toml .
COPY backend/uv.lock* ./

# Install Python dependencies
RUN uv sync --no-dev

# Copy application source
COPY backend/ .

# Copy and set up entrypoint
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
