FROM python:3.14-slim

RUN pip install uv==0.10.* --no-cache-dir

WORKDIR /app
COPY . .

ARG MODE=locale
RUN if [ "$MODE" = "debug" ]; then uv sync --frozen; else uv sync --frozen --no-dev; fi
ENV PATH="/app/.venv/bin:$PATH"

CMD ["gunicorn", "main:app", "-c", "core/gunicorn.py"]
