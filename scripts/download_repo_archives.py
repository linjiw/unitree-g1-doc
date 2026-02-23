#!/usr/bin/env python3
"""Download raw tar.gz archives for repositories in the source manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest

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


def parse_github(url: str) -> tuple[str, str] | None:
    m = re.match(r"^https://github\.com/([^/]+)/([^/]+)/?$", url.strip())
    if not m:
        return None
    return m.group(1), m.group(2)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, out: Path, timeout: int) -> None:
    req = urlrequest.Request(url, headers={"User-Agent": "unitree-g1-doc-archive-sync/1.0"})
    with urlrequest.urlopen(req, timeout=timeout) as response:
        payload = response.read()
    out.write_bytes(payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download raw tar.gz archives for manifest repos")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("sources/unitree_g1_sources.yaml"),
        help="Path to source manifest",
    )
    parser.add_argument(
        "--archives-dir",
        type=Path,
        default=Path("data/repo_archives"),
        help="Target directory for tar.gz archives",
    )
    parser.add_argument(
        "--summary-out",
        type=Path,
        default=Path("data/snapshots"),
        help="Output directory for archive summary",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="HTTP timeout in seconds",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download archives even if file already exists",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit non-zero if any archive download fails",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest)

    args.archives_dir.mkdir(parents=True, exist_ok=True)
    args.summary_out.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    repos = manifest.get("repos", [])
    if not isinstance(repos, list):
        raise ValueError("manifest repos must be a list")

    for repo in repos:
        name = str(repo.get("name", "")).strip()
        url = str(repo.get("url", "")).strip()
        branch = str(repo.get("branch", "main")).strip() or "main"
        result: dict[str, Any] = {
            "name": name,
            "url": url,
            "branch": branch,
            "status": "unknown",
        }

        parsed = parse_github(url)
        if not parsed:
            result["status"] = "skipped"
            result["reason"] = "non-github-url"
            results.append(result)
            continue

        org, repo_name = parsed
        archive_url = f"https://codeload.github.com/{org}/{repo_name}/tar.gz/refs/heads/{branch}"
        out = args.archives_dir / f"{name}-{branch}.tar.gz"

        try:
            if out.exists() and not args.force:
                result["status"] = "cached"
            else:
                download(archive_url, out, args.timeout)
                result["status"] = "downloaded"
            result["archive_url"] = archive_url
            result["file"] = str(out)
            result["bytes"] = out.stat().st_size
            result["sha256"] = sha256(out)
        except (urlerror.URLError, TimeoutError, OSError) as exc:
            result["status"] = "error"
            result["error"] = str(exc)

        results.append(result)

    summary = {
        "manifest": str(args.manifest),
        "timestamp_unix": int(time.time()),
        "archives_dir": str(args.archives_dir),
        "repos": results,
    }
    out = args.summary_out / f"repo_archive_summary_{summary['timestamp_unix']}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[OK] Wrote archive summary: {out}")

    errors = [r for r in results if r.get("status") == "error"]
    print(f"[SUMMARY] total={len(results)} errors={len(errors)}")
    if args.fail_on_error and errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
