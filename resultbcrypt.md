# Bcrypt testing results

- Sample hashes: `../../hashes/bcrypt/hashes.txt` — a synthetic dataset created by the team.
- Wordlist: `../../wordlists/lab.txt`.
- Tool: John the Ripper, using the `bcrypt` format.
- Results: The sample password `LabDemo-2026!` was recovered; John reported 1 hash cracked.
- Execution time (measured via `time`): 0.79 seconds.
- Notes: John indicated a cost factor of 4096 and utilized 4 OpenMP threads. As the wordlist contained only 6 candidates, this duration reflects a limited test run on a Kali VM.
