
import csv
import hashlib
import random
import sys
import time
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parent

WORDLIST = BASE / "wordlist-1000.txt"
RAINBOW = BASE / "md5_table_1000.csv"
DIRECT = BASE / "md5_direct_table_1000.csv"
TARGETS = BASE / "targets_20.csv"
RESULTS = BASE / "test_results_20.csv"

CHAIN_COUNT = 100
CHAIN_LENGTH = 12
TEST_COUNT = 20


# Ham bam MD5
def md5(password):
    return hashlib.md5(
        password.encode("utf-8")
    ).hexdigest()


# Bien hash thanh ung vien trong wordlist
def reduction(hash_value, column, words):
    index = (
        int(hash_value[:8], 16) + column * 9973
    ) % len(words)

    return words[index]


# Tao mot chuoi 12 vong
def chain_end(start, words):
    password = start

    for column in range(CHAIN_LENGTH):
        hash_value = md5(password)
        password = reduction(hash_value, column, words)

    return password


# Doc wordlist 1000 mat khau
def load_words():
    words = [
        line.strip()
        for line in WORDLIST.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    if len(words) != 1000 or len(set(words)) != 1000:
        raise ValueError(
            "Wordlist must contain 1000 unique passwords"
        )

    return words


# TAO RAINBOW TABLE
def build(words):
    starts = random.Random(2026).sample(
        words, CHAIN_COUNT
    )

    begin = time.perf_counter()

    with RAINBOW.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.writer(f)
        writer.writerow(["start", "end"])

        for start in starts:
            writer.writerow([
                start,
                chain_end(start, words)
            ])

    rainbow_time = time.perf_counter() - begin

    # Tao bang hash thong thuong de so sanh
    begin = time.perf_counter()

    with DIRECT.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.writer(f)
        writer.writerow(["password", "md5_hash"])

        for password in words:
            writer.writerow([password, md5(password)])

    direct_time = time.perf_counter() - begin

    print("=== BUILD RESULTS ===")
    print("Wordlist:", len(words))
    print("Rainbow chains:", CHAIN_COUNT)
    print("Chain length:", CHAIN_LENGTH)

    print(f"Rainbow build time: {rainbow_time:.6f} s")
    print(f"Direct build time: {direct_time:.6f} s")

    print("Rainbow size:", RAINBOW.stat().st_size, "bytes")
    print("Direct size:", DIRECT.stat().st_size, "bytes")


# TIM MAT KHAU BANG RAINBOW TABLE
def lookup(target_hash, words, endpoints):

    # Thu hash muc tieu o tung vi tri co the
    for position in range(CHAIN_LENGTH - 1, -1, -1):

        current_hash = target_hash
        endpoint = None

        # Tinh den diem END
        for column in range(position, CHAIN_LENGTH):
            endpoint = reduction(
                current_hash, column, words
            )

            if column < CHAIN_LENGTH - 1:
                current_hash = md5(endpoint)

        # Tim nhung chuoi co END trung
        for start in endpoints.get(endpoint, []):

            password = start

            # Dung lai chuoi tu START
            for column in range(CHAIN_LENGTH):
                digest = md5(password)

                if digest == target_hash:
                    return password

                password = reduction(
                    digest, column, words
                )

    return None


# KIEM TRA 20 HASH MUC TIEU
def test(words):

    if not RAINBOW.exists():
        raise FileNotFoundError(
            "Run build before test"
        )

    endpoints = defaultdict(list)
    starts = set()

    with RAINBOW.open(
        newline="", encoding="utf-8"
    ) as f:
        for row in csv.DictReader(f):
            starts.add(row["start"])
            endpoints[row["end"]].append(row["start"])

    # Khong chon mat khau la START
    candidates = [
        word for word in words
        if word not in starts
    ]

    selected = random.Random(2027).sample(
        candidates, TEST_COUNT
    )

    successful = 0
    total_time = 0.0

    with (
        TARGETS.open("w", newline="", encoding="utf-8") as tf,
        RESULTS.open("w", newline="", encoding="utf-8") as rf
    ):
        tw = csv.writer(tf)
        rw = csv.writer(rf)

        tw.writerow(["case", "target_hash"])
        rw.writerow([
            "case", "actual_password",
            "found_password", "correct", "lookup_ms"
        ])

        print("=== 20 HASH TESTS ===")

        for number, actual in enumerate(selected, 1):
            target_hash = md5(actual)

            tw.writerow([number, target_hash])

            begin = time.perf_counter()
            found = lookup(target_hash, words, endpoints)
            elapsed = (
                time.perf_counter() - begin
            ) * 1000

            correct = found == actual
            successful += int(correct)
            total_time += elapsed

            rw.writerow([
                number, actual, found or "",
                correct, f"{elapsed:.3f}"
            ])

            status = "FOUND" if correct else "NOT FOUND"
            print(f"Test {number:02d}: {status}")

    print("\n=== SUMMARY ===")
    print(f"Successful: {successful}/{TEST_COUNT}")
    print(
        f"Success rate: {successful / TEST_COUNT * 100:.1f}%"
    )
    print(
        f"Average lookup time: {total_time / TEST_COUNT:.3f} ms"
    )


def main():
    words = load_words()

    if len(sys.argv) != 2:
        print("Usage: python3 md5_rainbow_1000.py build|test")
    elif sys.argv[1] == "build":
        build(words)
    elif sys.argv[1] == "test":
        test(words)
    else:
        print("Unknown command")


if __name__ == "__main__":
    main()
