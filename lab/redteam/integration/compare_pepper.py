
import csv
import base64
import getpass
from pathlib import Path

from argon2 import PasswordHasher, extract_parameters
from argon2.exceptions import VerificationError, InvalidHashError
from argon2.low_level import hash_secret

ROOT = Path(__file__).resolve().parents[3]
HASH_FILE = Path("/tmp/ptit_lab_leaked_4.csv")
WORDLIST = ROOT / "lab/redteam/wordlists/wordlist-100.txt"

# Mat khau goc do nguoi thuc hien LAB biet.
# Chi dung de doi chieu, KHONG dung trong redteam_4.py.
KNOWN_PASSWORDS = {
    "lab01": "BlueLab#A2026",
    "lab02": "BlueLab#B2026",
    "lab03": "BlueLab#C2026",
    "lab04": "BlueLab#D2026",
}

def hash_with_original_salt(password, original_hash):
    params = extract_parameters(original_hash)

    salt_text = original_hash.split("$")[4]
    salt = base64.b64decode(
        salt_text + "=" * (-len(salt_text) % 4)
    )

    return hash_secret(
        secret=password.encode("utf-8"),
        salt=salt,
        time_cost=params.time_cost,
        memory_cost=params.memory_cost,
        parallelism=params.parallelism,
        hash_len=params.hash_len,
        type=params.type,
        version=params.version,
    ).decode("utf-8")


with HASH_FILE.open(newline="", encoding="utf-8") as f:
    targets = list(csv.DictReader(f))

words = set(
    WORDLIST.read_text(encoding="utf-8").splitlines()
)

if len(targets) != 4:
    raise SystemExit("Can du 4 hash de thuc hien doi chieu.")

print("=== ARGON2ID HASH COMPARISON ===")
print("Same salt and same Argon2id parameters")
print()

for target in targets:
    username = target["username"]
    original_hash = target["password_hash"]
    password = KNOWN_PASSWORDS[username]

    # Red Team tinh hash ma KHONG co pepper
    red_hash = hash_with_original_salt(
        password, original_hash
    )

    print("=" * 60)
    print("USER:", username)
    print("Correct password in wordlist:", password in words)

    print("\nBLUE TEAM - ORIGINAL HASH:")
    print(original_hash)

    print("\nRED TEAM - HASH WITHOUT PEPPER:")
    print(red_hash)

    print("\nHashes identical:", red_hash == original_hash)
    print()

print("=" * 60)
print("=== BLUE TEAM CONTROL TEST ===")
print("Chi nguoi quan ly Blue Team nhap pepper.")
print("Khong cung cap pepper cho Red Team.")

pepper = getpass.getpass(
    "Nhap pepper de doi chung (Enter de bo qua): "
)

if pepper:
    hasher = PasswordHasher()
    matched = 0

    for target in targets:
        username = target["username"]
        password = KNOWN_PASSWORDS[username]

        try:
            ok = hasher.verify(
                target["password_hash"],
                password + pepper
            )
        except (VerificationError, InvalidHashError):
            ok = False

        matched += int(ok)
        print(f"{username}: Blue verification = {ok}")

    print(f"\nBLUE TEAM VERIFIED: {matched}/4")
else:
    print("Skipped Blue Team control test.")
