
import csv
from pathlib import Path
from md5_rainbow_1000 import md5, load_words, lookup
from collections import defaultdict

BASE = Path(__file__).resolve().parent

# Doc rainbow table da tao truoc do
endpoints = defaultdict(list)

with (BASE / "md5_table_1000.csv").open(
    newline="", encoding="utf-8"
) as f:
    for row in csv.DictReader(f):
        endpoints[row["end"]].append(row["start"])

words = load_words()

# Chon mot mat khau ma rainbow table da tim duoc
password = None

with (BASE / "test_results_20.csv").open(
    newline="", encoding="utf-8"
) as f:
    for row in csv.DictReader(f):
        if row["correct"] == "True":
            password = row["actual_password"]
            break

if password is None:
    raise RuntimeError("No successful test case found")

print("Password selected:", password)

# TRUONG HOP A: KHONG SALT
hash_normal = md5(password)
result_normal = lookup(hash_normal, words, endpoints)

print("\n=== MD5 WITHOUT SALT ===")
print("Hash:", hash_normal)
print("Found:", result_normal)
print("Success:", result_normal == password)

# TRUONG HOP B: CO SALT
salt_a = "lab_salt_A:"
salt_b = "lab_salt_B:"

hash_salted_a = md5(salt_a + password)
hash_salted_b = md5(salt_b + password)

result_salted = lookup(hash_salted_a, words, endpoints)

print("\n=== MD5 WITH SALT ===")
print("Salt A:", salt_a)
print("Hash A:", hash_salted_a)
print("Salt B:", salt_b)
print("Hash B:", hash_salted_b)
print("Hashes different:", hash_salted_a != hash_salted_b)
print("Old rainbow table found:", result_salted)
print("Old table success:", result_salted == password)

# Salt la cong khai: van co the thu tung ung vien
recovered = next(
    (p for p in words if md5(salt_a + p) == hash_salted_a),
    None
)

print("\n=== KNOWN SALT + WORDLIST ===")
print("Recovered:", recovered)
print("Success:", recovered == password)
