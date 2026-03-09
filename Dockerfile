FROM python:3.11-slim

# Tambahkan libpq-dev agar driver database bisa terinstal dengan benar
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Pastikan CMD menjalankan gunicorn dengan konfigurasi yang benar
CMD ["gunicorn", "-k", "gevent", "--bind", ":8080", "--workers", "2", "run:app"]