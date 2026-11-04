
#!/bin/bash

cd "$(dirname "$0")/../../.." || exit 1

.venv/bin/python - <<'PY'
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from pathlib import Path
import time

LIMIT = 5.0

target = Path("lab/redteam/argon2id/hash.txt").read_text().strip()
wordlist = Path("lab/redteam/wordlists/wordlist-100.txt").read_text().splitlines()

ph = PasswordHasher()

print("===== ARGON2ID TIMEOUT TEST =====")
print(f"Time limit: {LIMIT} seconds")
print(f"Wordlist size: {len(wordlist)}")

start = time.perf_counter()
attempts = 0
found = False

for candidate in wordlist:
    if time.perf_counter() - start >= LIMIT:
        break

    attempts += 1

    try:
        if ph.verify(target, candidate):
            found = True
            print(f"Password found: {candidate}")
            break
    except VerifyMismatchError:
        pass

elapsed = time.perf_counter() - start

print(f"Passwords tested: {attempts}")
print(f"Elapsed time: {elapsed:.3f} s")
print(f"Crack successful: {found}")

if not found:
    print("Password not found within lab window")
PY
