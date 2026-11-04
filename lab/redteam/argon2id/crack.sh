
#!/bin/bash

cd "$(dirname "$0")/../../.." || exit 1

.venv/bin/python - <<'PY'
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError
from pathlib import Path
import time

password = "student123"

ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    type=Type.ID
)

print("===== ARGON2ID HASHING BENCHMARK =====")
print("Memory cost: 65536 KiB")
print("Time cost: 3")
print("Parallelism: 4")

N = 3
start = time.perf_counter()

for _ in range(N):
    ph.hash(password)

elapsed = time.perf_counter() - start
print(f"Average hashing time: {elapsed / N * 1000:.3f} ms")

print()
print("===== ARGON2ID CRACK TEST =====")

target = Path("lab/redteam/argon2id/hash.txt").read_text().strip()
pot_file = Path("lab/redteam/argon2id/test.pot")
pot_file.unlink(missing_ok=True)

start = time.perf_counter()
attempts = 0
found = False

with open("lab/redteam/wordlist.txt", encoding="utf-8") as f:
    for line in f:
        candidate = line.rstrip("\r\n")
        attempts += 1

        try:
            if ph.verify(target, candidate):
                found = True
                print(f"Password found: {candidate}")

                pot_file.write_text(f"{target}:{candidate}\n")
                break
        except VerifyMismatchError:
            pass

elapsed = time.perf_counter() - start

print(f"Passwords tested: {attempts}")
print(f"Crack successful: {found}")
print(f"Crack time: {elapsed:.3f} s")
PY

