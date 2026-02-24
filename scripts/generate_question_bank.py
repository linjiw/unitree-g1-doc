#!/usr/bin/env python3
"""Generate Unitree G1 evaluation questions with an OpenAI-compatible model."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: pyyaml. Install with `pip install pyyaml`.") from exc


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


def parse_model_json(text: str) -> dict:
    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\n", "", raw)
        raw = raw.removesuffix("```").strip()

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

    raise ValueError("Model output is not valid JSON object")


def normalize_id(raw: str, fallback: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", raw.strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        return fallback
    return cleaned


def load_seed_paths(seed_file: Path) -> list[str]:
    if not seed_file.exists():
        return []
    data = yaml.safe_load(seed_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return []
    cases = data.get("cases", [])
    out: list[str] = []
    for case in cases:
        for pat in case.get("expected_path_patterns", []):
            pat_s = str(pat).strip()
            if pat_s and pat_s not in out:
                out.append(pat_s)
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Unitree G1 question bank with Ollama/OpenAI-compatible API")
    parser.add_argument(
        "--seed-benchmark",
        type=Path,
        default=Path("benchmarks/retrieval_benchmark.yaml"),
        help="Seed benchmark file with known source paths",
    )
    parser.add_argument(
        "--api-base",
        type=str,
        default=os.environ.get("OPENAI_API_BASE", os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:11434/v1")),
        help="OpenAI-compatible API base",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.environ.get("OPENAI_API_KEY", "ollama"),
        help="API key",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.environ.get("OPENAI_MODEL", "llama3.1"),
        help="Model name",
    )
    parser.add_argument("--count", type=int, default=24, help="Number of questions to request")
    parser.add_argument("--temperature", type=float, default=0.2, help="Sampling temperature")
    parser.add_argument("--timeout-sec", type=int, default=600, help="HTTP timeout in seconds")
    parser.add_argument(
        "--yaml-out",
        type=Path,
        default=Path("benchmarks/ollama_question_bank.yaml"),
        help="YAML output path",
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=Path("docs/verification/ollama_question_bank.md"),
        help="Markdown output path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    seed_paths = load_seed_paths(args.seed_benchmark)
    seed_blob = "\n".join(f"- {p}" for p in seed_paths[:48])

    system = (
        "You design practical benchmark questions for Unitree G1 documentation and code retrieval. "
        "Return strict JSON only."
    )
    user = (
        "Create a diverse question bank for testing an AI assistant on Unitree G1.\n"
        f"Generate exactly {args.count} items.\n"
        "Focus areas: sdk2, sdk2_python, dds services, ros2, sim2sim/sim2real, "
        "remote PC deployment, troubleshooting, repo coverage, verification status, and skills usage.\n"
        "Each item must include:\n"
        "- id (snake_case)\n"
        "- question (natural user question)\n"
        "- expected_path_patterns (1-2 likely path hints from the source list)\n"
        "- difficulty (easy|medium|hard)\n"
        "Return JSON schema:\n"
        "{ \"questions\": [ {\"id\": \"...\", \"question\": \"...\", \"expected_path_patterns\": [\"...\"], \"difficulty\": \"...\"} ] }\n\n"
        "Known source path hints:\n"
        f"{seed_blob}\n"
    )

    raw = call_chat(
        api_base=args.api_base,
        api_key=args.api_key,
        model=args.model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=args.temperature,
        timeout_sec=args.timeout_sec,
    )
    parsed = parse_model_json(raw)
    questions = parsed.get("questions", [])
    if not isinstance(questions, list):
        raise ValueError("`questions` must be a list")

    normalized: list[dict] = []
    used_ids: set[str] = set()
    for i, q in enumerate(questions, start=1):
        if not isinstance(q, dict):
            continue
        qid = normalize_id(str(q.get("id", "")), f"ollama_q_{i}")
        while qid in used_ids:
            qid = f"{qid}_{i}"
        used_ids.add(qid)
        question = str(q.get("question", "")).strip()
        if not question:
            continue
        patterns = [str(p).strip() for p in q.get("expected_path_patterns", []) if str(p).strip()]
        difficulty = str(q.get("difficulty", "medium")).strip().lower()
        if difficulty not in {"easy", "medium", "hard"}:
            difficulty = "medium"
        normalized.append(
            {
                "id": qid,
                "question": question,
                "expected_path_patterns": patterns[:2],
                "difficulty": difficulty,
                "generated_by": args.model,
                "reviewed_by": "codex",
            }
        )

    payload = {
        "version": 1,
        "generated_at_unix": int(time.time()),
        "model": args.model,
        "count": len(normalized),
        "questions": normalized,
    }

    args.yaml_out.parent.mkdir(parents=True, exist_ok=True)
    args.yaml_out.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    lines = [
        "# Ollama + Codex Question Bank",
        "",
        f"- Model: `{args.model}`",
        f"- Generated questions: {len(normalized)}",
        "",
        "| id | difficulty | question | expected_path_patterns |",
        "| --- | --- | --- | --- |",
    ]
    for item in normalized:
        pats = ", ".join(item["expected_path_patterns"])
        q = item["question"].replace("|", "/")
        lines.append(f"| {item['id']} | {item['difficulty']} | {q} | {pats} |")

    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[OK] Wrote YAML question bank: {args.yaml_out}")
    print(f"[OK] Wrote Markdown report: {args.md_out}")
    print(f"[SUMMARY] count={len(normalized)} model={args.model}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
