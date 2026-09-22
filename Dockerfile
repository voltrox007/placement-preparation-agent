FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    HOME=/app \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    DEPLOYMENT_ENVIRONMENT=local \
    AUTH_MODE=local_demo \
    DATABASE_URL=sqlite:////app/data/private/placement.db \
    PRIVATE_STORAGE_DIR=/app/data/private

WORKDIR /app
COPY requirements.lock pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.lock
COPY app.py ./
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./
COPY scripts/healthcheck.py ./scripts/healthcheck.py
RUN mkdir -p /app/.streamlit /app/data/private /app/data/runtime && chown -R 10001:10001 /app
USER 10001

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "scripts/healthcheck.py"]
CMD ["streamlit", "run", "app.py", "--server.headless=true"]
