"""Offline checks for the synthetic Group 7 dataset and its lab hashes."""

import csv
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import bcrypt
from argon2 import PasswordHasher, extract_parameters
from argon2.exceptions import VerifyMismatchError
from argon2.low_level import Type

from scripts import generate_dataset, generate_hashes


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DATASET_FILES = ("wordlist.txt", "targets.txt", "targets_metadata.csv")
ALGORITHMS = ("md5", "bcrypt", "argon2id")


def read_lf_lines(path):
    """Read artifacts without silently accepting a BOM or CRLF conversion."""
    content = path.read_bytes()
    if content.startswith(b"\xef\xbb\xbf") or b"\r" in content:
        raise AssertionError(f"Expected UTF-8 without BOM and LF endings: {path}")
    if not content.endswith(b"\n"):
        raise AssertionError(f"Expected a final LF: {path}")
    return content.decode("utf-8").splitlines()


class DatasetTests(unittest.TestCase):
    def test_dataset_is_deterministic_and_matches_shipped_files(self):
        self.assertEqual(generate_dataset.SEED, 7007)
        first = generate_dataset.build_dataset()
        self.assertEqual(first, generate_dataset.build_dataset())
        wordlist, targets, metadata = first
        self.assertEqual(len(wordlist), 1000)
        self.assertEqual(len(set(wordlist)), 1000)
        self.assertTrue(all(password and password.isascii() for password in wordlist))
        self.assertTrue(all("\n" not in password and "\r" not in password
                            and "\x00" not in password for password in wordlist))
        self.assertEqual(generate_dataset.GROUP_SIZES,
                         {"easy": 400, "medium": 350, "harder": 250})
        self.assertEqual(sum(generate_dataset.GROUP_SIZES.values()), len(wordlist))

        self.assertEqual(read_lf_lines(DATA_DIR / "wordlist.txt"), wordlist)
        self.assertEqual(read_lf_lines(DATA_DIR / "targets.txt"), targets)
        read_lf_lines(DATA_DIR / "targets_metadata.csv")
        with (DATA_DIR / "targets_metadata.csv").open(
            encoding="utf-8", newline=""
        ) as stream:
            stored_metadata = list(csv.DictReader(stream))
        normalized_metadata = [
            {key: str(value) for key, value in row.items()} for row in metadata
        ]
        self.assertEqual(stored_metadata, normalized_metadata)

    def test_target_positions_and_metadata(self):
        wordlist, targets, metadata = generate_dataset.build_dataset()
        self.assertEqual(len(targets), 3)
        self.assertEqual(len(set(targets)), 3)
        self.assertEqual(targets[:2], [wordlist[24], wordlist[649]])
        self.assertEqual(len(targets[2]), 20)
        self.assertTrue(targets[2].isascii())
        self.assertNotIn(targets[2], wordlist)
        expected = [
            {"target_id": "target_1", "target_line": "1",
             "difficulty": "easy", "wordlist_line": "25"},
            {"target_id": "target_2", "target_line": "2",
             "difficulty": "medium", "wordlist_line": "650"},
            {"target_id": "target_3", "target_line": "3",
             "difficulty": "harder", "wordlist_line": ""},
        ]
        self.assertEqual(
            [{key: str(value) for key, value in row.items()} for row in metadata],
            expected,
        )

    def test_dataset_writer_reproduces_exact_files(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "data"
            generate_dataset.write_dataset(destination)
            first = {name: (destination / name).read_bytes() for name in DATASET_FILES}
            generate_dataset.write_dataset(destination)
            for name, content in first.items():
                with self.subTest(file=name):
                    self.assertEqual((destination / name).read_bytes(), content)
                    self.assertEqual((DATA_DIR / name).read_bytes(), content)
                    read_lf_lines(destination / name)


class HashArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary_directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temporary_directory.cleanup)
        isolated_root = Path(temporary_directory.name)
        scripts_dir = isolated_root / "scripts"
        scripts_dir.mkdir()
        unrelated_cwd = isolated_root / "unrelated-working-directory"
        unrelated_cwd.mkdir()
        cls.generated_data = isolated_root / "data"
        environment = dict(os.environ, PYTHONIOENCODING="utf-8")
        for name in ("generate_dataset.py", "generate_hashes.py"):
            shutil.copyfile(ROOT_DIR / "scripts" / name, scripts_dir / name)

        def run_script(name):
            result = subprocess.run(
                [sys.executable, "-B", str(scripts_dir / name)],
                cwd=unrelated_cwd,
                env=environment,
                capture_output=True,
                encoding="utf-8",
                timeout=60,
            )
            if result.returncode:
                raise AssertionError(
                    f"{name} failed ({result.returncode}):\n{result.stderr}"
                )

        run_script("generate_dataset.py")
        run_script("generate_hashes.py")
        cls.first_hashes = {
            algorithm: read_lf_lines(cls.generated_data / "hashes" / f"{algorithm}.txt")
            for algorithm in ALGORITHMS
        }
        run_script("generate_hashes.py")
        cls.second_hashes = {
            algorithm: read_lf_lines(cls.generated_data / "hashes" / f"{algorithm}.txt")
            for algorithm in ALGORITHMS
        }

    def assert_hashes_match(self, targets, hashes):
        self.assertEqual(set(hashes), set(ALGORITHMS))
        hasher = PasswordHasher()
        for algorithm, values in hashes.items():
            self.assertEqual(len(values), 3)
            for password, encoded in zip(targets, values):
                with self.subTest(algorithm=algorithm, target_line=targets.index(password) + 1):
                    password_bytes = password.encode("utf-8")
                    if algorithm == "md5":
                        self.assertRegex(encoded, r"^[0-9a-f]{32}$")
                        self.assertEqual(encoded, hashlib.md5(password_bytes).hexdigest())
                        self.assertNotEqual(
                            encoded, hashlib.md5((password + "!").encode("utf-8")).hexdigest()
                        )
                    elif algorithm == "bcrypt":
                        self.assertRegex(encoded, r"^\$2[aby]\$10\$[./A-Za-z0-9]{53}$")
                        self.assertTrue(bcrypt.checkpw(password_bytes, encoded.encode("ascii")))
                        self.assertFalse(bcrypt.checkpw(
                            (password + "!").encode("utf-8"), encoded.encode("ascii")
                        ))
                    else:
                        self.assertTrue(encoded.startswith("$argon2id$v=19$"))
                        parameters = extract_parameters(encoded)
                        self.assertEqual(parameters.type, Type.ID)
                        self.assertEqual(parameters.time_cost, 3)
                        self.assertEqual(parameters.memory_cost, 65536)
                        self.assertEqual(parameters.parallelism, 1)
                        self.assertEqual(parameters.hash_len, 32)
                        self.assertEqual(parameters.salt_len, 16)
                        self.assertTrue(hasher.verify(encoded, password))
                        with self.assertRaises(VerifyMismatchError):
                            hasher.verify(encoded, password + "!")
        self.assertEqual(len({value[:29] for value in hashes["bcrypt"]}), 3)
        self.assertEqual(len({value.split("$")[4] for value in hashes["argon2id"]}), 3)

    def test_shipped_hashes_verify_in_target_order(self):
        targets = read_lf_lines(DATA_DIR / "targets.txt")
        hashes = {
            algorithm: read_lf_lines(DATA_DIR / "hashes" / f"{algorithm}.txt")
            for algorithm in ALGORITHMS
        }
        self.assert_hashes_match(targets, hashes)

    def test_scripts_work_outside_repository_and_produce_valid_hashes(self):
        for name in DATASET_FILES:
            with self.subTest(file=name):
                self.assertEqual(
                    (self.generated_data / name).read_bytes(), (DATA_DIR / name).read_bytes()
                )
        self.assert_hashes_match(
            read_lf_lines(self.generated_data / "targets.txt"), self.first_hashes
        )

    def test_rerun_preserves_md5_and_renews_salted_hashes(self):
        self.assertEqual(self.first_hashes["md5"], self.second_hashes["md5"])
        for algorithm in ("bcrypt", "argon2id"):
            for first, second in zip(self.first_hashes[algorithm], self.second_hashes[algorithm]):
                with self.subTest(algorithm=algorithm):
                    self.assertNotEqual(first, second)
                    if algorithm == "bcrypt":
                        self.assertNotEqual(first[:29], second[:29])
                    else:
                        self.assertNotEqual(first.split("$")[4], second.split("$")[4])


class TargetInputTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.target_path = Path(temporary_directory.name) / "targets.txt"

    def write_targets(self, values):
        self.target_path.write_bytes(("\n".join(values) + "\n").encode("utf-8"))

    def test_reader_preserves_password_spaces_and_accepts_72_utf8_bytes(self):
        targets = [" with spaces ", "\u00e9" * 36, "third-target"]
        self.write_targets(targets)
        self.assertEqual(generate_hashes.read_targets(self.target_path), targets)

    def test_reader_rejects_invalid_inputs(self):
        invalid_cases = {
            "empty_file": [],
            "too_few": ["first", "second"],
            "too_many": ["first", "second", "third", "fourth"],
            "duplicate": ["first", "first", "third"],
            "blank": ["first", "", "third"],
            "whitespace_only": ["first", " \t ", "third"],
            "nul": ["first", "second\x00", "third"],
            "73_ascii_bytes": ["first", "a" * 73, "third"],
            "74_utf8_bytes": ["first", "\u00e9" * 37, "third"],
        }
        for label, targets in invalid_cases.items():
            with self.subTest(case=label):
                self.write_targets(targets)
                with self.assertRaises(ValueError):
                    generate_hashes.read_targets(self.target_path)


if __name__ == "__main__":
    unittest.main()
