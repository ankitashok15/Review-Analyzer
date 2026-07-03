#!/usr/bin/env python3
"""Convenience wrapper to ingest the Phase 1 Spotify reviews dataset."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "phases" / "phase-1" / "data" / "spotify_reviews.csv"


def main() -> int:
    if not DATA_FILE.exists():
        print(f"Dataset not found: {DATA_FILE}")
        return 1

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_pipeline.py"),
        "ingest",
        "--source",
        "csv",
        "--file",
        str(DATA_FILE),
    ]
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
