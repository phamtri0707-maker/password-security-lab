#!/bin/bash
set -o pipefail

cd "$(dirname "$0")/../../.." || exit 1

HASH_FILE="hashes/argon2id/hashes.txt"
WORDLIST="wordlists/lab.txt"
RESULT_FILE="results/argon2id/result.txt"

if [[ ! -f "$HASH_FILE" || ! -f "$WORDLIST" ]]; then
    echo "Không tìm thấy file hash hoặc wordlist."
    echo "Kiểm tra: $HASH_FILE và $WORDLIST"
    exit 1
fi

python3 - <<'PY' 2>&1 | tee "results/argon2id/result.txt"
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from pathlib import Path
import time

target = Path("hashes/argon2id/hashes.txt").read_text().strip()
wordlist = Path("wordlists/lab.txt")

hasher = PasswordHasher()
attempts = 0
found = False
start = time.perf_counter()

with wordlist.open(encoding="utf-8") as file:
    for line in file:
        candidate = line.rstrip("\r\n")
        if not candidate:
            continue

        attempts += 1
        try:
            if hasher.verify(target, candidate):
                print(f"Mật khẩu tìm thấy: {candidate}")
                found = True
                break
        except VerifyMismatchError:
            pass
        except InvalidHashError:
            print("File hash không chứa hash Argon2 hợp lệ.")
            raise SystemExit(1)

elapsed = time.perf_counter() - start
print(f"Số ứng viên đã thử: {attempts}")
print(f"Tìm thấy bằng wordlist này: {'Có' if found else 'Không'}")
print(f"Thời gian thử: {elapsed:.3f} giây")
PY
