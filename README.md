# AGY FastAPI CLI Wrapper (Windows Mini PC & Cloud Ready)

REST API server berbasis Python (FastAPI + Uvicorn) yang membungkus (*wrapper*) Command Line Interface **Antigravity (`agy`)** agar dapat dieksekusi via panggilan HTTP request oleh chatbot Anda (**Chiko**), menggunakan kuota mingguan dan limit 5 jam dari akun AGY Anda.

Dapat dijalankan langsung di **Windows Mini PC** (selalu aktif 24/7), atau di lingkungan Docker/Render.

---

## 📁 Struktur Direktori

```text
.
├── start_server_windows.bat  # Klik 2x untuk menjalankan server di Windows Mini PC
├── start_tunnel_windows.bat  # Klik 2x untuk mendapatkan URL HTTPS publik via Cloudflare Tunnel
├── main.py                   # Server FastAPI & async executor agy (Cross-Platform)
├── .env                      # File konfigurasi lokal (token, command, default model)
├── requirements.txt          # Dependensi Python (FastAPI, Uvicorn, Pydantic)
├── Dockerfile                # Docker image containerization
├── render.yaml               # Blueprint Render.com
└── README.md                 # Panduan instalasi dan penggunaan
```

---

## 🖥️ Panduan Menjalankan di Windows Mini PC (24/7)

### Langkah 1: Persiapan di Windows Mini PC
1. Pastikan **Python** sudah terinstall (unduh dari [python.org](https://www.python.org/downloads/) dan pastikan centang opsi *"Add python.exe to PATH"* saat instalasi).
2. Pastikan **Git** sudah terinstall.
3. Pastikan **`agy`** sudah terinstall dan login ke akun Google Anda:
   - Buka Command Prompt (cmd) dan pastikan perintah `agy` bisa dijalankan.
   - Login dengan akun Anda jika belum: `agy auth login`.

---

### Langkah 2: Clone Repository Ini ke Mini PC
Buka Command Prompt atau PowerShell di Mini PC Anda:
```cmd
git clone https://github.com/ErwinYasa24/fastapi-cli-wrapper.git
cd fastapi-cli-wrapper
```

Buat file `.env` di dalam folder tersebut (atau salin dari contoh):
```env
CLI_COMMAND=agy --dangerously-skip-permissions
CLI_PROMPT_FLAG=-p
CLI_MODEL_FLAG=--model
DEFAULT_MODEL=gemini-3.8-flash
CLI_AUTH_TOKEN=ZrQ96ZZVnlGVjnpUSoNSiFviOLosGjEZtvcKXgp1jc0=
PORT=8000
```

---

### Langkah 3: Menjalankan Server (Cukup Klik 2x)
1. **Klik dua kali file `start_server_windows.bat`**.
   - Skrip ini akan otomatis membuat virtual environment, memasang library yang dibutuhkan, dan menyalakan server di `http://localhost:8000`.
2. **Klik dua kali file `start_tunnel_windows.bat`**.
   - Skrip ini akan otomatis mengunduh `cloudflared.exe` (jika belum ada) dan menghasilkan **URL HTTPS Publik** gratis, misalnya:
     `https://example-words-random.trycloudflare.com`

---

## 🤖 Menghubungkan Bot Chiko

Arahkan request dari bot Chiko ke URL publik dari Cloudflare Tunnel tersebut:

* **Endpoint:** `https://<URL_CLOUDFLARE_TUNNEL>/api/chat`
* **Header:**
  * `Content-Type: application/json`
  * `X-API-Key: ZrQ96ZZVnlGVjnpUSoNSiFviOLosGjEZtvcKXgp1jc0=`
* **JSON Body:**
  ```json
  {
    "prompt": "Halo Chiko!",
    "model": "gemini-3.8-flash",
    "timeout": 90
  }
  ```

---

## 🔄 Agar Otomatis Hidup Saat Windows Mini PC Dinyalakan (Auto-start)

1. Tekan tombol **Windows + R**, ketik `shell:startup`, lalu tekan **Enter**.
2. Jendela folder Startup Windows akan terbuka.
3. Buat *Shortcut* dari file **`start_server_windows.bat`** dan **`start_tunnel_windows.bat`**, lalu letakkan shortcut tersebut ke dalam folder Startup tersebut.
4. Selesai! Sekarang setiap kali Mini PC dinyalakan atau direstart, server dan tunnel akan langsung aktif otomatis.
