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

- **Pemilihan Model Dinamis oleh Client (Chiko)**: Client dapat menentukan model secara bebas di setiap request via field `"model"`, atau mengandalkan default server.
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
| `CLI_COMMAND` | `echo` | Perintah atau path biner CLI yang akan dipanggil (contoh: `python3 mock_cli.py`, `my-tool`). |
| `DEFAULT_MODEL` | `gemini-1.5-flash` | Model default yang digunakan jika client (Chiko) tidak mengirim parameter `model`. |
| `CLI_MODEL_FLAG` | `--model` | Flag argumen model yang disematkan saat memanggil CLI tool (contoh: `--model` atau `-m`). |
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

### 2. Eksekusi dengan Model Dinamis dari Client (Chiko)
Kirim request dengan menentukan model secara bebas:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: rahasia123" \
  -d '{
    "prompt": "Halo Chiko!",
    "model": "gemini-1.5-flash",
    "timeout": 30
  }'
```

**Respon Sukses (HTTP 200):**
```json
{
  "success": true,
  "output": "[Mock CLI Berhasil | Model: gemini-1.5-flash]: Input diterima -> 'Halo Chiko!'",
  "model": "gemini-1.5-flash"
}
```

---

### 3. Simulasi Error CLI (HTTP 500)
Jika perintah CLI menghasilkan error (misal mengirim prompt `trigger-error`):

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

## 🌐 Panduan Deployment ke Render.com

1. Buka dashboard [Render.com](https://dashboard.render.com).
2. Klik tombol **New +** -> **Blueprint**.
3. Pilih repository **`ErwinYasa24/fastapi-cli-wrapper`**.
4. Klik **Deploy Blueprint**.
5. Render akan secara otomatis mem-build Docker container dan mendeploy web service Anda.
