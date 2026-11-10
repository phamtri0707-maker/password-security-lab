"""Hash three synthetic targets; no database, Blue Team config, or pepper."""

import hashlib
from pathlib import Path

import bcrypt
from argon2 import PasswordHasher
from argon2.low_level import Type


ROOT_DIR = Path(__file__).resolve().parent.parent
BCRYPT_ROUNDS = 10
ARGON2_PARAMETERS = {
    "time_cost": 3,
    "memory_cost": 65536,  # KiB = 64 MiB per hash, also with parallelism=1.
    "parallelism": 1,
    "hash_len": 32,
    "salt_len": 16,
}


def validate_targets(targets):
    if len(targets) != 3 or len(set(targets)) != 3:
        raise ValueError("targets.txt must contain exactly 3 distinct passwords.")
    for line, password in enumerate(targets, start=1):
        if not password.strip() or "\x00" in password or "\ufeff" in password:
            raise ValueError(f"Target line {line}: blank, NUL, or BOM is not allowed.")
        if len(password.encode("utf-8")) > 72:
            raise ValueError(f"Target line {line}: bcrypt supports at most 72 UTF-8 bytes.")


def read_targets(path):
    targets = Path(path).read_text(encoding="utf-8").splitlines()
    validate_targets(targets)
    return targets


def generate_hashes(targets):
    validate_targets(targets)
    hasher = PasswordHasher(type=Type.ID, **ARGON2_PARAMETERS)
    hashes = {"md5": [], "bcrypt": [], "argon2id": []}
    for password in targets:
        encoded = password.encode("utf-8")
        # Unsalted MD5 is deliberately insecure: demonstration only.
        hashes["md5"].append(hashlib.md5(encoded, usedforsecurity=False).hexdigest())
        hashes["bcrypt"].append(
            bcrypt.hashpw(encoded, bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("ascii")
        )
        # No salt argument: argon2-cffi creates a fresh random salt internally.
        hashes["argon2id"].append(hasher.hash(password))
    return hashes


def write_hashes(data_dir):
    data_dir = Path(data_dir)
    # Validate and generate all nine hashes before replacing any output file.
    hashes = generate_hashes(read_targets(data_dir / "targets.txt"))
    hashes_dir = data_dir / "hashes"
    hashes_dir.mkdir(parents=True, exist_ok=True)
    for algorithm, lines in hashes.items():
        (hashes_dir / f"{algorithm}.txt").write_text(
            "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
        )


def main():
    try:
        write_hashes(ROOT_DIR / "data")
    except (OSError, ValueError) as error:
        raise SystemExit(f"Cannot generate hashes: {error}") from error
    print("Created 9 hashes: data/hashes/{md5,bcrypt,argon2id}.txt (3 lines each).")
    print(f"bcrypt: rounds={BCRYPT_ROUNDS}; Argon2id: {ARGON2_PARAMETERS}")
    print("Hash line n belongs to targets.txt line n. Salted hashes change on rerun.")


if __name__ == "__main__":
    main()
