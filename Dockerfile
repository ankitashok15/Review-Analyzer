FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN sed -i 's/\r$//' scripts/start_api.sh && chmod +x scripts/start_api.sh

EXPOSE 8000

# Shell form ensures Railway's injected $PORT is used when startCommand is not overridden.
CMD /bin/sh -c "exec uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"
