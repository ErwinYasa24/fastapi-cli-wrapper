# ==============================================================================
# Dockerfile untuk FastAPI CLI Wrapper (Kompatibel dengan Render.com)
# ==============================================================================
FROM python:3.11-slim

# Mencegah Python membuat file .pyc dan memastikan output log langsung dialirkan
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Install dependensi sistem dasar (curl untuk healthcheck, git & bash untuk utilitas CLI)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    bash \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Tentukan direktori kerja aplikasi di dalam container
WORKDIR /app

# Salin requirements dan install library Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode aplikasi ke dalam direktori kerja
COPY . /app/

# Buat dan gunakan non-root user demi standar keamanan container
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Dokumentasi port (Render mengabaikan EXPOSE dan mem-bind port dinamis via $PORT)
EXPOSE 8000

# Healthcheck internal container
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Jalankan Uvicorn membaca environment variable $PORT dari Render
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
