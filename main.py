import asyncio
import os
import shlex
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ==============================================================================
# Konfigurasi Environment & Autentikasi
# ==============================================================================
# Token autentikasi untuk membatasi akses (opsional, jika kosong tidak ada auth check)
AUTH_TOKEN = os.getenv("CLI_AUTH_TOKEN") or os.getenv("API_KEY")

# Command CLI dasar yang akan dibungkus (contoh: 'echo', 'git', atau path binary tool kustom)
CLI_COMMAND = os.getenv("CLI_COMMAND", "echo")

# Mode input:
# - 'arg'   : prompt dikirimkan sebagai argumen baris perintah (contoh: `my-cli "halo"`)
# - 'stdin' : prompt dikirimkan melalui stdin stream (cocok untuk tool REPL/interaktif)
CLI_INPUT_MODE = os.getenv("CLI_INPUT_MODE", "arg").lower()

# ==============================================================================
# Inisialisasi Aplikasi FastAPI
# ==============================================================================
app = FastAPI(
    title="CLI Wrapper REST API",
    description="FastAPI service wrapper untuk mengeksekusi Command Line Interface (CLI) tool secara asynchronous.",
    version="1.0.0",
)

# CORS Middleware (mengizinkan pemanggilan dari browser / frontend jika diperlukan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# Model Skema Data (Pydantic)
# ==============================================================================
class RunRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=1,
        description="Teks instruksi atau input yang akan dikirimkan ke CLI tool.",
        examples=["Halo dari REST API"],
    )
    timeout: int = Field(
        default=60,
        ge=1,
        le=600,
        description="Batas waktu eksekusi dalam detik (default: 60, max: 600).",
        examples=[60],
    )


class RunResponse(BaseModel):
    success: bool = Field(..., description="Status keberhasilan eksekusi CLI.")
    output: str = Field(..., description="Hasil output standar (stdout) dari proses CLI.")


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["healthy"])


# ==============================================================================
# Helper Autentikasi
# ==============================================================================
def verify_authentication(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> None:
    """
    Memvalidasi token jika AUTH_TOKEN / API_KEY diset pada environment variable.
    Mendukung header 'X-API-Key: <token>' atau 'Authorization: Bearer <token>'.
    """
    if not AUTH_TOKEN:
        # Jika tidak ada token yang disetel di server, bypass autentikasi
        return

    provided_token = None
    if x_api_key:
        provided_token = x_api_key.strip()
    elif authorization:
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            provided_token = parts[1]
        else:
            provided_token = authorization.strip()

    if not provided_token or provided_token != AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autentikasi gagal: Token API tidak valid atau tidak disertakan.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ==============================================================================
# Helper Eksekutor Subprocess (Asynchronous & Safe)
# ==============================================================================
async def execute_cli(prompt: str, timeout: int) -> str:
    """
    Mengeksekusi CLI tool secara asynchronous dan aman tanpa `shell=True`
    untuk mencegah risiko shell injection.
    """
    # Parsing perintah dasar CLI
    base_args = shlex.split(CLI_COMMAND)
    if not base_args:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Konfigurasi CLI_COMMAND kosong atau tidak valid.",
        )

    # Tentukan argumen dan stdin sesuai CLI_INPUT_MODE
    stdin_data: Optional[bytes] = None
    if CLI_INPUT_MODE == "stdin":
        cmd_args = base_args
        stdin_data = prompt.encode("utf-8")
    else:
        # Mode 'arg': prompt ditambahkan sebagai argumen baris perintah
        cmd_args = base_args + [prompt]

    # Jalankan subprocess secara asynchronous
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdin=asyncio.subprocess.PIPE if stdin_data is not None else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Perintah/binary '{base_args[0]}' tidak ditemukan pada sistem.",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal memulai proses CLI: {str(exc)}",
        )

    # Tunggu output dengan batas waktu (timeout)
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=stdin_data),
            timeout=float(timeout),
        )
    except asyncio.TimeoutError:
        # Hentikan proses jika melebihi batas waktu
        try:
            process.kill()
            await process.wait()
        except ProcessLookupError:
            pass

        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Eksekusi CLI melebihi batas waktu (timeout {timeout} detik).",
        )

    # Dekode output stdout dan stderr
    stdout_text = stdout.decode("utf-8", errors="replace").strip()
    stderr_text = stderr.decode("utf-8", errors="replace").strip()

    # Periksa status return code dari CLI
    if process.returncode != 0:
        error_msg = stderr_text if stderr_text else f"CLI exit code: {process.returncode}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Perintah CLI gagal dieksekusi: {error_msg}",
        )

    return stdout_text


# ==============================================================================
# Endpoints
# ==============================================================================
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Monitoring"],
    summary="Health check endpoint",
)
async def health_check():
    """
    Endpoint healthcheck sederhana untuk memonitor ketersediaan aplikasi di Render.com.
    """
    return {"status": "healthy"}


@app.post(
    "/api/chat",
    response_model=RunResponse,
    tags=["CLI Execution"],
    summary="Kirim prompt instruksi ke CLI tool",
)
@app.post(
    "/api/run",
    response_model=RunResponse,
    tags=["CLI Execution"],
    summary="Alias untuk /api/chat",
    include_in_schema=False,
)
async def run_cli_handler(
    payload: RunRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Menerima JSON prompt dan timeout, menjalankan perintah CLI,
    dan mengembalikan hasilnya dalam format JSON.
    """
    # 1. Validasi Autentikasi
    verify_authentication(x_api_key=x_api_key, authorization=authorization)

    # 2. Eksekusi CLI Asynchronous
    output_text = await execute_cli(prompt=payload.prompt, timeout=payload.timeout)

    # 3. Return JSON Response
    return RunResponse(success=True, output=output_text)


# ==============================================================================
# Direct execution (untuk testing lokal dengan `python main.py`)
# ==============================================================================
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
