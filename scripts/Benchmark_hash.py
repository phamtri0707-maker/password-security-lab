import hashlib
import time
import statistics
import bcrypt
from argon2 import PasswordHasher
from argon2.low_level import Type

import csv
from pathlib import Path


PASSWORD_DEMO_BENCHMARK = "hello123"
password_byte = PASSWORD_DEMO_BENCHMARK.encode("utf-8")
results = []


# MD5: giữ 5 đợt, mỗi đợt 10.000 lần băm như code gốc.
# MD5 chỉ để minh họa, không phù hợp để lưu mật khẩu.
hashlib.md5(password_byte).digest()  # Warm-up một lần, không tính thời gian.
result_md5 = []

for i in range(5):
    start = time.perf_counter()

    for j in range(10000):
        password_hash = hashlib.md5(password_byte).digest()

    end = time.perf_counter()
    ans = (end - start) * 1000 / 10000
    result_md5.append(ans)

median_time_md5 = statistics.median(result_md5)
print("MD5 hash time: ", median_time_md5, " ms/hash", sep="")
results.append(["MD5", "", "", "", "", median_time_md5, "ms/hash", 5, 10000])


# BCRYPT
# Tính cả sinh salt trong mỗi lần đo, giống cách Argon2id tự sinh salt.
for cost in [10, 11, 12]:
    result_bcrypt = []
    bcrypt.hashpw(password_byte, bcrypt.gensalt(rounds=cost))  # Warm-up.

    for i in range(5):
        start = time.perf_counter()

        salt = bcrypt.gensalt(rounds=cost)
        hashed = bcrypt.hashpw(password_byte, salt)

        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000
        result_bcrypt.append(elapsed_ms)

    median_time_bcrypt = statistics.median(result_bcrypt)
    print(f"Bcrypt hash time with cost {cost}: {median_time_bcrypt} ms/hash")
    results.append(["bcrypt", cost, "", "", "", median_time_bcrypt, "ms/hash", 5, 1])


# ARGON2ID
config = [
    (32768, 3),
    (65536, 3),
    (65536, 4),
]

for memory_cost, time_cost in config:
    ph = PasswordHasher(
        time_cost=time_cost,
        memory_cost=memory_cost,
        parallelism=1,
        type=Type.ID,
    )
    result_argon2 = []
    ph.hash(password_byte)  # Warm-up; thư viện tự sinh salt.

    for i in range(5):
        start = time.perf_counter()

        hashed = ph.hash(password_byte)

        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000
        result_argon2.append(elapsed_ms)

    median_time_argon2 = statistics.median(result_argon2)
    print(f"Argon2id m={memory_cost // 1024} MiB, t={time_cost}, p=1: "
          f"{median_time_argon2} ms/hash")
    results.append(["Argon2id", "", memory_cost // 1024, time_cost, 1,
                    median_time_argon2, "ms/hash", 5, 1])


# Ghi 7 kết quả tổng hợp sau khi đo xong; chạy lại sẽ cập nhật CSV này.
results_dir = Path(__file__).resolve().parent.parent / "lab" / "results"
results_dir.mkdir(parents=True, exist_ok=True)
csv_path = results_dir / "benchmark_summary.csv"

with csv_path.open("w", encoding="utf-8", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["algorithm", "bcrypt_cost", "memory_mib", "time_cost",
                     "parallelism", "median_ms", "unit", "measurements",
                     "hashes_per_measurement"])
    writer.writerows(results)

print("Da luu ket qua:", csv_path)












