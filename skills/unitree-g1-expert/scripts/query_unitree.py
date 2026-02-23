#!/usr/bin/env python3
"""Skill-local wrapper for repo-level Unitree index querying."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query Unitree index from skill context")
    parser.add_argument("question", type=str, help="Question text")
    parser.add_argument("--top-k", type=int, default=5, help="Top K matches")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    query_script = repo_root / "scripts/query_index.py"
    cmd = [
        "python3",
        str(query_script),
        args.question,
        "--top-k",
        str(args.top_k),
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
