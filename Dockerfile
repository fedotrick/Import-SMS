FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY main.py ./
COPY .env.example ./
COPY Контроль ./Контроль

RUN groupadd --system app \
    && useradd --system --gid app --create-home appuser \
    && chown -R appuser:app /app

USER appuser

CMD ["python", "main.py"]
