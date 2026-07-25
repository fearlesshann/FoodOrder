FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/pip \
    mkdir -p app && touch app/__init__.py \
    && pip install --default-timeout=120 --retries 10 .

COPY app ./app

RUN addgroup --system dinner && adduser --system --ingroup dinner dinner \
    && mkdir -p /data && chown -R dinner:dinner /data

USER dinner

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
