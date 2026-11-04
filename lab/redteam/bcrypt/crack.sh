#!/bin/bash

echo "===== BCRYPT HASHING BENCHMARK ====="

.venv/bin/python - <<'PY'
import bcrypt
import time

password = b"student123"
cost = 12
salt = bcrypt.gensalt(rounds=cost)

N = 5

start = time.perf_counter()

for _ in range(N):
    bcrypt.hashpw(password, salt)

end = time.perf_counter()

avg_ms = (end - start) / N * 1000

print(f"bcrypt cost factor: {cost}")
print(f"bcrypt average hashing time: {avg_ms:.3f} ms")
PY

echo
echo "===== BCRYPT CRACK TEST ====="

rm -f lab/redteam/bcrypt/test.pot

time john \
  --format=bcrypt \
  --wordlist=lab/redteam/wordlist.txt \
  --pot=lab/redteam/bcrypt/test.pot \
  lab/redteam/bcrypt/hash.txt
