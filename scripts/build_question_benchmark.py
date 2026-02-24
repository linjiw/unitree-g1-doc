#!/usr/bin/env python3
"""Convert a question bank YAML into eval_retrieval benchmark format."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: pyyaml. Install with `pip install pyyaml`.") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build retrieval benchmark from question bank")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("benchmarks/ollama_question_bank.yaml"),
        help="Input question bank YAML",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmarks/ollama_question_benchmark.yaml"),
        help="Output benchmark YAML",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="ollama_codex_question_bank",
        help="Benchmark name",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = yaml.safe_load(args.input.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Invalid question bank format")

    questions = payload.get("questions", [])
    if not isinstance(questions, list):
        raise ValueError("Invalid question bank: `questions` must be a list")

    cases = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        question = str(q.get("question", "")).strip()
        if not question:
            continue
        qid = str(q.get("id", "")).strip() or f"q_{len(cases) + 1}"
        patterns = [str(p).strip() for p in q.get("expected_path_patterns", []) if str(p).strip()]
        cases.append(
            {
                "id": qid,
                "query": question,
                "expected_path_patterns": patterns,
            }
        )

    out = {
        "version": 1,
        "name": args.name,
        "cases": cases,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(out, sort_keys=False), encoding="utf-8")
    print(f"[OK] Wrote benchmark YAML: {args.output}")
    print(f"[SUMMARY] cases={len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
