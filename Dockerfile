FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    FAC_DATABASE_URL=sqlite:////app/data/fac.db \
    FAC_DEMO_ENABLED=false

WORKDIR /app

COPY pyproject.toml README.md ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src
COPY fixtures ./fixtures
COPY scripts ./scripts

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

RUN mkdir -p /app/data

VOLUME ["/app/data"]

EXPOSE 8000

CMD ["sh", "-c", "python -m alembic upgrade head && exec uvicorn fac.main:create_app --factory --host 0.0.0.0 --port 8000"]
