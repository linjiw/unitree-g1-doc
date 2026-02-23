#!/usr/bin/env python3
"""Discover Unitree organization repositories and optionally update manifest."""

from __future__ import annotations

import argparse
import json
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

CORE_REPO_HINTS = {
    "unitree_sdk2",
    "unitree_sdk2_python",
    "unitree_rl_lab",
    "unitree_rl_gym",
    "unitree_ros2",
    "unitree_ros",
    "unitree_mujoco",
    "unitree_sim_isaaclab",
    "unitree_rl_mjlab",
    "unitree_ros2_to_real",
    "unitree_ros_to_real",
    "unitree_il_lerobot",
    "kinect_teleoperate",
    "xr_teleoperate",
}


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
        "teleoperate": "teleoperation",
        "reality": "deployment",
        "real": "deployment",
        "camera": "sensor",
        "lidar": "sensor",
    }
    for key, topic in mapping.items():
        if key in text and topic not in topics:
            topics.append(topic)
    return topics or ["unitree"]


def repo_matches(repo: dict[str, Any], keywords: list[str]) -> bool:
    text = f"{repo.get('name', '')} {repo.get('description') or ''}".lower()
    return any(kw in text for kw in keywords)


def to_repo_entry(repo: dict[str, Any]) -> dict[str, Any]:
    name = str(repo.get("name", "")).strip()
    description = str(repo.get("description") or "")
    lower = name.lower()
    priority = "core" if ("g1" in lower or lower in CORE_REPO_HINTS) else "supporting"
    return {
        "name": name,
        "url": str(repo.get("html_url", "")),
        "branch": str(repo.get("default_branch", "main")),
        "topics": infer_topics(name, description),
        "priority": priority,
        "description": description,
        "archived": bool(repo.get("archived", False)),
        "private": bool(repo.get("private", False)),
        "pushed_at": str(repo.get("pushed_at") or ""),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover Unitree repositories")
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
        default=6,
        help="Maximum GitHub API pages (100 repos per page)",
    )
    parser.add_argument(
        "--snapshot-out",
        type=Path,
        default=Path("data/snapshots"),
        help="Output directory for discovery snapshot",
    )
    parser.add_argument(
        "--catalog-out",
        type=Path,
        default=Path("sources/unitree_org_repo_catalog.json"),
        help="Output JSON catalog of all discovered org repos",
    )
    parser.add_argument(
        "--include-all",
        action="store_true",
        help="Include all public org repos in manifest, not only keyword-matched repos",
    )
    parser.add_argument(
        "--include-archived",
        action="store_true",
        help="Include archived repositories in selected results",
    )
    parser.add_argument(
        "--update-manifest",
        action="store_true",
        help="Merge selected repos into source manifest",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    keywords = [k.strip().lower() for k in args.keywords.split(",") if k.strip()]

    all_repos_raw: list[dict[str, Any]] = []
    for page in range(1, args.max_pages + 1):
        url = f"https://api.github.com/orgs/{args.org}/repos?per_page=100&page={page}"
        try:
            data = fetch_json(url)
        except urlerror.URLError as exc:
            print(f"[ERROR] Failed to fetch page {page}: {exc}")
            break

        if not isinstance(data, list) or not data:
            break
        all_repos_raw.extend(data)

    all_public = [r for r in all_repos_raw if not bool(r.get("private", False))]
    matched = [r for r in all_public if repo_matches(r, keywords)]

    if args.include_all:
        selected_raw = all_public
    else:
        selected_raw = matched

    if not args.include_archived:
        selected_raw = [r for r in selected_raw if not bool(r.get("archived", False))]

    selected_entries = [to_repo_entry(r) for r in selected_raw]
    selected_entries.sort(key=lambda x: x["name"].lower())

    # Catalog of all repos (tracked in sources/ for transparency)
    all_catalog = [to_repo_entry(r) for r in all_public]
    all_catalog.sort(key=lambda x: x["name"].lower())
    catalog_payload = {
        "org": args.org,
        "timestamp_unix": int(time.time()),
        "total_public_repos": len(all_catalog),
        "repos": all_catalog,
    }
    args.catalog_out.parent.mkdir(parents=True, exist_ok=True)
    args.catalog_out.write_text(json.dumps(catalog_payload, indent=2), encoding="utf-8")
    print(f"[OK] Wrote repo catalog: {args.catalog_out}")

    snapshot = {
        "org": args.org,
        "timestamp_unix": int(time.time()),
        "keywords": keywords,
        "all_repo_count": len(all_public),
        "matched_repo_count": len(matched),
        "selected_repo_count": len(selected_entries),
        "include_all": args.include_all,
        "include_archived": args.include_archived,
        "selected_repos": selected_entries,
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
        for repo in selected_entries:
            merged[repo["name"]] = {
                "name": repo["name"],
                "url": repo["url"],
                "branch": repo["branch"],
                "topics": repo["topics"],
                "priority": repo["priority"],
            }

        manifest_data["repos"] = [merged[k] for k in sorted(merged.keys(), key=str.lower)]
        manifest_data["updated_at"] = time.strftime("%Y-%m-%d")
        args.manifest.write_text(
            yaml.safe_dump(manifest_data, sort_keys=False),
            encoding="utf-8",
        )
        print(
            f"[OK] Updated manifest repos: {len(existing)} -> {len(manifest_data['repos'])} "
            f"({len(manifest_data['repos']) - len(existing)} added/updated)"
        )

    print(f"[INFO] Total public repos seen: {len(all_public)}")
    print(f"[INFO] Keyword matches: {len(matched)}")
    print(f"[INFO] Selected repos for manifest: {len(selected_entries)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
