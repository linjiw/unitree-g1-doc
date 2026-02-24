#!/usr/bin/env python3
"""Query the local Unitree knowledge index with lexical scoring."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from retrieval_scoring import normalize_query_tokens, rank_records


def build_snippet(content: str, query_tokens: list[str], max_chars: int = 320) -> str:
    plain = content.replace("\n", " ").strip()
    if len(plain) <= max_chars:
        return plain

    lower = plain.lower()
    first_hit = min((lower.find(tok) for tok in query_tokens if tok in lower), default=-1)
    if first_hit < 0:
        return plain[:max_chars].strip()

    start = max(first_hit - max_chars // 3, 0)
    end = min(start + max_chars, len(plain))
    return plain[start:end].strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query local Unitree knowledge index")
    parser.add_argument("question", type=str, help="Question text")
    parser.add_argument(
        "--index",
        type=Path,
        default=Path("data/index/knowledge_index.jsonl"),
        help="Path to JSONL knowledge index",
    )
    parser.add_argument("--top-k", type=int, default=8, help="Number of results to return")
    parser.add_argument(
        "--source-type",
        action="append",
        default=[],
        help="Filter results by source type (repeatable)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.index.exists():
        print(f"Index not found: {args.index}")
        print("Run: python3 scripts/build_knowledge_index.py")
        return 1

    query_tokens = normalize_query_tokens(args.question)
    source_filters = {s.strip() for s in args.source_type if s.strip()}
    records: list[dict[str, Any]] = []
    with args.index.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    ranked = rank_records(
        records=records,
        query=args.question,
        top_k=args.top_k,
        source_filters=source_filters if source_filters else None,
    )
    if args.format == "json":
        payload = {
            "question": args.question,
            "top_k": args.top_k,
            "matches": [],
        }
        for match in ranked:
            rec = match.record
            payload["matches"].append(
                {
                    "score": round(match.score, 4),
                    "id": rec.get("id"),
                    "type": rec.get("source_type"),
                    "title": rec.get("title"),
                    "path": rec.get("path"),
                    "url": rec.get("url"),
                    "tags": rec.get("tags", []),
                    "snippet": build_snippet(str(rec.get("content", "")), query_tokens),
                }
            )
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if args.format == "markdown":
        print(f"# Query\n\n{args.question}\n")
        for idx, match in enumerate(ranked, start=1):
            rec = match.record
            print(f"## {idx}. {rec.get('title')} (`{rec.get('source_type')}`)\n")
            print(f"- score: `{match.score:.2f}`")
            if rec.get("path"):
                print(f"- path: `{rec['path']}`")
            if rec.get("url"):
                print(f"- url: {rec['url']}")
            print(f"- snippet: {build_snippet(str(rec.get('content', '')), query_tokens)}\n")
        return 0

    if not ranked:
        print("No relevant matches found.")
        return 0

    print(f"Question: {args.question}")
    print(f"Top {len(ranked)} matches:\n")
    for i, match in enumerate(ranked, start=1):
        rec = match.record
        preview = build_snippet(str(rec.get("content", "")), query_tokens)
        print(
            f"{i}. score={match.score:.2f} id={rec.get('id')} "
            f"type={rec.get('source_type')}"
        )
        print(f"   title: {rec.get('title')}")
        if rec.get("path"):
            print(f"   path: {rec['path']}")
        if rec.get("url"):
            print(f"   url: {rec['url']}")
        print(f"   preview: {preview}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
