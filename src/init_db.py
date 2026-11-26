import sqlite3
from pathlib import Path


# Luôn đặt users.db ở thư mục gốc của project.
DB_PATH = Path(__file__).resolve().parent.parent / "users.db"


def init_db():
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
            """
        )
        connection.commit()
    finally:
        connection.close()

    print(f"Database: {DB_PATH}")


if __name__ == "__main__":
    init_db()
