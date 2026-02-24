#!/usr/bin/env python3
"""Shared lexical retrieval scoring for query and evaluation scripts."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable

TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "do",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "our",
    "should",
    "that",
    "the",
    "this",
    "to",
    "use",
    "we",
    "what",
    "where",
    "which",
    "with",
}

NOISE_PATH_HINTS = {
    "/thirdparty/",
    "/third-party/",
    "/extern/",
    "/external/",
    "/vendor/",
    "/deps/",
    "/.github/",
    "/wayland/",
    "/glfw/",
}

CODEX_HINTS = {
    "codex",
    "agent",
    "agents",
    "verified",
    "inference",
    "skill",
    "skills",
    "answer",
    "answers",
    "contract",
    "priority",
}

PIPELINE_HINTS = {
    "command",
    "commands",
    "script",
    "scripts",
    "refresh",
    "sync",
    "index",
    "pipeline",
    "query",
}

BENCHMARK_HINTS = {
    "benchmark",
    "benchmarks",
    "eval",
    "evaluation",
    "experiment",
    "experiments",
    "stretch",
    "design",
    "documented",
    "question",
    "questions",
    "threshold",
    "thresholds",
}

SITE_HINTS = {
    "site",
    "website",
    "page",
    "pages",
    "html",
    "examples",
    "example",
    "methodology",
    "payload",
}

VERIFICATION_HINTS = {
    "verify",
    "verification",
    "coverage",
    "blocked",
    "lock",
    "status",
}

CODE_EXAMPLE_HINTS = {
    "source",
    "file",
    "files",
    "example",
    "examples",
    "ros2",
    "cpp",
    "python",
    "low",
    "level",
}

MANIFEST_HINTS = {
    "manifest",
    "catalog",
    "snapshot",
    "scope",
}

SIM2REAL_HINTS = {
    "sim2sim",
    "sim2real",
    "simulation",
    "real",
    "stages",
    "stage",
}

SOURCE_BOOST = {
    "support_doc": 1.40,
    "curated_doc": 1.30,
    "skill_doc": 1.45,
    "source_manifest": 1.10,
    "repo_file": 0.95,
    "project_doc": 1.55,
    "project_script": 1.35,
    "benchmark_spec": 1.30,
    "site_doc": 1.20,
    "site_data": 1.20,
}


@dataclass
class Match:
    score: float
    record: dict[str, Any]


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def normalize_query_tokens(query: str) -> list[str]:
    raw = tokenize(query)
    if not raw:
        return []
    filtered = [tok for tok in raw if len(tok) > 1 and tok not in STOPWORDS]
    if filtered:
        return filtered
    fallback = [tok for tok in raw if len(tok) > 1]
    return fallback or raw


def classify_query_intent(query_tokens: list[str]) -> set[str]:
    token_set = set(query_tokens)
    intents: set[str] = set()
    if token_set & CODEX_HINTS:
        intents.add("codex")
    if token_set & PIPELINE_HINTS:
        intents.add("pipeline")
    if token_set & BENCHMARK_HINTS:
        intents.add("benchmark")
    if token_set & SITE_HINTS:
        intents.add("site")
    if token_set & VERIFICATION_HINTS:
        intents.add("verification")
    if token_set & CODE_EXAMPLE_HINTS:
        intents.add("code_example")
    if token_set & MANIFEST_HINTS:
        intents.add("manifest")
    if token_set & SIM2REAL_HINTS:
        intents.add("sim2real")
    return intents


def _path_has_noise(path: str, title: str) -> bool:
    if title in {"license", "license.txt", "copying"}:
        return True
    path_norm = f"/{path.strip('/')}/"
    if any(hint in path_norm for hint in NOISE_PATH_HINTS):
        return True
    return path.endswith("/license") or path.endswith("/license.txt")


def score_record(
    *,
    query_tokens: list[str],
    query_intents: set[str],
    record: dict[str, Any],
) -> float:
    if not query_tokens:
        return 0.0

    content = str(record.get("content", "")).lower()
    title = str(record.get("title", "")).lower()
    tags = " ".join(str(item) for item in record.get("tags", [])).lower()
    path = str(record.get("path", "")).lower()
    source_type = str(record.get("source_type", "")).lower()

    if not content and not title and not path:
        return 0.0

    content_tokens = tokenize(content)
    title_tokens = tokenize(title)
    tag_tokens = tokenize(tags)
    path_tokens = tokenize(path)
    if not content_tokens and not title_tokens and not path_tokens:
        return 0.0

    query_set = set(query_tokens)
    if not query_set:
        return 0.0

    content_set = set(content_tokens)
    title_set = set(title_tokens)
    tag_set = set(tag_tokens)
    path_set = set(path_tokens)

    overlap_all = query_set & (content_set | title_set | tag_set | path_set)
    if not overlap_all:
        return 0.0

    coverage = len(overlap_all) / max(len(query_set), 1)
    path_overlap = query_set & path_set
    path_coverage = len(path_overlap) / max(len(query_set), 1)

    content_count = Counter(content_tokens)
    title_count = Counter(title_tokens)
    tag_count = Counter(tag_tokens)
    path_count = Counter(path_tokens)

    content_hits = sum(min(content_count.get(tok, 0), 5) for tok in query_set)
    title_hits = sum(min(title_count.get(tok, 0), 3) for tok in query_set)
    tag_hits = sum(min(tag_count.get(tok, 0), 2) for tok in query_set)
    path_hits = sum(min(path_count.get(tok, 0), 3) for tok in query_set)

    phrase_bonus = 0.0
    phrase = " ".join(query_tokens[:3])
    if phrase:
        if phrase in content:
            phrase_bonus += 1.5
        if phrase in path:
            phrase_bonus += 2.0

    raw_score = (
        content_hits
        + (title_hits * 3.1)
        + (tag_hits * 2.4)
        + (path_hits * 2.8)
        + (coverage * 7.0)
        + (path_coverage * 4.0)
        + phrase_bonus
    )

    source_boost = SOURCE_BOOST.get(source_type, 1.0)
    record_tags = {str(tag).lower() for tag in record.get("tags", [])}
    if "support_unverified" in record_tags:
        source_boost *= 0.35

    path_boost = 1.0
    if path == "agents.md":
        path_boost *= 2.0
    elif path.startswith("skills/unitree-g1-expert"):
        path_boost *= 1.7
    elif path.startswith("docs/verification"):
        path_boost *= 1.35
    elif path.startswith("scripts/"):
        path_boost *= 1.30
    elif path.startswith("benchmarks/"):
        path_boost *= 1.25
    elif path.startswith("site/"):
        path_boost *= 1.20
    elif path.startswith("sources/"):
        path_boost *= 1.25

    intent_boost = 1.0
    if "codex" in query_intents:
        if path == "agents.md" or path.startswith("skills/unitree-g1-expert"):
            intent_boost *= 1.6
        elif path.startswith("scripts/") or path.startswith("docs/verification"):
            intent_boost *= 1.25
        elif source_type == "repo_file":
            intent_boost *= 0.78

    if "pipeline" in query_intents:
        if path.startswith("scripts/"):
            intent_boost *= 1.5
        elif path.startswith("docs/pipelines"):
            intent_boost *= 1.3

    if "benchmark" in query_intents:
        if path.startswith("benchmarks/"):
            intent_boost *= 1.5
        elif path.startswith("docs/verification"):
            intent_boost *= 1.3
        if path == "agents.md" or path.startswith("skills/unitree-g1-expert"):
            intent_boost *= 0.70

    if "site" in query_intents:
        if path.startswith("site/"):
            intent_boost *= 1.8
        elif source_type == "repo_file":
            intent_boost *= 0.75

    if "verification" in query_intents and path.startswith("docs/verification"):
        intent_boost *= 1.4

    if "code_example" in query_intents:
        if path.startswith("data/repos/"):
            intent_boost *= 1.7
        elif path.startswith("skills/"):
            intent_boost *= 0.80

    if "manifest" in query_intents:
        if path.startswith("sources/") or source_type == "source_manifest":
            intent_boost *= 1.9
        elif path.startswith("scripts/"):
            intent_boost *= 0.90

    if "sim2real" in query_intents and path.startswith("docs/pipelines/"):
        intent_boost *= 1.6

    if source_type == "benchmark_spec" and "benchmark" not in query_intents:
        intent_boost *= 0.40

    if source_type == "site_data" and "site" in query_intents:
        intent_boost *= 1.5

    token_set = set(query_tokens)
    if {"ros2", "low", "level"} & token_set and path.startswith("data/repos/unitree_ros2/"):
        intent_boost *= 1.9

    if {"payload", "website", "site"} & token_set:
        if path == "site/data/benchmark_examples.json":
            intent_boost *= 2.4
        elif path == "scripts/build_site.py":
            intent_boost *= 1.9

    if {"catalog", "manifest"} & token_set and path.startswith("sources/"):
        intent_boost *= 2.0

    noise_penalty = 1.0
    if _path_has_noise(path, title):
        noise_penalty *= 0.25

    if len(query_set) >= 4 and coverage < 0.20:
        noise_penalty *= 0.55

    return raw_score * source_boost * path_boost * intent_boost * noise_penalty


def rank_records(
    *,
    records: Iterable[dict[str, Any]],
    query: str,
    top_k: int,
    source_filters: set[str] | None = None,
) -> list[Match]:
    query_tokens = normalize_query_tokens(query)
    intents = classify_query_intent(query_tokens)

    ranked: list[Match] = []
    for record in records:
        if source_filters and str(record.get("source_type", "")) not in source_filters:
            continue
        score = score_record(
            query_tokens=query_tokens,
            query_intents=intents,
            record=record,
        )
        if score > 0:
            ranked.append(Match(score=score, record=record))

    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked[:top_k]
