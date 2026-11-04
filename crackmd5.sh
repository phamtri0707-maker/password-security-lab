#!/bin/bash



echo "=== MD5 HASHING BENCHMARK ==="



python3 - << 'PY'

import hashlib

import time



password = b"123456"

 = 100000



start = time.perfcounter(

for  in range:

    hashlib.md5password.digest

end = time.perfcounter)



avgms = end - start /   1000

printf5 average hashing time avgms.6f ms





echo 

echo === 5   ===



rm -f /.john/john.pot



time john \

  --format=aw-5 \

  --wordlist=wordlists/wordlist.txt \

  hashes/md5.txt 21  tee results/md5/result.txt



echo ===  O ===
