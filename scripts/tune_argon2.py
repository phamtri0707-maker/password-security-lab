import json
import os
import platform
import secrets
from pathlib import Path
from time import perf_counter

from argon2 import PasswordHasher


ROOT_DIR = Path(__file__).resolve().parent.parent
APP_PARAMETERS = json.loads(
    (ROOT_DIR / "src" / "argon2_config.json").read_text(encoding="utf-8")
)
REPEATS = 3


def main():
    pepper = os.environ.get("PASSWORD_PEPPER")
    if not pepper:
        raise SystemExit("Set PASSWORD_PEPPER before running this script.")

    # Mật khẩu đo tạm trong RAM, không đọc hay ghi users.db.
    password = secrets.token_urlsafe(16) + pepper
    configurations = [
        {"memory_cost": 19456, "time_cost": 2, "parallelism": 1},
        {"memory_cost": 65536, "time_cost": 2, "parallelism": 1},
        {"memory_cost": 65536, "time_cost": 3, "parallelism": 1},
        {"memory_cost": 65536, "time_cost": 3, "parallelism": 4},
    ]
    if APP_PARAMETERS not in configurations:
        configurations.append(APP_PARAMETERS)

    print(f"Python {platform.python_version()} | {platform.processor()}")
    print(f"Average of {REPEATS} runs; memory_cost is in KiB (1024 KiB = 1 MiB).")
    print("memory_cost  time_cost  parallelism  hash_ms  verify_ms  app")

    for parameters in configurations:
        hasher = PasswordHasher(**parameters)
        hasher.hash(password)  # Chạy khởi động trước khi đo.
        hash_seconds = 0
        verify_seconds = 0
        for _ in range(REPEATS):
            start = perf_counter()
            password_hash = hasher.hash(password)
            hash_seconds += perf_counter() - start

            start = perf_counter()
            hasher.verify(password_hash, password)
            verify_seconds += perf_counter() - start

        hash_ms = hash_seconds * 1000 / REPEATS
        verify_ms = verify_seconds * 1000 / REPEATS
        selected = "*" if parameters == APP_PARAMETERS else ""
        print(
            f"{parameters['memory_cost']:>11}  {parameters['time_cost']:>9}  "
            f"{parameters['parallelism']:>11}  {hash_ms:>7.1f}  "
            f"{verify_ms:>9.1f}  {selected}"
        )


if __name__ == "__main__":
    main()
