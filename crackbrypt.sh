#!/bin/bash
set -o pipefail

cd "$(dirname "$0")/../../.." || exit 1

HASH_FILE="hashes/bcrypt/hashes.txt"
WORDLIST="wordlists/lab.txt"
POT_FILE="/tmp/password-lab-bcrypt-redteam.pot"
RESULT_FILE="results/bcrypt/result.txt"

if [[ ! -f "$HASH_FILE" || ! -f "$WORDLIST" ]]; then
    echo "Không tìm thấy file hash hoặc wordlist."
    echo "Kiểm tra: $HASH_FILE và $WORDLIST"
    exit 1
fi

{
    echo "===== BCRYPT OFFLINE DICTIONARY TEST ====="
    date
    /usr/bin/time -p john \
        --format=bcrypt \
        --wordlist="$WORDLIST" \
        --pot="$POT_FILE" \
        "$HASH_FILE"

    echo
    echo "===== KẾT QUẢ ====="
    john --show --format=bcrypt --pot="$POT_FILE" "$HASH_FILE"
} 2>&1 | tee "$RESULT_FILE"
