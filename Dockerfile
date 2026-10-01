FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

RUN addgroup --system h3app && adduser --system --ingroup h3app h3app \
    && mkdir -p /tmp/prometheus \
    && chown -R h3app:h3app /tmp/prometheus

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=h3app:h3app app ./app
COPY --chown=h3app:h3app scripts ./scripts
COPY --chown=h3app:h3app sql ./sql
COPY --chown=h3app:h3app tests ./tests
COPY --chown=h3app:h3app data ./data
COPY --chown=h3app:h3app benchmarks ./benchmarks

USER h3app

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz',timeout=3)"
