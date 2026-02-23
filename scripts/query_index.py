#!/usr/bin/env python3
"""Query the local Unitree knowledge index with lexical scoring."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9_]+", text.lower())


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


def score(query_tokens: list[str], record: dict[str, Any]) -> float:
    if not query_tokens:
        return 0.0

    content = str(record.get("content", "")).lower()
    title = str(record.get("title", "")).lower()
    tags = " ".join(record.get("tags", [])).lower()

    if not content and not title:
        return 0.0

    content_tokens = tokenize(content)
    title_tokens = tokenize(title)
    tag_tokens = tokenize(tags)

    if not content_tokens and not title_tokens:
        return 0.0

    content_set = set(content_tokens)
    title_set = set(title_tokens)
    tag_set = set(tag_tokens)
    query_set = set(query_tokens)

    overlap_content = query_set & content_set
    overlap_title = query_set & title_set
    overlap_tags = query_set & tag_set

    coverage = len(overlap_content | overlap_title | overlap_tags) / max(len(query_set), 1)
    content_hits = sum(min(content_tokens.count(tok), 5) for tok in query_set)
    title_hits = sum(min(title_tokens.count(tok), 3) for tok in query_set)
    tag_hits = sum(min(tag_tokens.count(tok), 2) for tok in query_set)

    phrase = " ".join(query_tokens[:4])
    phrase_bonus = 2.0 if phrase and phrase in content else 0.0

    source_boost = {
        "support_doc": 1.3,
        "curated_doc": 1.2,
        "skill_doc": 1.1,
        "source_manifest": 0.65,
        "repo_file": 1.0,
    }.get(str(record.get("source_type", "")), 1.0)
    if "support_unverified" in record.get("tags", []):
        source_boost *= 0.35

    raw_score = (
        content_hits
        + (title_hits * 2.2)
        + (tag_hits * 1.6)
        + (coverage * 8.0)
        + phrase_bonus
    )
    return raw_score * source_boost


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

    query_tokens = tokenize(args.question)
    source_filters = {s.strip() for s in args.source_type if s.strip()}
    results: list[tuple[float, dict[str, Any]]] = []

    with args.index.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if source_filters and record.get("source_type") not in source_filters:
                continue
            s = score(query_tokens, record)
            if s > 0:
                results.append((s, record))

    ranked = sorted(results, key=lambda x: x[0], reverse=True)[: args.top_k]
    if args.format == "json":
        payload = {
            "question": args.question,
            "top_k": args.top_k,
            "matches": [],
        }
        for s, rec in ranked:
            payload["matches"].append(
                {
                    "score": round(s, 4),
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
        for idx, (s, rec) in enumerate(ranked, start=1):
            print(f"## {idx}. {rec.get('title')} (`{rec.get('source_type')}`)\n")
            print(f"- score: `{s:.2f}`")
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
    for i, (s, rec) in enumerate(ranked, start=1):
        preview = build_snippet(str(rec.get("content", "")), query_tokens)
        print(f"{i}. score={s:.2f} id={rec.get('id')} type={rec.get('source_type')}")
        print(f"   title: {rec.get('title')}")
        if rec.get("path"):
            print(f"   path: {rec['path']}")
        if rec.get("url"):
            print(f"   url: {rec['url']}")
        print(f"   preview: {preview}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
