#!/usr/bin/env python3
"""Evaluate an OpenAI-compatible model on Unitree G1 source-selection tasks."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
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


def shrink(text: str, max_chars: int = 220) -> str:
    clean = " ".join(text.split())
    return clean[:max_chars]


def unique_candidates(matches: list[Match], max_candidates: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in matches:
        path = str(item.record.get("path", ""))
        if not path or path in seen:
            continue
        seen.add(path)
        out.append(
            {
                "path": path,
                "title": str(item.record.get("title", "")),
                "type": str(item.record.get("source_type", "")),
                "score": round(item.score, 4),
                "url": str(item.record.get("url", "")),
                "snippet": shrink(str(item.record.get("content", ""))),
            }
        )
        if len(out) >= max_candidates:
            break
    return out


def normalize_api_base(api_base: str) -> str:
    base = api_base.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


def call_chat(
    *,
    api_base: str,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    timeout_sec: int,
) -> str:
    endpoint = normalize_api_base(api_base)
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from model endpoint: {err}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to reach model endpoint: {exc}") from exc

    parsed = json.loads(body)
    choices = parsed.get("choices", [])
    if not choices:
        raise RuntimeError(f"No choices returned from endpoint: {body[:400]}")
    content = choices[0].get("message", {}).get("content", "")
    if not isinstance(content, str):
        raise RuntimeError(f"Unexpected completion format: {body[:400]}")
    return content


def parse_model_json(text: str) -> dict[str, Any]:
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        parsed = json.loads(raw[start : end + 1])
        if isinstance(parsed, dict):
            return parsed

    raise ValueError("Model response is not valid JSON object")


def match_patterns(values: list[str], patterns: list[str]) -> tuple[int, int]:
    if not values or not patterns:
        return 0, len(patterns)
    hits = 0
    lowered_values = [v.lower() for v in values]
    for pat in patterns:
        p = pat.lower()
        if any(p in val for val in lowered_values):
            hits += 1
    return hits, len(patterns)


def count_selected_relevant(values: list[str], patterns: list[str]) -> int:
    if not values or not patterns:
        return 0
    lowered_patterns = [p.lower() for p in patterns]
    count = 0
    for value in values:
        v = value.lower()
        if any(p in v for p in lowered_patterns):
            count += 1
    return count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate OpenAI-compatible model for source selection")
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
    parser.add_argument(
        "--api-base",
        type=str,
        default=os.environ.get("OPENAI_API_BASE", os.environ.get("OPENAI_BASE_URL", "http://localhost:8000/v1")),
        help="OpenAI-compatible API base URL",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.environ.get("OPENAI_API_KEY", "EMPTY"),
        help="API key for endpoint",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.environ.get("OPENAI_MODEL", ""),
        help="Model name",
    )
    parser.add_argument("--top-k", type=int, default=20, help="Retriever top-k before dedupe")
    parser.add_argument("--candidates", type=int, default=10, help="Unique candidates given to model")
    parser.add_argument("--select-k", type=int, default=3, help="Expected number of selected paths")
    parser.add_argument("--temperature", type=float, default=0.0, help="Model temperature")
    parser.add_argument("--timeout-sec", type=int, default=60, help="HTTP timeout in seconds")
    parser.add_argument("--max-cases", type=int, default=0, help="Limit number of benchmark cases (0=all)")
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path("docs/verification/agent_eval.json"),
        help="JSON output path",
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=Path("docs/verification/agent_eval.md"),
        help="Markdown output path",
    )
    parser.add_argument("--fail-below", type=float, default=0.70, help="Fail when pass rate below threshold")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when below threshold")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.model:
        raise SystemExit("Missing --model (or OPENAI_MODEL env var)")

    bench = yaml.safe_load(args.benchmark.read_text(encoding="utf-8"))
    if not isinstance(bench, dict) or not isinstance(bench.get("cases"), list):
        raise ValueError("Invalid benchmark format")

    records = load_index(args.index)
    cases = list(bench["cases"])
    if args.max_cases > 0:
        cases = cases[: args.max_cases]

    results: list[dict[str, Any]] = []
    pass_count = 0
    precision_sum = 0.0
    recall_sum = 0.0

    for i, case in enumerate(cases, start=1):
        cid = str(case.get("id", f"case_{i}"))
        query = str(case.get("query", "")).strip()
        expected = [str(x) for x in case.get("expected_path_patterns", [])]
        forbidden = [str(x) for x in case.get("forbidden_path_patterns", [])]
        require_all_expected = bool(case.get("require_all_expected", False))
        max_forbidden_hits = int(case.get("max_forbidden_hits", 0 if forbidden else 999999))

        eval_records = filter_leaky_records(records, args.benchmark, expected)
        ranked = rank_records(records=eval_records, query=query, top_k=args.top_k)
        candidates = unique_candidates(ranked, args.candidates)

        candidate_lines: list[str] = []
        for idx, c in enumerate(candidates, start=1):
            candidate_lines.append(
                f"{idx}. path={c['path']} | type={c['type']} | title={c['title']} | snippet={c['snippet']}"
            )

        user_prompt = (
            "Select the most relevant source paths for this Unitree G1 question.\n"
            "Return JSON only with schema: "
            '{"selected_paths": ["..."], "rationale": "..."}.\n'
            f"Choose at most {args.select_k} paths and only from the candidate list.\n\n"
            f"Question:\n{query}\n\n"
            "Candidates:\n"
            + "\n".join(candidate_lines)
        )

        messages = [
            {
                "role": "system",
                "content": "You are a retrieval expert. Output strict JSON only.",
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ]

        case_out: dict[str, Any] = {
            "id": cid,
            "query": query,
            "expected_path_patterns": expected,
            "forbidden_path_patterns": forbidden,
            "require_all_expected": require_all_expected,
            "max_forbidden_hits": max_forbidden_hits,
            "candidates": candidates,
        }
        try:
            raw = call_chat(
                api_base=args.api_base,
                api_key=args.api_key,
                model=args.model,
                messages=messages,
                temperature=args.temperature,
                timeout_sec=args.timeout_sec,
            )
            parsed = parse_model_json(raw)
            selected = parsed.get("selected_paths", [])
            if not isinstance(selected, list):
                raise ValueError("selected_paths must be a list")
            selected_paths = [str(x) for x in selected if str(x).strip()]
            if len(selected_paths) > args.select_k:
                selected_paths = selected_paths[: args.select_k]

            matched_expected, expected_total = match_patterns(selected_paths, expected)
            matched_forbidden, _ = match_patterns(selected_paths, forbidden)
            selected_relevant = count_selected_relevant(selected_paths, expected)

            recall = (matched_expected / expected_total) if expected_total else 1.0
            precision = (selected_relevant / len(selected_paths)) if selected_paths else 0.0
            expected_ok = (
                matched_expected == expected_total if require_all_expected else matched_expected > 0
            ) if expected_total else True
            forbidden_ok = matched_forbidden <= max_forbidden_hits
            passed = expected_ok and forbidden_ok

            pass_count += 1 if passed else 0
            precision_sum += precision
            recall_sum += recall

            case_out.update(
                {
                    "pass": passed,
                    "selected_paths": selected_paths,
                    "rationale": parsed.get("rationale", ""),
                    "precision": round(precision, 4),
                    "recall": round(recall, 4),
                    "matched_expected": matched_expected,
                    "expected_total": expected_total,
                    "matched_forbidden": matched_forbidden,
                    "raw_response": raw[:1200],
                }
            )
        except Exception as exc:  # pragma: no cover - endpoint/model variance
            case_out.update(
                {
                    "pass": False,
                    "selected_paths": [],
                    "precision": 0.0,
                    "recall": 0.0,
                    "matched_forbidden": 0,
                    "error": str(exc),
                }
            )

        results.append(case_out)
        print(f"[{i}/{len(cases)}] {cid}: pass={case_out['pass']}")

    total = len(results)
    pass_rate = (pass_count / total) if total else 0.0
    avg_precision = (precision_sum / total) if total else 0.0
    avg_recall = (recall_sum / total) if total else 0.0

    report = {
        "timestamp_unix": int(time.time()),
        "benchmark": str(args.benchmark),
        "index": str(args.index),
        "api_base": args.api_base,
        "model": args.model,
        "total": total,
        "passed": pass_count,
        "pass_rate": pass_rate,
        "avg_precision": avg_precision,
        "avg_recall": avg_recall,
        "top_k": args.top_k,
        "candidates": args.candidates,
        "select_k": args.select_k,
        "fail_below": args.fail_below,
        "results": results,
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Agent Source-Selection Evaluation",
        "",
        f"- Total cases: {total}",
        f"- Passed: {pass_count}",
        f"- Pass rate: {pass_rate:.2%}",
        f"- Avg precision: {avg_precision:.2%}",
        f"- Avg recall: {avg_recall:.2%}",
        f"- Model: `{args.model}`",
        f"- API base: `{args.api_base}`",
        "",
        "| Case | Pass | Precision | Recall |",
        "| --- | --- | --- | --- |",
    ]
    for item in results:
        lines.append(
            f"| {item['id']} | {item['pass']} | {item.get('precision', 0.0):.2f} | {item.get('recall', 0.0):.2f} |"
        )

    args.md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[OK] Wrote agent eval JSON: {args.json_out}")
    print(f"[OK] Wrote agent eval MD: {args.md_out}")
    print(
        f"[SUMMARY] passed={pass_count}/{total} pass_rate={pass_rate:.2%} "
        f"avg_precision={avg_precision:.2%} avg_recall={avg_recall:.2%}"
    )

    if args.strict and pass_rate < args.fail_below:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
