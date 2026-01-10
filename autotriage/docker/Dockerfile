FROM node:20-alpine AS webbuild
WORKDIR /app
COPY web/package.json web/package-lock.json* web/ ./
RUN npm install
COPY web/ ./web/
WORKDIR /app/web
RUN npm run build

FROM python:3.11-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY pyproject.toml README.md ./
COPY autotriage/ ./autotriage/
COPY data/ ./data/
RUN pip install -U pip && pip install -e ".[dev]" --no-cache-dir
COPY --from=webbuild /app/web/dist/ ./autotriage/app/static/
EXPOSE 8080
CMD ["python", "-m", "autotriage.cli.main", "run", "--mode", "all", "--host", "0.0.0.0", "--port", "8080"]

