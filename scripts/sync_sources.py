#!/usr/bin/env python3
"""Sync Unitree source links and repositories into local storage."""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
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
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Manifest must be a mapping: {path}")
    return data


def run_command(cmd: list[str], cwd: Path | None = None) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def update_repo(repo: dict[str, Any], repos_dir: Path, depth: int | None) -> dict[str, Any]:
    name = str(repo["name"])
    url = str(repo["url"])
    branch = str(repo.get("branch", "main"))
    target = repos_dir / name

    result: dict[str, Any] = {"name": name, "url": url, "branch": branch, "path": str(target)}
    clone_cmd = ["git", "clone", "--branch", branch]
    if depth and depth > 0:
        clone_cmd.extend(["--depth", str(depth)])
    clone_cmd.extend([url, str(target)])

    try:
        if (target / ".git").exists():
            print(f"[SYNC] Updating repo: {name}")
            fetch_cmd = ["git", "-C", str(target), "fetch", "origin", branch]
            if depth and depth > 0:
                fetch_cmd.extend(["--depth", str(depth)])
            run_command(fetch_cmd)
            run_command(["git", "-C", str(target), "checkout", branch])
            run_command(["git", "-C", str(target), "pull", "--ff-only", "origin", branch])
            result["status"] = "updated"
        else:
            print(f"[SYNC] Cloning repo: {name}")
            run_command(clone_cmd)
            result["status"] = "cloned"
    except subprocess.CalledProcessError as exc:
        result["status"] = "error"
        result["error"] = f"git command failed with exit code {exc.returncode}"

    return result


def strip_html_text(raw_html: str) -> str:
    no_script = re.sub(r"(?is)<script.*?>.*?</script>", " ", raw_html)
    no_style = re.sub(r"(?is)<style.*?>.*?</style>", " ", no_script)
    no_tags = re.sub(r"(?s)<[^>]+>", " ", no_style)
    text = html.unescape(no_tags)
    return re.sub(r"\s+", " ", text).strip()


def extract_title(raw_html: str) -> str:
    match = re.search(r"(?is)<title>(.*?)</title>", raw_html)
    return re.sub(r"\s+", " ", html.unescape(match.group(1))).strip() if match else ""


def is_access_blocked(text: str, title: str) -> bool:
    hay = f"{title} {text}".lower()
    markers = [
        "restricted access",
        "blocked you from further access",
        "edgeone",
        "security policy of this website",
        "protected by tencent cloud",
    ]
    return any(marker in hay for marker in markers)


def snapshot_support_doc(doc: dict[str, Any], support_dir: Path, timeout: int) -> dict[str, Any]:
    doc_id = str(doc["id"])
    url = str(doc["url"])
    html_path = support_dir / f"{doc_id}.html"
    meta_path = support_dir / f"{doc_id}.json"

    print(f"[SYNC] Snapshot support doc: {doc_id}")
    result: dict[str, Any] = {
        "id": doc_id,
        "url": url,
        "topics": list(doc.get("topics", [])),
        "priority": doc.get("priority", "supporting"),
        "status": "unknown",
    }

    try:
        req = urlrequest.Request(url, headers={"User-Agent": "unitree-g1-doc-sync/1.0"})
        with urlrequest.urlopen(req, timeout=timeout) as response:
            payload = response.read()
        raw_html = payload.decode("utf-8", errors="replace")
        html_path.write_text(raw_html, encoding="utf-8")

        text = strip_html_text(raw_html)
        title = extract_title(raw_html)
        blocked = is_access_blocked(text, title)
        needs_browser_render = len(text) < 250

        result.update(
            {
                "status": "blocked_access" if blocked else "snapshotted",
                "title": title,
                "html_file": str(html_path),
                "text_chars": len(text),
                "needs_browser_render": needs_browser_render,
                "blocked_access": blocked,
                "snapshot_time_unix": int(time.time()),
            }
        )
        meta_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    except (urlerror.URLError, TimeoutError) as exc:
        result.update({"status": "error", "error": str(exc)})
        meta_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync Unitree source repos and docs")
    parser.add_argument(
        "--manifest",
        default="sources/unitree_g1_sources.yaml",
        type=Path,
        help="Path to source manifest",
    )
    parser.add_argument(
        "--repos-dir",
        default=Path("data/repos"),
        type=Path,
        help="Directory for cloned repositories",
    )
    parser.add_argument(
        "--support-dir",
        default=Path("data/support_pages"),
        type=Path,
        help="Directory for support page snapshots",
    )
    parser.add_argument(
        "--depth",
        default=1,
        type=int,
        help="Git clone/fetch depth. Use 0 for full history",
    )
    parser.add_argument(
        "--timeout",
        default=20,
        type=int,
        help="HTTP timeout in seconds for support pages",
    )
    parser.add_argument(
        "--skip-repos",
        action="store_true",
        help="Skip repo clone/pull",
    )
    parser.add_argument(
        "--skip-support",
        action="store_true",
        help="Skip support docs snapshot",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit non-zero when any repo/doc sync fails",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest)

    repos_dir: Path = args.repos_dir
    support_dir: Path = args.support_dir
    repos_dir.mkdir(parents=True, exist_ok=True)
    support_dir.mkdir(parents=True, exist_ok=True)

    summary: dict[str, Any] = {
        "manifest": str(args.manifest),
        "timestamp_unix": int(time.time()),
        "repos": [],
        "support_docs": [],
    }

    if not args.skip_repos:
        for repo in manifest.get("repos", []):
            summary["repos"].append(update_repo(repo, repos_dir, args.depth))
    if not args.skip_support:
        for doc in manifest.get("support_docs", []):
            summary["support_docs"].append(snapshot_support_doc(doc, support_dir, args.timeout))

    summary_path = Path("data/snapshots") / f"sync_summary_{summary['timestamp_unix']}.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[OK] Wrote sync summary: {summary_path}")
    if args.fail_on_error:
        repo_errors = [r for r in summary["repos"] if r.get("status") == "error"]
        doc_errors = [d for d in summary["support_docs"] if d.get("status") == "error"]
        doc_blocked = [d for d in summary["support_docs"] if d.get("status") == "blocked_access"]
        if repo_errors or doc_errors or doc_blocked:
            print(
                f"[ERROR] Sync completed with {len(repo_errors)} repo errors "
                f"{len(doc_errors)} support doc errors, and {len(doc_blocked)} blocked docs."
            )
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
