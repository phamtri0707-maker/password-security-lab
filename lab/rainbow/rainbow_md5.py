
import hashlib
import json
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

WORDLIST_PATH = ROOT / "data/wordlist.txt"
HASHES_PATH = ROOT / "data/hashes/md5.txt"
TARGETS_PATH = ROOT / "data/targets.txt"
TABLE_PATH = ROOT / "lab/rainbow/md5_table.json"

WORDLIST = WORDLIST_PATH.read_text(encoding="utf-8").splitlines()

CHAIN_COUNT = 200
CHAIN_LENGTH = 6


# Ham bam MD5
def H(password):
    return hashlib.md5(password.encode("utf-8")).hexdigest()


# Reduction: chuyen hash thanh mot ung vien trong Wordlist
def R(hash_hex, position):
    digest = hashlib.sha256(
        f"{position}:{hash_hex}".encode()
    ).digest()

    index = int.from_bytes(digest[:8], "big") % len(WORDLIST)
    return WORDLIST[index]


# Giai doan 1: Tao Rainbow Table
def build():
    chains = []
    starts = random.Random(7007).sample(WORDLIST, CHAIN_COUNT)

    for start in starts:
        current = start

        for position in range(CHAIN_LENGTH):
            current = R(H(current), position)

        chains.append([start, current])

    table = {
        "wordlist_sha256": hashlib.sha256(
            WORDLIST_PATH.read_bytes()
        ).hexdigest(),
        "length": CHAIN_LENGTH,
        "chains": chains,
    }

    TABLE_PATH.write_text(
        json.dumps(table, indent=2),
        encoding="utf-8"
    )

    print(f"BUILD: {len(chains)} chains x {CHAIN_LENGTH} steps")
    print(f"Saved: {TABLE_PATH}")


def read_table():
    table = json.loads(TABLE_PATH.read_text(encoding="utf-8"))

    actual = hashlib.sha256(WORDLIST_PATH.read_bytes()).hexdigest()

    if actual != table["wordlist_sha256"]:
        raise SystemExit("Wordlist changed. Build the table again.")

    return table


# Tim mat khau tu hash bang Rainbow Table
def lookup(target_hash, table):
    ends = defaultdict(list)

    for start, end in table["chains"]:
        ends[end].append(start)

    for position in reversed(range(table["length"])):
        h = target_hash

        for i in range(position, table["length"]):
            candidate = R(h, i)

            if i < table["length"] - 1:
                h = H(candidate)

        for start in ends.get(candidate, []):
            password = start

            for i in range(table["length"]):
                hashed = H(password)

                if hashed == target_hash:
                    return password

                password = R(hashed, i)

    return None


# Giai doan 2: Crack 3 hash MD5 trong repo
def crack():
    table = read_table()
    hashes = HASHES_PATH.read_text(encoding="utf-8").splitlines()

    recovered = 0

    for index, target_hash in enumerate(hashes, 1):
        password = lookup(target_hash, table)

        print(
            f"target_{index}: "
            f"{password if password is not None else 'NOT FOUND'}"
        )

        recovered += password is not None

    print(f"RESULT: {recovered}/{len(hashes)} recovered")


# Giai doan 3: Kiem tra tac dung cua Salt
def salt():
    table = read_table()

    password = TARGETS_PATH.read_text(
        encoding="utf-8"
    ).splitlines()[0]

    salt_bytes = os.urandom(16)

    salted_hash = hashlib.md5(
        salt_bytes + password.encode("utf-8")
    ).hexdigest()

    print("Unsalted MD5:", H(password))
    print("Lookup:", lookup(H(password), table))

    print("Salted MD5:", salted_hash)
    print("Lookup:", lookup(salted_hash, table))
    print("Salt (hex):", salt_bytes.hex())


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in (
        "build", "crack", "salt"
    ):
        raise SystemExit(
            "Usage: python3 lab/rainbow/rainbow_md5.py "
            "{build|crack|salt}"
        )

    {
        "build": build,
        "crack": crack,
        "salt": salt
    }[sys.argv[1]]()
