
import csv
import time
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError

ROOT = Path(__file__).resolve().parents[3]

# 4 hash gia lap bi lo tu Blue Team
HASH_FILE = Path("/tmp/ptit_lab_leaked_4.csv")

# Wordlist 100 mat khau da them 4 mat khau thu nghiem
WORDLIST = ROOT / "lab/redteam/wordlists/wordlist-100.txt"

with HASH_FILE.open(newline="", encoding="utf-8") as f:
    targets = list(csv.DictReader(f))

candidates = [
    line.strip()
    for line in WORDLIST.read_text(encoding="utf-8").splitlines()
    if line.strip()
]

hasher = PasswordHasher()
recovered = 0
total_attempts = 0

print("=== RED TEAM: OFFLINE ATTACK ===")
print("Hash targets:", len(targets))
print("Wordlist size:", len(candidates))
print("Pepper known: NO")
print()

for target in targets:
    username = target["username"]
    target_hash = target["password_hash"]

    if not target_hash.startswith("$argon2id$"):
        raise RuntimeError(f"{username}: invalid Argon2id hash")

    found = None
    attempts = 0
    start = time.perf_counter()

    for candidate in candidates:
        attempts += 1

        try:
            if hasher.verify(target_hash, candidate):
                found = candidate
                break
        except (VerificationError, InvalidHashError):
            pass

    elapsed = time.perf_counter() - start
    total_attempts += attempts

    if found is not None:
        recovered += 1

    print(f"User: {username}")
    print(f"  Found: {found is not None}")
    print(f"  Attempts: {attempts}")
    print(f"  Time: {elapsed:.3f} s")
    print()

print("=== SUMMARY ===")
print(f"Recovered: {recovered}/{len(targets)}")
print(f"Total attempts: {total_attempts}")
