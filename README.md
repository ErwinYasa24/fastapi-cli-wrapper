# FastAPI CLI Wrapper (Docker & Render.com Ready)

REST API server berbasis Python (FastAPI + Uvicorn) yang membungkus (*wrapper*) Command Line Interface (CLI) tool agar dapat dieksekusi secara aman melalui panggilan HTTP request. Proyek ini sudah dikonfigurasi siap pakai untuk dideploy ke **Render.com** menggunakan **Docker**.

---

## 📁 Struktur Direktori

```text
.
├── Dockerfile          # Multi-stage/slim Docker configuration untuk Render.com
├── .dockerignore       # Daftar file/folder yang dikecualikan dari Docker build
├── main.py             # Aplikasi FastAPI & asynchronous CLI subprocess executor
├── mock_cli.py         # Skrip CLI percontohan untuk simulasi & pengujian lokal
├── render.yaml         # Blueprint Infrastructure-as-Code untuk Render.com
├── requirements.txt    # Dependensi Python (FastAPI, Uvicorn, Pydantic)
└── README.md           # Panduan lengkap instalasi, testing, dan deployment
```

---

## 🚀 Fitur Utama

- **FastAPI Asynchronous Subprocess**: Menggunakan `asyncio.create_subprocess_exec` tanpa `shell=True` untuk mencegah kerentanan *Shell Injection*.
- **Endpoint Healthcheck**: `GET /health` yang siap dipantau oleh monitoring Render.
- **Endpoint Eksekusi CLI**: `POST /api/chat` (dan alias `POST /api/run`) dengan batas `timeout` yang dapat disesuaikan per request.
- **Penanganan Error Komprehensif**:
  - Validasi schema input otomatis via Pydantic (HTTP 422).
  - Timeout eksekusi otomatis memutus proses CLI (*process kill*) dan mengembalikan HTTP 504.
  - Kegagalan proses CLI (return code != 0) menangkap `stderr` dan mengembalikannya dalam respon HTTP 500.
- **Keamanan & Autentikasi**: Mendukung verifikasi token via header `X-API-Key` atau `Authorization: Bearer <token>` menggunakan environment variable `CLI_AUTH_TOKEN` atau `API_KEY`.
- **Render.com Compatibility**: Menyesuaikan binding port dinamis via environment variable `$PORT`.

---

## ⚙️ Variabel Lingkungan (Environment Variables)

| Variabel | Default | Keterangan |
| :--- | :--- | :--- |
| `PORT` | `8000` | Port tempat Uvicorn mendengarkan request (diatur otomatis oleh Render). |
| `CLI_AUTH_TOKEN` / `API_KEY` | *(Kosong)* | Token rahasia untuk memproteksi API. Jika dikosongkan, API terbuka untuk publik. |
| `CLI_COMMAND` | `echo` | Perintah atau path biner CLI yang akan dipanggil (contoh: `python3 mock_cli.py`, `curl`, `my-tool`). |
| `CLI_INPUT_MODE` | `arg` | Mode pengiriman prompt: `arg` (sebagai argumen baris perintah) atau `stdin` (dialirkan lewat standar input). |

---

## 💻 Menjalankan Secara Lokal

### Opsi 1: Menjalankan Langsung dengan Python

1. **Buat virtual environment dan aktifkan:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Untuk Linux/macOS
   # venv\Scripts\activate   # Untuk Windows
   ```

2. **Install dependensi:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Jalankan server:**
   ```bash
   # Contoh menjalankan dengan Mock CLI lokal:
   export CLI_COMMAND="python3 mock_cli.py"
   export CLI_AUTH_TOKEN="rahasia123"
   python3 main.py
   ```
   Server akan aktif di `http://localhost:8000`. Dokumentasi interaktif Swagger UI tersedia di `http://localhost:8000/docs`.

---

### Opsi 2: Menjalankan Menggunakan Docker

1. **Build Docker image:**
   ```bash
   docker build -t fastapi-cli-wrapper .
   ```

2. **Jalankan Docker container:**
   ```bash
   docker run -d \
     -p 8000:8000 \
     -e PORT=8000 \
     -e CLI_AUTH_TOKEN=rahasia123 \
     -e CLI_COMMAND="python3 mock_cli.py" \
     --name cli-api-container \
     fastapi-cli-wrapper
   ```

3. **Cek log container:**
   ```bash
   docker logs -f cli-api-container
   ```

---

## 🧪 Pengujian API Menggunakan cURL

### 1. Healthcheck Endpoint (`GET /health`)
```bash
curl -i http://localhost:8000/health
```
**Respon (HTTP 200):**
```json
{
  "status": "healthy"
}
```

---

### 2. Eksekusi Berhasil (`POST /api/chat`)
Kirim request dengan header autentikasi (`X-API-Key` atau `Authorization: Bearer`):

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: rahasia123" \
  -d '{
    "prompt": "Halo dunia dari cURL",
    "timeout": 30
  }'
```

**Respon Sukses (HTTP 200):**
```json
{
  "success": true,
  "output": "[Mock CLI Berhasil]: Input yang diterima -> 'Halo dunia dari cURL'"
}
```

---

### 3. Simulasi Error CLI (HTTP 500)
Jika perintah CLI menghasilkan error (misal dengan mengirim prompt `trigger-error` ke `mock_cli.py`):

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: rahasia123" \
  -d '{
    "prompt": "trigger-error",
    "timeout": 30
  }'
```

**Respon Error (HTTP 500):**
```json
{
  "detail": "Perintah CLI gagal dieksekusi: Error: Perintah gagal memproses input 'trigger-error'"
}
```

---

### 4. Simulasi Timeout Eksekusi (HTTP 504)
Kirim prompt `trigger-timeout` dengan parameter timeout pendek (misal 2 detik):

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: rahasia123" \
  -d '{
    "prompt": "trigger-timeout",
    "timeout": 2
  }'
```

**Respon Timeout (HTTP 504):**
```json
{
  "detail": "Eksekusi CLI melebihi batas waktu (timeout 2 detik)."
}
```

---

### 5. Validasi Autentikasi Gagal (HTTP 401)
Jika token salah atau tidak dikirim:

```bash
curl -i -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "halo"
  }'
```

**Respon (HTTP 401 Unauthorized):**
```json
{
  "detail": "Autentikasi gagal: Token API tidak valid atau tidak disertakan."
}
```

---

## 🔧 Menyesuaikan Dockerfile untuk Tool CLI Kustom Anda

Jika tool CLI Anda membutuhkan biner khusus atau package manager pihak ketiga (misalnya `ffmpeg`, biner Go, npm package, atau dependensi C):

Cukup tambahkan langkah instalasi pada baris `apt-get` atau unduh biner tersebut di dalam `Dockerfile`:

```dockerfile
# Contoh menambahkan tool tambahan (misal: jq, ffmpeg):
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    bash \
    jq \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# ATAU mengunduh biner executable kustom:
# RUN curl -L -o /usr/local/bin/my-cli https://example.com/download/my-cli && \
#     chmod +x /usr/local/bin/my-cli
```

Lalu atur environment variable `CLI_COMMAND` menjadi path tool tersebut (misal: `/usr/local/bin/my-cli`).

---

## 🌐 Panduan Deployment ke Render.com

### Metode A: Menggunakan Render Blueprint (`render.yaml`) - Disarankan

1. Push seluruh kode repository ini ke GitHub / GitLab Anda.
2. Buka dashboard [Render.com](https://dashboard.render.com).
3. Klik tombol **New +** di pojok kanan atas, lalu pilih **Blueprint**.
4. Hubungkan repository GitHub/GitLab Anda.
5. Render akan secara otomatis membaca konfigurasi `render.yaml`:
   - Membuat Web Service dengan runtime Docker.
   - Mengatur healthcheck path ke `/health`.
   - Meng-generate nilai aman untuk `CLI_AUTH_TOKEN`.
6. Klik **Apply**. Render akan memulai build Docker dan service Anda akan langsung online!

---

### Metode B: Manual Deploy via Render Dashboard

1. Di Render Dashboard, klik **New +** -> **Web Service**.
2. Pilih repository Anda.
3. Konfigurasikan pengaturan:
   - **Name**: `fastapi-cli-wrapper` (atau nama lain pilihan Anda).
   - **Language / Runtime**: Pilih `Docker`.
   - **Region**: Pilih yang terdekat (contoh: *Singapore*).
   - **Branch**: `main`.
4. Di bagian **Advanced Settings**:
   - **Health Check Path**: `/health`
   - **Environment Variables**:
     - `CLI_AUTH_TOKEN`: Masukkan string token rahasia Anda.
     - `CLI_COMMAND`: Sesuaikan perintah (contoh: `python3 mock_cli.py`).
     - `CLI_INPUT_MODE`: `arg`
5. Klik **Create Web Service**.
