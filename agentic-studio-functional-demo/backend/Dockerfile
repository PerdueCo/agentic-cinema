FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY agentic-studio-functional-demo/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --requirement requirements.txt

COPY agentic-studio-functional-demo/backend/app ./app
COPY src ./src

RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
