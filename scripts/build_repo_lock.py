#!/usr/bin/env python3
"""Build a lockfile/report for synced Unitree repositories."""

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


def git_output(cmd: list[str]) -> str:
    out = subprocess.check_output(cmd, text=True)
    return out.strip()


def optional_git_output(cmd: list[str]) -> str:
    try:
        return git_output(cmd)
    except Exception:
        return ""


def collect_repo(repo: dict[str, Any], repos_dir: Path, mirrors_dir: Path) -> dict[str, Any]:
    name = str(repo.get("name", "")).strip()
    branch = str(repo.get("branch", "main")).strip() or "main"
    url = str(repo.get("url", "")).strip()

    worktree = repos_dir / name
    mirror = mirrors_dir / f"{name}.git"

    payload: dict[str, Any] = {
        "name": name,
        "url": url,
        "branch": branch,
        "worktree_path": str(worktree),
        "mirror_path": str(mirror),
        "worktree_present": (worktree / ".git").exists(),
        "mirror_present": (mirror / "HEAD").exists(),
    }

    if payload["worktree_present"]:
        payload["head_commit"] = optional_git_output(["git", "-C", str(worktree), "rev-parse", "HEAD"])
        payload["head_commit_time"] = optional_git_output(
            ["git", "-C", str(worktree), "show", "-s", "--format=%cI", "HEAD"]
        )
        payload["remote_origin"] = optional_git_output(
            ["git", "-C", str(worktree), "remote", "get-url", "origin"]
        )
        tags = optional_git_output(["git", "-C", str(worktree), "tag", "--list"])
        payload["tag_count"] = len([ln for ln in tags.splitlines() if ln.strip()])

    if payload["mirror_present"]:
        ref_lines = optional_git_output(["git", "-C", str(mirror), "for-each-ref", "--format=%(refname)"])
        payload["mirror_ref_count"] = len([ln for ln in ref_lines.splitlines() if ln.strip()])

    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build lock/report for synced Unitree repositories")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("sources/unitree_g1_sources.yaml"),
        help="Path to source manifest",
    )
    parser.add_argument(
        "--repos-dir",
        type=Path,
        default=Path("data/repos"),
        help="Directory with working clones",
    )
    parser.add_argument(
        "--mirrors-dir",
        type=Path,
        default=Path("data/repo_mirrors"),
        help="Directory with bare mirrors",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path("docs/verification/repo_lock.json"),
        help="Output JSON lock path",
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=Path("docs/verification/repo_lock.md"),
        help="Output Markdown report path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest)

    repos = manifest.get("repos", [])
    if not isinstance(repos, list):
        raise ValueError("manifest repos must be a list")

    entries = [collect_repo(repo, args.repos_dir, args.mirrors_dir) for repo in repos]

    report = {
        "manifest": str(args.manifest),
        "timestamp_unix": int(time.time()),
        "repos": entries,
        "summary": {
            "total": len(entries),
            "worktree_present": len([e for e in entries if e.get("worktree_present")]),
            "mirror_present": len([e for e in entries if e.get("mirror_present")]),
        },
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines: list[str] = []
    lines.append("# Repo Lock Report")
    lines.append("")
    lines.append(f"- Total repos in manifest: {report['summary']['total']}")
    lines.append(f"- Working clones present: {report['summary']['worktree_present']}")
    lines.append(f"- Bare mirrors present: {report['summary']['mirror_present']}")
    lines.append("")
    lines.append("| Repo | Branch | Worktree | Mirror | HEAD |")
    lines.append("| --- | --- | --- | --- | --- |")
    for entry in entries:
        lines.append(
            f"| {entry.get('name','')} | {entry.get('branch','')} | "
            f"{entry.get('worktree_present', False)} | {entry.get('mirror_present', False)} | "
            f"{entry.get('head_commit','')} |"
        )

    args.md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] Wrote repo lock JSON: {args.json_out}")
    print(f"[OK] Wrote repo lock MD: {args.md_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
