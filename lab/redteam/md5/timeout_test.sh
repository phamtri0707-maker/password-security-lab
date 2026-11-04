
#!/bin/bash

cd "$(dirname "$0")/../../.." || exit 1

echo "===== MD5 TIMEOUT TEST ====="
echo "Time limit: 5 seconds"
echo "Wordlist: 100 passwords"

rm -f lab/redteam/md5/timeout.pot

time timeout 5s john \
  --format=Raw-MD5 \
  --wordlist=lab/redteam/wordlists/wordlist-100.txt \
  --pot=lab/redteam/md5/timeout.pot \
  lab/redteam/md5/hash.txt

echo
echo "===== CRACK RESULT ====="

john --show \
  --format=Raw-MD5 \
  --pot=lab/redteam/md5/timeout.pot \
  lab/redteam/md5/hash.txt

