FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt ./
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
RUN groupadd -r app && useradd -r -g app app && \
    mkdir -p /app/uploads && chown -R app:app /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder --chown=app:app /opt/venv /opt/venv
COPY --chown=app:app app/ ./app

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN chmod -R 755 /app && \
    chmod -R 700 /app/uploads

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

USER app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
