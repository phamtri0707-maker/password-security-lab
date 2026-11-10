"""Create reproducible, entirely synthetic inputs for the stage 1 hash lab."""

import csv
import random
import string
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
SEED = 7007
GROUP_SIZES = {"easy": 400, "medium": 350, "harder": 250}
WORDS = (
    "moon", "sun", "star", "cloud", "rain", "wind", "river", "ocean",
    "stone", "leaf", "tree", "moss", "fern", "reed", "rose", "iris",
    "cedar", "maple", "coral", "amber",
)
SYMBOLS = "!@#$%&*?"


def random_candidate(rng, length):
    # Fixed seed is for reproducible exercises, not real password generation.
    characters = [
        rng.choice(string.ascii_lowercase), rng.choice(string.ascii_uppercase),
        rng.choice(string.digits), rng.choice(SYMBOLS),
    ]
    alphabet = string.ascii_letters + string.digits + SYMBOLS
    characters.extend(rng.choice(alphabet) for _ in range(length - 4))
    rng.shuffle(characters)
    return "".join(characters)


def build_dataset():
    rng = random.Random(SEED)
    # Easy candidates follow one small, predictable lab-themed template.
    wordlist = [f"lab{word}{number:02d}" for word in WORDS for number in range(20)]
    rng.shuffle(wordlist)
    seen = set(wordlist)

    for difficulty in ("medium", "harder"):
        added = 0
        while added < GROUP_SIZES[difficulty]:
            if difficulty == "medium":
                candidate = (
                    rng.choice(WORDS).capitalize() + rng.choice(WORDS).capitalize()
                    + f"{rng.randrange(10000):04d}" + rng.choice(SYMBOLS)
                )
            else:
                candidate = random_candidate(rng, 18)
            if candidate not in seen:
                seen.add(candidate)
                wordlist.append(candidate)
                added += 1

    absent_target = random_candidate(rng, 20)
    while absent_target in seen:
        absent_target = random_candidate(rng, 20)
    targets = [wordlist[24], wordlist[649], absent_target]
    metadata = [
        {"target_id": "target_1", "target_line": 1,
         "difficulty": "easy", "wordlist_line": 25},
        {"target_id": "target_2", "target_line": 2,
         "difficulty": "medium", "wordlist_line": 650},
        {"target_id": "target_3", "target_line": 3,
         "difficulty": "harder", "wordlist_line": ""},
    ]
    return wordlist, targets, metadata


def write_dataset(data_dir):
    data_dir = Path(data_dir)
    wordlist, targets, metadata = build_dataset()
    data_dir.mkdir(parents=True, exist_ok=True)
    for filename, passwords in (("wordlist.txt", wordlist), ("targets.txt", targets)):
        (data_dir / filename).write_text(
            "\n".join(passwords) + "\n", encoding="utf-8", newline="\n"
        )
    with (data_dir / "targets_metadata.csv").open(
        "w", encoding="utf-8", newline=""
    ) as output:
        writer = csv.DictWriter(
            output,
            fieldnames=["target_id", "target_line", "difficulty", "wordlist_line"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(metadata)


def main():
    write_dataset(ROOT_DIR / "data")
    print(f"Created 1000 unique synthetic candidates and 3 targets (seed={SEED}).")
    print("Wordlist positions (1-based): target_1=25, target_2=650, target_3=absent.")
    print("Next: python scripts/generate_hashes.py (refresh hashes after inputs change).")


if __name__ == "__main__":
    main()
