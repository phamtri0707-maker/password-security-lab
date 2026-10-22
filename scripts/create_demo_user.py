import json
import os
import sqlite3
from getpass import getpass
from pathlib import Path

from argon2 import PasswordHasher


ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "users.db"
ARGON2_PARAMETERS = json.loads(
    (ROOT_DIR / "src" / "argon2_config.json").read_text(encoding="utf-8")
)


def create_demo_user():
    pepper = os.environ.get("PASSWORD_PEPPER")
    if not pepper:
        raise SystemExit("Set PASSWORD_PEPPER before creating the demo user.")
    if not DB_PATH.is_file():
        raise SystemExit("Database missing. Run src/init_db.py first.")

    password = getpass("Password for demo: ")
    if not password:
        raise SystemExit("Password must not be empty.")

    # Dùng cùng cấu hình với app; thư viện tự sinh salt ngẫu nhiên.
    password_hash = PasswordHasher(**ARGON2_PARAMETERS).hash(password + pepper)

    # mode=rw chỉ mở database đã có, không tự tạo database mới.
    connection = sqlite3.connect(DB_PATH.as_uri() + "?mode=rw", uri=True)
    try:
        connection.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("demo", password_hash),
        )
        connection.commit()
    except sqlite3.IntegrityError:
        print("User 'demo' already exists. No changes made.")
    else:
        print("Created demo user: demo")
    finally:
        connection.close()


if __name__ == "__main__":
    create_demo_user()
