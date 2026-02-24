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
        "--repo-lock-json",
        type=Path,
        default=Path("docs/verification/repo_lock.json"),
        help="Repo lock report path",
    )
    parser.add_argument(
        "--retrieval-eval-json",
        type=Path,
        default=Path("docs/verification/retrieval_eval.json"),
        help="Baseline retrieval evaluation JSON path",
    )
    parser.add_argument(
        "--agent-eval-json",
        type=Path,
        default=Path("docs/verification/agent_eval.json"),
        help="Baseline agent source-selection evaluation JSON path",
    )
    parser.add_argument(
        "--ollama-retrieval-eval-json",
        type=Path,
        default=Path("docs/verification/ollama_question_retrieval_eval.json"),
        help="Ollama question benchmark retrieval evaluation JSON path",
    )
    parser.add_argument(
        "--ollama-agent-eval-json",
        type=Path,
        default=Path("docs/verification/ollama_agent_eval.json"),
        help="Ollama question benchmark agent source-selection evaluation JSON path",
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


def summarize_eval(path: Path, label: str, test_type: str, command: str) -> dict[str, Any]:
    payload = read_json(path)
    if not payload:
        return {
            "label": label,
            "test_type": test_type,
            "command": command,
            "path": str(path),
            "available": False,
        }

    results = payload.get("results", [])
    failed_cases: list[str] = []
    if isinstance(results, list):
        for item in results:
            if not isinstance(item, dict):
                continue
            if bool(item.get("pass")):
                continue
            case_id = item.get("id")
            if case_id:
                failed_cases.append(str(case_id))

    return {
        "label": label,
        "test_type": test_type,
        "command": command,
        "path": str(path),
        "available": True,
        "timestamp_unix": payload.get("timestamp_unix"),
        "benchmark": payload.get("benchmark"),
        "index": payload.get("index"),
        "model": payload.get("model"),
        "api_base": payload.get("api_base"),
        "total": payload.get("total"),
        "passed": payload.get("passed"),
        "pass_rate": payload.get("pass_rate"),
        "top_k": payload.get("top_k"),
        "fail_below": payload.get("fail_below"),
        "avg_precision": payload.get("avg_precision"),
        "avg_recall": payload.get("avg_recall"),
        "failed_cases": failed_cases,
        "failed_count": len(failed_cases),
    }


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
    repo_lock = read_json(args.repo_lock_json)
    benchmark_runs = [
        summarize_eval(
            args.retrieval_eval_json,
            "Baseline Retrieval Regression",
            "retrieval",
            "make eval-retrieval",
        ),
        summarize_eval(
            args.agent_eval_json,
            "Baseline Llama Source-Selection",
            "agent",
            "make eval-agent-ollama",
        ),
        summarize_eval(
            args.ollama_retrieval_eval_json,
            "Ollama+Codex Question Set Retrieval",
            "retrieval",
            "make eval-retrieval-ollama-qbank",
        ),
        summarize_eval(
            args.ollama_agent_eval_json,
            "Ollama+Codex Question Set Llama Source-Selection",
            "agent",
            "make eval-agent-ollama-qbank",
        ),
    ]

    latest_eval_ts = max(
        (
            int(run.get("timestamp_unix"))
            for run in benchmark_runs
            if run.get("available") and run.get("timestamp_unix") is not None
        ),
        default=None,
    )

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
        "repo_lock": {
            "total": repo_lock.get("summary", {}).get("total", 0),
            "worktree_present": repo_lock.get("summary", {}).get("worktree_present", 0),
            "mirror_present": repo_lock.get("summary", {}).get("mirror_present", 0),
        },
        "benchmarks": {
            "latest_timestamp_unix": latest_eval_ts,
            "runs": benchmark_runs,
            "tests_run": [
                {
                    "command": "make eval-retrieval",
                    "description": "Lexical retrieval regression on baseline benchmark.",
                },
                {
                    "command": "make eval-agent-ollama",
                    "description": "Llama source-selection on baseline benchmark.",
                },
                {
                    "command": "make gen-questions-ollama",
                    "description": "Generate and curate an Ollama+Codex question bank.",
                },
                {
                    "command": "make eval-retrieval-ollama-qbank",
                    "description": "Retrieval regression on the curated Ollama+Codex benchmark.",
                },
                {
                    "command": "make eval-agent-ollama-qbank",
                    "description": "Llama source-selection on the curated Ollama+Codex benchmark.",
                },
            ],
            "quality_gates": {
                "baseline_retrieval_min": 0.75,
                "baseline_agent_min": 0.70,
                "qbank_retrieval_min": 0.70,
                "qbank_agent_min": 0.60,
            },
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
