
import os
import sqlite3
import sys
from getpass import getpass
from pathlib import Path
from time import perf_counter

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError

ROOT = Path(__file__).resolve().parents[3]

SOURCE_DB = ROOT / "users.db"
LEAKED_DB = Path.home() / "hashlab_leaked_demo.db"
WORDLIST = ROOT / "data" / "wordlist.txt"

# Chi kiem tra 4 tai khoan thu nghiem
USERS = ["studetn1", "student2", "student3", "student4"]
MAX_CANDIDATES = 104

hasher = PasswordHasher()


# Buoc 1: Gia lap ro ri hash tu Blue Team
def export_hashes():
    source = sqlite3.connect(
        SOURCE_DB.as_uri() + "?mode=ro", uri=True
    )
    try:
        placeholders = ",".join("?" for _ in USERS)
        rows = source.execute(
            f"SELECT username, password_hash FROM users "
            f"WHERE username IN ({placeholders})",
            USERS
        ).fetchall()
    finally:
        source.close()

    if len(rows) != len(USERS):
        raise SystemExit(
            f"Chi tim thay {len(rows)}/{len(USERS)} tai khoan. "
            "Kiem tra ten tai khoan."
        )

    if LEAKED_DB.exists():
        raise SystemExit(
            "File demo da ton tai. Khong ghi de database cu."
        )

    os.umask(0o077)

    with sqlite3.connect(LEAKED_DB) as db:
        db.execute(
            "CREATE TABLE users "
            "(username TEXT, password_hash TEXT)"
        )
        db.executemany(
            "INSERT INTO users VALUES (?, ?)", rows
        )

    print(f"Exported {len(rows)} demo hashes.")
    print("Saved:", LEAKED_DB)
    print("Pepper is NOT included.")


# Buoc 2: Thu Dictionary Attack
def attack(mode):
    if mode == "none":
        pepper = ""
    elif mode == "wrong":
        pepper = "wrong-demo-pepper"
    elif mode == "correct":
        pepper = getpass("Nhap Pepper dung cua Flask: ")
        if not pepper:
            raise SystemExit("Pepper khong duoc rong.")
    else:
        raise SystemExit("Mode khong hop le.")

    candidates = WORDLIST.read_text(
        encoding="utf-8"
    ).splitlines()[:MAX_CANDIDATES]

    db = sqlite3.connect(
        LEAKED_DB.as_uri() + "?mode=ro", uri=True
    )
    try:
        users = db.execute(
            "SELECT username, password_hash FROM users"
        ).fetchall()
    finally:
        db.close()

    recovered = 0
    start = perf_counter()

    for username, stored_hash in users:
        found = False

        for password in candidates:
            try:
                if hasher.verify(
                    stored_hash, password + pepper
                ):
                    found = True
                    break
            except (VerificationError, InvalidHashError):
                pass

        print(
            f"{username}: "
            f"{'FOUND' if found else 'NOT FOUND'}",
            flush=True
        )
        recovered += found

    elapsed = perf_counter() - start

    print(f"Mode: {mode}")
    print(f"Wordlist: {len(candidates)} candidates")
    print(f"RESULT: {recovered}/{len(users)} recovered")
    print(f"Elapsed: {elapsed:.2f} seconds")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python3 crack_db.py export|none|wrong|correct"
        )

    if sys.argv[1] == "export":
        export_hashes()
    else:
        attack(sys.argv[1])
