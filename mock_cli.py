#!/usr/bin/env python3
"""
Skrip CLI Contoh (Mock CLI) untuk pengujian lokal.
Mendukung argumen model (--model / -m) untuk simulasi CLI AI.
"""
import sys
import time


def main():
    args = sys.argv[1:]
    model_name = "default"
    non_flag_args = []

    # Parsing flag sederhana (--model <nama> atau -m <nama>)
    i = 0
    while i < len(args):
        if args[i] in ("--model", "-m") and i + 1 < len(args):
            model_name = args[i + 1]
            i += 2
        else:
            non_flag_args.append(args[i])
            i += 1

    if non_flag_args:
        input_text = " ".join(non_flag_args).strip()
    else:
        input_text = sys.stdin.read().strip()

    if not input_text:
        print("Error: Input prompt kosong.", file=sys.stderr)
        sys.exit(1)

    # Contoh simulasi error jika prompt berisi keyword 'trigger-error'
    if "trigger-error" in input_text.lower():
        print(f"Error: Perintah gagal memproses input '{input_text}'", file=sys.stderr)
        sys.exit(2)

    # Contoh simulasi long-running task jika prompt berisi keyword 'trigger-timeout'
    if "trigger-timeout" in input_text.lower():
        time.sleep(10)

    # Output sukses standar dengan informasi model yang digunakan
    print(f"[Mock CLI Berhasil | Model: {model_name}]: Input diterima -> '{input_text}'")


if __name__ == "__main__":
    main()
