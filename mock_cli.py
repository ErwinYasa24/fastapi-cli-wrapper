#!/usr/bin/env python3
"""
Skrip CLI Contoh (Mock CLI) untuk pengujian lokal.
Anda dapat mengganti ini dengan tool CLI sebenarnya yang ingin Anda bungkus.
"""
import sys
import time


def main():
    if len(sys.argv) < 2:
        # Jika dipanggil tanpa argumen, baca dari stdin
        input_text = sys.stdin.read().strip()
    else:
        input_text = " ".join(sys.argv[1:]).strip()

    if not input_text:
        print("Error: Input kosong tidak diizinkan.", file=sys.stderr)
        sys.exit(1)

    # Contoh simulasi error jika prompt berisi keyword 'trigger-error'
    if "trigger-error" in input_text.lower():
        print(f"Error: Perintah gagal memproses input '{input_text}'", file=sys.stderr)
        sys.exit(2)

    # Contoh simulasi long-running task jika prompt berisi keyword 'trigger-timeout'
    if "trigger-timeout" in input_text.lower():
        time.sleep(10)

    # Output sukses standar
    print(f"[Mock CLI Berhasil]: Input yang diterima -> '{input_text}'")


if __name__ == "__main__":
    main()
