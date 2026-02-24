#!/usr/bin/env python3
"""Evaluate retrieval quality against a local benchmark file."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency check
    raise SystemExit("Missing dependency: pyyaml. Install with `pip install pyyaml`.") from exc


TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")


@dataclass
class Match:
    score: float
    record: dict[str, Any]


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def score(query_tokens: list[str], record: dict[str, Any]) -> float:
    if not query_tokens:
        return 0.0

    content = str(record.get("content", "")).lower()
    title = str(record.get("title", "")).lower()
    tags = " ".join(record.get("tags", [])).lower()

    content_tokens = tokenize(content)
    title_tokens = tokenize(title)
    tag_tokens = tokenize(tags)

    if not content_tokens and not title_tokens:
        return 0.0

    query_set = set(query_tokens)
    content_set = set(content_tokens)
    title_set = set(title_tokens)
    tag_set = set(tag_tokens)

    overlap = query_set & (content_set | title_set | tag_set)
    coverage = len(overlap) / max(len(query_set), 1)

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

    raw = (
        content_hits
        + (title_hits * 2.2)
        + (tag_hits * 1.6)
        + (coverage * 8.0)
        + phrase_bonus
    )
    return raw * source_boost


def load_index(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def search(records: list[dict[str, Any]], query: str, top_k: int) -> list[Match]:
    query_tokens = tokenize(query)
    ranked: list[Match] = []
    for rec in records:
        s = score(query_tokens, rec)
        if s > 0:
            ranked.append(Match(s, rec))
    ranked.sort(key=lambda x: x.score, reverse=True)
    return ranked[:top_k]


def match_expected(results: list[Match], patterns: list[str]) -> tuple[bool, str]:
    if not patterns:
        return True, "no expected patterns"

    for idx, item in enumerate(results, start=1):
        path = str(item.record.get("path", ""))
        url = str(item.record.get("url", ""))
        target = f"{path}\n{url}".lower()
        for pat in patterns:
            if pat.lower() in target:
                return True, f"matched pattern `{pat}` at rank {idx}"
    return False, "no expected path pattern found in top-k"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate retrieval benchmark")
    parser.add_argument(
        "--benchmark",
        type=Path,
        default=Path("benchmarks/retrieval_benchmark.yaml"),
        help="Benchmark yaml path",
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=Path("data/index/knowledge_index.jsonl"),
        help="Knowledge index JSONL path",
    )
    parser.add_argument("--top-k", type=int, default=8, help="Top-K per query")
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path("docs/verification/retrieval_eval.json"),
        help="JSON output path",
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=Path("docs/verification/retrieval_eval.md"),
        help="Markdown output path",
    )
    parser.add_argument(
        "--fail-below",
        type=float,
        default=0.80,
        help="Fail if pass rate is below this threshold",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when score is below threshold",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    bench = yaml.safe_load(args.benchmark.read_text(encoding="utf-8"))
    if not isinstance(bench, dict) or not isinstance(bench.get("cases"), list):
        raise ValueError("Invalid benchmark format")

    records = load_index(args.index)
    cases = bench["cases"]

    results_payload: list[dict[str, Any]] = []
    passed = 0

    for case in cases:
        cid = str(case.get("id", ""))
        query = str(case.get("query", "")).strip()
        expected = list(case.get("expected_path_patterns", []))

        ranked = search(records, query, args.top_k)
        ok, reason = match_expected(ranked, expected)
        if ok:
            passed += 1

        top = []
        for m in ranked:
            top.append(
                {
                    "score": round(m.score, 4),
                    "id": m.record.get("id"),
                    "type": m.record.get("source_type"),
                    "path": m.record.get("path"),
                    "url": m.record.get("url"),
                    "title": m.record.get("title"),
                }
            )

        results_payload.append(
            {
                "id": cid,
                "query": query,
                "pass": ok,
                "reason": reason,
                "expected_path_patterns": expected,
                "top_results": top,
            }
        )

    total = len(cases)
    pass_rate = (passed / total) if total else 0.0

    report = {
        "timestamp_unix": int(time.time()),
        "benchmark": str(args.benchmark),
        "index": str(args.index),
        "total": total,
        "passed": passed,
        "pass_rate": pass_rate,
        "top_k": args.top_k,
        "fail_below": args.fail_below,
        "results": results_payload,
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Retrieval Evaluation",
        "",
        f"- Total cases: {total}",
        f"- Passed: {passed}",
        f"- Pass rate: {pass_rate:.2%}",
        f"- Top-K: {args.top_k}",
        f"- Threshold: {args.fail_below:.0%}",
        "",
        "| Case | Pass | Reason |",
        "| --- | --- | --- |",
    ]

    for item in results_payload:
        lines.append(
            f"| {item['id']} | {item['pass']} | {item['reason']} |"
        )

    args.md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[OK] Wrote retrieval eval JSON: {args.json_out}")
    print(f"[OK] Wrote retrieval eval MD: {args.md_out}")
    print(f"[SUMMARY] passed={passed}/{total} pass_rate={pass_rate:.2%}")

    if args.strict and pass_rate < args.fail_below:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
