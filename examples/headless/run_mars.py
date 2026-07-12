"""Run a MARS JSON job and consume its JSON Lines result protocol."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path, help="Path to MARSBatch.exe")
    parser.add_argument("job", type=Path, help="Path to a MARS JSON job")
    args = parser.parse_args()

    completed = subprocess.run(
        [str(args.executable), "run", str(args.job), "--format", "json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    terminal_result = None
    for line in completed.stdout.splitlines():
        record = json.loads(line)
        if record.get("record") == "event":
            print(record["event"])
        elif record.get("record") == "result":
            terminal_result = record["result"]

    if completed.stderr:
        print(completed.stderr, end="")
    if terminal_result is not None:
        print(json.dumps(terminal_result, indent=2))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
