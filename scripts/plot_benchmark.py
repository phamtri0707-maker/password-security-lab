import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Lưu ảnh ra file, không mở cửa sổ biểu đồ.
import matplotlib.pyplot as plt


results_dir = Path(__file__).resolve().parent.parent / "lab" / "results"

bcrypt_costs = []
bcrypt_times = []
argon2_labels = []
argon2_times = []

with (results_dir / "benchmark_summary.csv").open(encoding="utf-8", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        if row["algorithm"] == "bcrypt":
            bcrypt_costs.append(int(row["bcrypt_cost"]))
            bcrypt_times.append(float(row["median_ms"]))
        elif row["algorithm"] == "Argon2id":
            argon2_labels.append(f"{row['memory_mib']} MiB\nt={row['time_cost']}")
            argon2_times.append(float(row["median_ms"]))

# Hai biểu đồ riêng vì cost bcrypt và tham số Argon2id khác đơn vị.
fig, axes = plt.subplots(1, 2, figsize=(10, 4))

axes[0].plot(bcrypt_costs, bcrypt_times, marker="o")
axes[0].set_title("bcrypt")
axes[0].set_xlabel("Cost")
axes[0].set_xticks(bcrypt_costs)
axes[0].set_ylabel("Thời gian băm (ms/hash)")
axes[0].set_ylim(bottom=0)
axes[0].grid(alpha=0.3)

axes[1].plot(argon2_labels, argon2_times, marker="o", color="tab:orange")
axes[1].set_title("Argon2id (p=1)")
axes[1].set_xlabel("Cấu hình bộ nhớ và số lượt")
axes[1].set_ylabel("Thời gian băm (ms/hash)")
axes[1].set_ylim(bottom=0)
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig(results_dir / "cost_trends.png", dpi=150)
plt.close(fig)
print("Da luu bieu do:", results_dir / "cost_trends.png")
