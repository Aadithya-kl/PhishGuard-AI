FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl libmagic1 && rm -rf /var/lib/apt/lists/*
RUN useradd -m -r appuser
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
RUN mkdir -p /app/uploads /app/reports && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
