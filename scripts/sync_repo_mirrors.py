#!/usr/bin/env python3
"""Sync full bare git mirrors for repositories in the source manifest."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - runtime dependency check
    raise SystemExit(
        "Missing dependency: pyyaml. Install with `pip install pyyaml`."
    ) from exc


def load_manifest(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Manifest must be a mapping: {path}")
    return data


def run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def get_ref_count(repo_dir: Path) -> int:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_dir), "for-each-ref", "--format=%(refname)"],
            text=True,
        )
    except subprocess.CalledProcessError:
        return 0
    return len([ln for ln in out.splitlines() if ln.strip()])


def sync_repo(repo: dict[str, Any], mirrors_dir: Path) -> dict[str, Any]:
    name = str(repo.get("name", "")).strip()
    url = str(repo.get("url", "")).strip()
    if not name or not url:
        return {"name": name or "<missing>", "status": "error", "error": "missing name/url"}

    target = mirrors_dir / f"{name}.git"
    result: dict[str, Any] = {
        "name": name,
        "url": url,
        "path": str(target),
        "status": "unknown",
    }

    try:
        if (target / "HEAD").exists():
            run(["git", "-C", str(target), "remote", "set-url", "origin", url])
            run(["git", "-C", str(target), "fetch", "--prune", "--tags", "origin"])
            result["status"] = "updated"
        else:
            run(["git", "clone", "--mirror", url, str(target)])
            result["status"] = "cloned"
        result["ref_count"] = get_ref_count(target)
    except subprocess.CalledProcessError as exc:
        result["status"] = "error"
        result["error"] = f"git command failed with exit code {exc.returncode}"

    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync full git mirrors for all manifest repos")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("sources/unitree_g1_sources.yaml"),
        help="Path to source manifest",
    )
    parser.add_argument(
        "--mirrors-dir",
        type=Path,
        default=Path("data/repo_mirrors"),
        help="Target directory for bare mirrors",
    )
    parser.add_argument(
        "--summary-out",
        type=Path,
        default=Path("data/snapshots"),
        help="Output directory for mirror summary",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit non-zero if any mirror sync fails",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest)

    args.mirrors_dir.mkdir(parents=True, exist_ok=True)
    args.summary_out.mkdir(parents=True, exist_ok=True)

    repos = manifest.get("repos", [])
    if not isinstance(repos, list):
        raise ValueError("manifest repos must be a list")

    results = [sync_repo(repo, args.mirrors_dir) for repo in repos]

    summary = {
        "manifest": str(args.manifest),
        "timestamp_unix": int(time.time()),
        "mirrors_dir": str(args.mirrors_dir),
        "repos": results,
    }
    out = args.summary_out / f"repo_mirror_summary_{summary['timestamp_unix']}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[OK] Wrote mirror summary: {out}")

    errors = [r for r in results if r.get("status") == "error"]
    print(f"[SUMMARY] total={len(results)} errors={len(errors)}")
    if args.fail_on_error and errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
