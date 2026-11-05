
import csv
import os
import sqlite3
from pathlib import Path

# Thu muc goc repository
ROOT = Path(__file__).resolve().parents[3]

# Database cua Blue Team
DATABASE = ROOT / "users.db"

# File hash gia lap bi lo cho Red Team
OUTPUT = Path("/tmp/ptit_lab_leaked_4.csv")

# Bon tai khoan thu nghiem
USERS = ("lab01", "lab02", "lab03", "lab04")

# Kiem tra database
if not DATABASE.is_file():
    raise SystemExit(f"Khong tim thay database: {DATABASE}")

# Chi doc database, khong sua du lieu
with sqlite3.connect(
    f"file:{DATABASE}?mode=ro", uri=True
) as conn:
    rows = conn.execute(
        """
        SELECT username, password_hash
        FROM users
        WHERE username IN (?, ?, ?, ?)
        ORDER BY username
        """,
        USERS
    ).fetchall()

# Dam bao du 4 tai khoan
if len(rows) != 4:
    raise SystemExit(
        f"Chi tim thay {len(rows)}/4 tai khoan!"
    )

# Gioi han quyen truy cap file moi
os.umask(0o077)

# Xuat 4 hash sang file CSV
with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["username", "password_hash"])
    writer.writerows(rows)

OUTPUT.chmod(0o600)

print("=== EXPORT LEAKED HASHES ===")
print("Database:", DATABASE)
print("Output:", OUTPUT)
print("Total hashes:", len(rows))

for username, _ in rows:
    print("Exported:", username)

print("Export successful!")
