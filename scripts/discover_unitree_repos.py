#!/usr/bin/env python3
"""Discover Unitree organization repos relevant to G1 and optionally update manifest."""

from __future__ import annotations

import argparse
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


DEFAULT_KEYWORDS = [
    "g1",
    "humanoid",
    "sdk",
    "rl",
    "ros",
    "sim",
    "isaac",
    "mujoco",
    "dds",
]


def fetch_json(url: str) -> Any:
    req = urlrequest.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "unitree-g1-doc-repo-discovery/1.0",
        },
    )
    with urlrequest.urlopen(req, timeout=30) as response:
        payload = response.read()
    return json.loads(payload.decode("utf-8", errors="replace"))


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Manifest must be a mapping: {path}")
    return data


def infer_topics(name: str, description: str) -> list[str]:
    text = f"{name} {description}".lower()
    topics: list[str] = []
    mapping = {
        "sdk": "sdk",
        "ros": "ros",
        "rl": "rl",
        "sim": "simulation",
        "isaac": "isaaclab",
        "mujoco": "mujoco",
        "dds": "dds",
        "g1": "g1",
        "humanoid": "humanoid",
    }
    for key, topic in mapping.items():
        if key in text and topic not in topics:
            topics.append(topic)
    return topics or ["unitree"]


def repo_matches(repo: dict[str, Any], keywords: list[str]) -> bool:
    text = f"{repo.get('name', '')} {repo.get('description') or ''}".lower()
    return any(kw in text for kw in keywords)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover Unitree repos relevant to G1")
    parser.add_argument("--org", default="unitreerobotics", help="GitHub organization name")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("sources/unitree_g1_sources.yaml"),
        help="Path to source manifest",
    )
    parser.add_argument(
        "--keywords",
        default=",".join(DEFAULT_KEYWORDS),
        help="Comma-separated keywords for relevance filtering",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Maximum GitHub API pages (100 repos per page)",
    )
    parser.add_argument(
        "--snapshot-out",
        type=Path,
        default=Path("data/snapshots"),
        help="Output directory for discovery snapshot",
    )
    parser.add_argument(
        "--update-manifest",
        action="store_true",
        help="Merge discovered repos into source manifest",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    keywords = [k.strip().lower() for k in args.keywords.split(",") if k.strip()]

    discovered: list[dict[str, Any]] = []
    all_repos: list[dict[str, Any]] = []

    for page in range(1, args.max_pages + 1):
        url = f"https://api.github.com/orgs/{args.org}/repos?per_page=100&page={page}"
        try:
            data = fetch_json(url)
        except urlerror.URLError as exc:
            print(f"[ERROR] Failed to fetch page {page}: {exc}")
            break

        if not isinstance(data, list) or not data:
            break

        all_repos.extend(data)
        for repo in data:
            if not repo_matches(repo, keywords):
                continue
            name = str(repo.get("name", "")).strip()
            if not name:
                continue
            description = str(repo.get("description") or "")
            discovered.append(
                {
                    "name": name,
                    "url": str(repo.get("html_url", "")),
                    "branch": str(repo.get("default_branch", "main")),
                    "topics": infer_topics(name, description),
                    "priority": "core" if "g1" in name.lower() else "supporting",
                    "description": description,
                    "archived": bool(repo.get("archived", False)),
                }
            )

    dedup: dict[str, dict[str, Any]] = {}
    for repo in discovered:
        dedup[repo["name"]] = repo
    discovered_sorted = sorted(dedup.values(), key=lambda x: x["name"].lower())

    snapshot = {
        "org": args.org,
        "timestamp_unix": int(time.time()),
        "keywords": keywords,
        "all_repo_count": len(all_repos),
        "matched_repo_count": len(discovered_sorted),
        "matched_repos": discovered_sorted,
    }

    args.snapshot_out.mkdir(parents=True, exist_ok=True)
    out_path = args.snapshot_out / f"repo_discovery_{snapshot['timestamp_unix']}.json"
    out_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"[OK] Wrote discovery snapshot: {out_path}")

    if args.update_manifest:
        manifest_data = load_manifest(args.manifest)
        existing = {
            str(repo.get("name", "")).strip(): repo
            for repo in manifest_data.get("repos", [])
            if str(repo.get("name", "")).strip()
        }

        merged = dict(existing)
        for repo in discovered_sorted:
            if repo["name"] in merged:
                continue
            merged[repo["name"]] = {
                "name": repo["name"],
                "url": repo["url"],
                "branch": repo["branch"],
                "topics": repo["topics"],
                "priority": repo["priority"],
            }

        manifest_data["repos"] = [merged[k] for k in sorted(merged.keys(), key=str.lower)]
        args.manifest.write_text(
            yaml.safe_dump(manifest_data, sort_keys=False),
            encoding="utf-8",
        )
        print(
            f"[OK] Updated manifest repos: {len(existing)} -> {len(manifest_data['repos'])} "
            f"({len(manifest_data['repos']) - len(existing)} added)"
        )

    print(f"[INFO] Total repos seen: {len(all_repos)}")
    print(f"[INFO] G1-related matches: {len(discovered_sorted)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
