#!/usr/bin/env python3
"""Build static data payloads for the GitHub Pages demo website."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - runtime dependency check
    raise SystemExit(
        "Missing dependency: pyyaml. Install with `pip install pyyaml`."
    ) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build static site data files")
    parser.add_argument(
        "--index-jsonl",
        type=Path,
        default=Path("data/index/knowledge_index.jsonl"),
        help="Knowledge index JSONL path",
    )
    parser.add_argument(
        "--index-meta",
        type=Path,
        default=Path("data/index/knowledge_index.meta.json"),
        help="Knowledge index metadata path",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("sources/unitree_g1_sources.yaml"),
        help="Source manifest path",
    )
    parser.add_argument(
        "--verification-json",
        type=Path,
        default=Path("docs/verification/g1_docs_verification.json"),
        help="Verification report path",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("site/data"),
        help="Output directory for site JSON files",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=5000,
        help="Maximum number of search records emitted to site",
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    if args.index_jsonl.exists():
        with args.index_jsonl.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                records.append(
                    {
                        "id": rec.get("id"),
                        "title": rec.get("title"),
                        "type": rec.get("source_type"),
                        "path": rec.get("path"),
                        "url": rec.get("url"),
                        "tags": rec.get("tags", []),
                        "content": str(rec.get("content", ""))[:900],
                    }
                )
                if len(records) >= args.max_records:
                    break

    site_index = {
        "records": records,
        "record_count": len(records),
    }
    (args.out_dir / "search-index.json").write_text(
        json.dumps(site_index, ensure_ascii=False),
        encoding="utf-8",
    )

    meta = read_json(args.index_meta)
    manifest = read_yaml(args.manifest)
    verification = read_json(args.verification_json)

    overview = {
        "index_meta": meta,
        "manifest": {
            "support_docs": len(manifest.get("support_docs", [])) if isinstance(manifest, dict) else 0,
            "repos": len(manifest.get("repos", [])) if isinstance(manifest, dict) else 0,
        },
        "verification": {
            "total_urls": verification.get("total_urls", 0),
            "verified": verification.get("verified", 0),
            "blocked_access": verification.get("blocked_access", 0),
            "needs_review": verification.get("needs_review", 0),
            "errors": verification.get("errors", 0),
        },
    }
    (args.out_dir / "overview.json").write_text(
        json.dumps(overview, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[OK] Wrote site search index: {args.out_dir / 'search-index.json'}")
    print(f"[OK] Wrote site overview: {args.out_dir / 'overview.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
