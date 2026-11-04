#!/bin/bash

rm -f lab/redteam/sha1/test.pot

time john \
  --format=Raw-SHA1 \
  --wordlist=lab/redteam/wordlist.txt \
  --pot=lab/redteam/sha1/test.pot \
  lab/redteam/sha1/hash.txt

