FROM python:3.14-slim

RUN pip install uv==0.10.* --no-cache-dir

WORKDIR /app
COPY . .

RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"

CMD ["gunicorn", "main:app", "-c", "core/gunicorn.py"]
