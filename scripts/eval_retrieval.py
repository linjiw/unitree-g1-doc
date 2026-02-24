#!/usr/bin/env python3
"""Evaluate retrieval quality against a local benchmark file."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency check
    raise SystemExit("Missing dependency: pyyaml. Install with `pip install pyyaml`.") from exc

from retrieval_scoring import Match, rank_records


def load_index(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def path_matches_patterns(path: str, patterns: list[str]) -> bool:
    if not path or not patterns:
        return False
    lowered = path.lower()
    return any(pattern.lower() in lowered for pattern in patterns)


def filter_leaky_records(
    records: list[dict[str, Any]],
    benchmark_path: Path,
    expected_patterns: list[str],
) -> list[dict[str, Any]]:
    bench_rel = benchmark_path.as_posix().lower()
    bench_abs = benchmark_path.resolve().as_posix().lower()
    filtered: list[dict[str, Any]] = []

    for record in records:
        path = str(record.get("path", "")).lower()
        if not path:
            filtered.append(record)
            continue
        is_benchmark_doc = bench_rel in path or bench_abs in path
        if is_benchmark_doc and not path_matches_patterns(path, expected_patterns):
            continue
        filtered.append(record)

    return filtered


def dedupe_matches(matches: list[Match], top_k: int) -> list[Match]:
    deduped: list[Match] = []
    seen: set[str] = set()
    for item in matches:
        path = str(item.record.get("path", "")).strip()
        url = str(item.record.get("url", "")).strip()
        rid = str(item.record.get("id", "")).strip()
        key = path or url or rid
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= top_k:
            break
    return deduped


def match_pattern_rank(results: list[Match], pattern: str) -> int | None:
    needle = pattern.lower()
    for idx, item in enumerate(results, start=1):
        path = str(item.record.get("path", ""))
        url = str(item.record.get("url", ""))
        target = f"{path}\n{url}".lower()
        if needle in target:
            return idx
    return None


def evaluate_case_matches(
    *,
    results: list[Match],
    expected_patterns: list[str],
    forbidden_patterns: list[str],
    require_all_expected: bool,
    max_forbidden_hits: int,
) -> tuple[bool, str, int, int, int]:
    expected_ranks: dict[str, int] = {}
    for pattern in expected_patterns:
        rank = match_pattern_rank(results, pattern)
        if rank is not None:
            expected_ranks[pattern] = rank

    forbidden_ranks: dict[str, int] = {}
    for pattern in forbidden_patterns:
        rank = match_pattern_rank(results, pattern)
        if rank is not None:
            forbidden_ranks[pattern] = rank

    matched_expected = len(expected_ranks)
    expected_total = len(expected_patterns)
    forbidden_hits = len(forbidden_ranks)

    if require_all_expected:
        expected_ok = matched_expected == expected_total
    else:
        expected_ok = matched_expected > 0 or expected_total == 0

    forbidden_ok = forbidden_hits <= max_forbidden_hits
    passed = expected_ok and forbidden_ok

    if not expected_ok:
        if require_all_expected:
            reason = f"matched {matched_expected}/{expected_total} expected patterns"
        else:
            reason = "no expected path pattern found in top-k"
    elif not forbidden_ok:
        reason = f"matched {forbidden_hits} forbidden patterns (limit {max_forbidden_hits})"
    elif expected_ranks:
        best_pattern = min(expected_ranks, key=expected_ranks.get)
        best_rank = expected_ranks[best_pattern]
        reason = f"matched pattern `{best_pattern}` at rank {best_rank}"
    else:
        reason = "no expected patterns"

    return passed, reason, matched_expected, expected_total, forbidden_hits


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
        forbidden = list(case.get("forbidden_path_patterns", []))
        require_all_expected = bool(case.get("require_all_expected", False))
        max_forbidden_hits = int(case.get("max_forbidden_hits", 0 if forbidden else 999999))

        eval_records = filter_leaky_records(records, args.benchmark, expected)
        ranked_raw = rank_records(records=eval_records, query=query, top_k=args.top_k * 6)
        ranked = dedupe_matches(ranked_raw, args.top_k)
        ok, reason, matched_expected, expected_total, forbidden_hits = evaluate_case_matches(
            results=ranked,
            expected_patterns=expected,
            forbidden_patterns=forbidden,
            require_all_expected=require_all_expected,
            max_forbidden_hits=max_forbidden_hits,
        )
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
                "forbidden_path_patterns": forbidden,
                "require_all_expected": require_all_expected,
                "max_forbidden_hits": max_forbidden_hits,
                "matched_expected": matched_expected,
                "expected_total": expected_total,
                "forbidden_hits": forbidden_hits,
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
