#!/bin/bash

echo "===== MD5 HASHING BENCHMARK ====="

python3 - <<'PY'
import hashlib
import time

password = b"student123"
N = 100000

start = time.perf_counter()

for _ in range(N):
    hashlib.md5(password).digest()

end = time.perf_counter()

avg_ms = (end - start) / N * 1000
print(f"MD5 average hashing time: {avg_ms:.6f} ms")
PY

echo
echo "===== MD5 CRACK TEST ====="

rm -f lab/redteam/md5/test.pot

time john \
  --format=Raw-MD5 \
  --wordl
echo
echo "===== MD5 CRACK TEST ====="

rm -f lab/redteam/md5/test.pot

time john \
  --format=Raw-MD5 \
  --wordlist=lab/redteam/wordlists/wordlist-100.txt \
  --pot=lab/redteam/md5/test.pot \
  lab/redteam/md5/hash.txt 
exit
