#!/usr/bin/env python3
"""Build a human-readable coverage report from sync and verification outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def latest_json(path: Path, pattern: str) -> Path | None:
    files = sorted(path.glob(pattern))
    if not files:
        return None
    return files[-1]


def latest_sync_with_repos(path: Path) -> Path | None:
    files = sorted(path.glob("sync_summary_*.json"))
    if not files:
        return None
    for candidate in reversed(files):
        payload = read_json(candidate)
        repos = payload.get("repos", [])
        if isinstance(repos, list) and repos:
            return candidate
    return files[-1]


def read_json(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Unitree G1 coverage report")
    parser.add_argument(
        "--snapshots-dir",
        type=Path,
        default=Path("data/snapshots"),
        help="Directory with sync/discovery snapshots",
    )
    parser.add_argument(
        "--verification-json",
        type=Path,
        default=Path("docs/verification/g1_docs_verification.json"),
        help="Verification report JSON path",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("docs/verification/coverage_report.md"),
        help="Output markdown report",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    latest_sync = latest_sync_with_repos(args.snapshots_dir)
    latest_discovery = latest_json(args.snapshots_dir, "repo_discovery_*.json")

    sync = read_json(latest_sync)
    discovery = read_json(latest_discovery)
    verification = read_json(args.verification_json)

    sync_repos = sync.get("repos", [])
    repo_errors = [r for r in sync_repos if r.get("status") == "error"]
    repo_ok = [r for r in sync_repos if r.get("status") in {"cloned", "updated"}]

    lines: list[str] = []
    lines.append("# Coverage Report")
    lines.append("")
    if latest_sync:
        lines.append(f"- Latest sync summary: `{latest_sync}`")
    if latest_discovery:
        lines.append(f"- Latest repo discovery: `{latest_discovery}`")
    lines.append("")
    lines.append("## Repo Coverage")
    lines.append("")
    lines.append(f"- Repos in latest sync: {len(sync_repos)}")
    lines.append(f"- Synced successfully: {len(repo_ok)}")
    lines.append(f"- Sync errors: {len(repo_errors)}")
    lines.append(f"- Org repos discovered: {discovery.get('all_repo_count', 0)}")
    lines.append(f"- G1-related discovery matches: {discovery.get('matched_repo_count', 0)}")
    lines.append("")

    lines.append("## G1 Docs Verification")
    lines.append("")
    lines.append(f"- Total URLs checked: {verification.get('total_urls', 0)}")
    lines.append(f"- Verified: {verification.get('verified', 0)}")
    lines.append(f"- Blocked access: {verification.get('blocked_access', 0)}")
    lines.append(f"- Needs review: {verification.get('needs_review', 0)}")
    lines.append(f"- Errors: {verification.get('errors', 0)}")
    lines.append("")

    if repo_errors:
        lines.append("## Repo Sync Errors")
        lines.append("")
        for err in repo_errors:
            lines.append(
                f"- `{err.get('name')}`: {err.get('error', 'unknown error')}"
            )
        lines.append("")

    blocked = [r for r in verification.get("results", []) if r.get("status") == "blocked_access"]
    if blocked:
        lines.append("## Blocked G1 Docs URLs")
        lines.append("")
        for item in blocked:
            lines.append(f"- {item.get('url')}")
        lines.append("")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] Wrote coverage report: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
