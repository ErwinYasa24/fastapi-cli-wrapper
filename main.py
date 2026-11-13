import asyncio
import os
import shlex
import shutil
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# ==============================================================================
# Helper Load File .env (Otomatis tanpa dependensi tambahan)
# ==============================================================================
def load_env_file():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = val


load_env_file()

# ==============================================================================
# Konfigurasi Environment & Autentikasi
# ==============================================================================
AUTH_TOKEN = os.getenv("CLI_AUTH_TOKEN") or os.getenv("API_KEY")

# Deteksi lokasi agy di Windows, macOS, atau Linux
detected_agy = shutil.which("agy") or shutil.which("agy.exe")
if not detected_agy:
    user_home = os.path.expanduser("~")
    possible_paths = [
        os.path.join(user_home, ".local", "bin", "agy.exe"),
        os.path.join(user_home, ".local", "bin", "agy"),
        os.path.join(user_home, "AppData", "Local", "Programs", "agy", "agy.exe"),
    ]
    for p in possible_paths:
        if os.path.isfile(p):
            detected_agy = p
            break

DEFAULT_CLI_CMD = (
    f'"{detected_agy}" --dangerously-skip-permissions'
    if detected_agy
    else "agy --dangerously-skip-permissions"
)

# Command CLI dasar yang akan dibungkus
CLI_COMMAND = os.getenv("CLI_COMMAND", DEFAULT_CLI_CMD)

# Default model AI (menggunakan model agy)
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-3.8-flash")

# Flag argumen untuk model pada CLI tool
CLI_MODEL_FLAG = os.getenv("CLI_MODEL_FLAG", "--model")

# Flag argumen untuk prompt (untuk agy menggunakan '-p')
CLI_PROMPT_FLAG = os.getenv("CLI_PROMPT_FLAG", "-p" if "agy" in CLI_COMMAND else "")

# Mode input: 'arg' atau 'stdin'
CLI_INPUT_MODE = os.getenv("CLI_INPUT_MODE", "arg").lower()

# ==============================================================================
# Inisialisasi Aplikasi FastAPI
# ==============================================================================
app = FastAPI(
    title="AGY CLI Wrapper REST API",
    description="FastAPI service wrapper untuk mengeksekusi Antigravity (agy) CLI tool di Windows / macOS / Linux.",
    version="1.3.0",
)

# CORS Middleware
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
    model: Optional[str] = Field(
        default=None,
        description="Nama model AI (misal: 'gemini-3.8-flash', 'gemini-1.5-flash', dll).",
        examples=["gemini-3.8-flash"],
    )
    timeout: int = Field(
        default=90,
        ge=1,
        le=600,
        description="Batas waktu eksekusi dalam detik (default: 90, max: 600).",
        examples=[90],
    )


class RunResponse(BaseModel):
    success: bool = Field(..., description="Status keberhasilan eksekusi CLI.")
    output: str = Field(..., description="Hasil output standar (stdout) dari proses CLI.")
    model: Optional[str] = Field(default=None, description="Nama model yang digunakan saat eksekusi.")


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["healthy"])


# ==============================================================================
# Helper Autentikasi
# ==============================================================================
def verify_authentication(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> None:
    if not AUTH_TOKEN:
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
# Helper Eksekutor Subprocess (Cross-platform Windows/Mac/Linux)
# ==============================================================================
async def execute_cli(prompt: str, timeout: int, model: Optional[str] = None) -> tuple[str, str]:
    # Parsing perintah dasar CLI dengan kompatibilitas Windows / POSIX
    is_windows = os.name == "nt"
    base_args = shlex.split(CLI_COMMAND, posix=not is_windows)
    if not base_args:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Konfigurasi CLI_COMMAND kosong atau tidak valid.",
        )

    # Tentukan model aktif
    active_model = model.strip() if model and model.strip() else DEFAULT_MODEL

    cmd_args = list(base_args)

    if active_model and CLI_MODEL_FLAG:
        cmd_args.extend([CLI_MODEL_FLAG, active_model])

    stdin_data: Optional[bytes] = None
    if CLI_INPUT_MODE == "stdin":
        stdin_data = prompt.encode("utf-8")
    else:
        if CLI_PROMPT_FLAG:
            cmd_args.extend([CLI_PROMPT_FLAG, prompt])
        else:
            cmd_args.append(prompt)

    # Siapkan subprocess environment
    sub_env = os.environ.copy()
    if active_model:
        sub_env["MODEL"] = active_model
        sub_env["CLI_MODEL"] = active_model

    # Jalankan subprocess secara asynchronous
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdin=asyncio.subprocess.PIPE if stdin_data is not None else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=sub_env,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Perintah/binary '{base_args[0]}' tidak ditemukan pada sistem Windows/Mini PC.",
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
        try:
            process.kill()
            await process.wait()
        except ProcessLookupError:
            pass

        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Eksekusi CLI melebihi batas waktu (timeout {timeout} detik).",
        )

    stdout_text = stdout.decode("utf-8", errors="replace").strip()
    stderr_text = stderr.decode("utf-8", errors="replace").strip()

    if process.returncode != 0:
        error_msg = stderr_text if stderr_text else f"CLI exit code: {process.returncode}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Perintah CLI gagal dieksekusi: {error_msg}",
        )

    return stdout_text, active_model


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
    return {"status": "healthy"}


@app.post(
    "/api/chat",
    response_model=RunResponse,
    tags=["CLI Execution"],
    summary="Kirim prompt instruksi dan model ke CLI tool",
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
    verify_authentication(x_api_key=x_api_key, authorization=authorization)
    output_text, active_model = await execute_cli(
        prompt=payload.prompt,
        timeout=payload.timeout,
        model=payload.model,
    )
    return RunResponse(success=True, output=output_text, model=active_model)


# ==============================================================================
# Direct execution
# ==============================================================================
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
