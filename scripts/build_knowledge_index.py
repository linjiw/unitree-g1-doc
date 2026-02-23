#!/usr/bin/env python3
"""Build a local JSONL knowledge index from synced Unitree sources."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError as exc:  # pragma: no cover - runtime dependency check
    raise SystemExit(
        "Missing dependency: pyyaml. Install with `pip install pyyaml`."
    ) from exc

TEXT_EXTENSIONS = {
    ".md",
    ".markdown",
    ".txt",
    ".rst",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
    ".py",
    ".sh",
    ".bash",
    ".zsh",
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".ts",
    ".tsx",
    ".xml",
    ".launch",
    ".urdf",
    ".xacro",
    ".proto",
    ".cmake",
}

TEXT_FILENAMES = {
    "readme",
    "readme.md",
    "readme_zh.md",
    "license",
    "changelog.md",
}

EXCLUDED_DIRS = {
    ".git",
    "build",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "logs",
    "outputs",
}


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Manifest must be a mapping: {path}")
    return data


def strip_markdown(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.M)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.M)
    return re.sub(r"\s+", " ", text).strip()


def strip_html_text(raw_html: str) -> str:
    no_script = re.sub(r"(?is)<script.*?>.*?</script>", " ", raw_html)
    no_style = re.sub(r"(?is)<style.*?>.*?</style>", " ", no_script)
    no_tags = re.sub(r"(?s)<[^>]+>", " ", no_style)
    return re.sub(r"\s+", " ", html.unescape(no_tags)).strip()


def is_binary_file(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            chunk = f.read(2048)
        return b"\x00" in chunk
    except OSError:
        return True


def should_index_file(path: Path, max_file_bytes: int) -> bool:
    if not path.is_file():
        return False
    try:
        size = path.stat().st_size
    except OSError:
        return False
    if size <= 0 or size > max_file_bytes:
        return False
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        return not is_binary_file(path)

    lower_name = path.name.lower()
    if lower_name in TEXT_FILENAMES:
        return not is_binary_file(path)

    return False


def iter_repo_files(repo_root: Path, max_file_bytes: int) -> Iterable[Path]:
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if should_index_file(path, max_file_bytes):
            yield path


def chunk_text(text: str, chunk_chars: int, overlap_chars: int) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    if len(cleaned) <= chunk_chars:
        return [cleaned]

    chunks: list[str] = []
    step = max(chunk_chars - overlap_chars, 1)
    i = 0
    while i < len(cleaned):
        part = cleaned[i : i + chunk_chars].strip()
        if part:
            chunks.append(part)
        if i + chunk_chars >= len(cleaned):
            break
        i += step
    return chunks


def normalize_text_by_path(path: Path, text: str) -> str:
    if path.suffix.lower() in {".md", ".markdown"}:
        return strip_markdown(text)
    if path.suffix.lower() in {".html", ".htm"}:
        return strip_html_text(text)
    return re.sub(r"\s+", " ", text).strip()


def make_record(
    *,
    rec_id: str,
    title: str,
    source_type: str,
    text: str,
    path: str | None = None,
    url: str | None = None,
    tags: list[str] | None = None,
    rank: int | None = None,
    total_chunks: int | None = None,
) -> dict[str, Any]:
    digest = hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()
    payload: dict[str, Any] = {
        "id": rec_id,
        "title": title,
        "source_type": source_type,
        "path": path,
        "url": url,
        "tags": tags or [],
        "content": text,
        "content_chars": len(text),
        "sha1": digest,
    }
    if rank is not None:
        payload["chunk_rank"] = rank
    if total_chunks is not None:
        payload["chunk_total"] = total_chunks
    return payload


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build local Unitree knowledge index")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("sources/unitree_g1_sources.yaml"),
        help="Path to source manifest",
    )
    parser.add_argument(
        "--repos-dir",
        type=Path,
        default=Path("data/repos"),
        help="Directory containing cloned repositories",
    )
    parser.add_argument(
        "--support-dir",
        type=Path,
        default=Path("data/support_pages"),
        help="Directory containing support page snapshots",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=Path("docs"),
        help="Directory containing curated docs",
    )
    parser.add_argument(
        "--skills-dir",
        type=Path,
        default=Path("skills"),
        help="Directory containing skill definitions",
    )
    parser.add_argument(
        "--sources-dir",
        type=Path,
        default=Path("sources"),
        help="Directory containing source manifests/catalogs",
    )
    parser.add_argument(
        "--index-jsonl",
        type=Path,
        default=Path("data/index/knowledge_index.jsonl"),
        help="Output JSONL file",
    )
    parser.add_argument(
        "--index-markdown",
        type=Path,
        default=Path("data/index/knowledge_index.md"),
        help="Output markdown summary file",
    )
    parser.add_argument(
        "--index-meta",
        type=Path,
        default=Path("data/index/knowledge_index.meta.json"),
        help="Output metadata summary file",
    )
    parser.add_argument(
        "--max-file-bytes",
        type=int,
        default=250_000,
        help="Maximum file size to index",
    )
    parser.add_argument(
        "--chunk-chars",
        type=int,
        default=1600,
        help="Chunk size for large text files",
    )
    parser.add_argument(
        "--overlap-chars",
        type=int,
        default=220,
        help="Overlap between chunks",
    )
    return parser.parse_args()


def add_file_records(
    records: list[dict[str, Any]],
    path: Path,
    rec_prefix: str,
    source_type: str,
    tags: list[str],
    url: str | None,
    chunk_chars: int,
    overlap_chars: int,
) -> None:
    raw_text = path.read_text(encoding="utf-8", errors="replace")
    normalized = normalize_text_by_path(path, raw_text)
    chunks = chunk_text(normalized, chunk_chars, overlap_chars)
    if not chunks:
        return
    for idx, chunk in enumerate(chunks):
        rec_id = f"{rec_prefix}:chunk-{idx:04d}"
        records.append(
            make_record(
                rec_id=rec_id,
                title=path.name,
                source_type=source_type,
                text=chunk,
                path=str(path),
                url=url,
                tags=tags,
                rank=idx,
                total_chunks=len(chunks),
            )
        )


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest)
    records: list[dict[str, Any]] = []

    # Repositories: index all relevant text/code files, chunked.
    for repo in manifest.get("repos", []):
        name = str(repo["name"])
        repo_dir = args.repos_dir / name
        if not repo_dir.exists():
            continue

        repo_url = str(repo.get("url", ""))
        tags = list(repo.get("topics", [])) + [name]
        for file_path in iter_repo_files(repo_dir, args.max_file_bytes):
            rel = file_path.relative_to(repo_dir)
            rec_prefix = f"repo:{name}:{rel.as_posix()}"
            add_file_records(
                records=records,
                path=file_path,
                rec_prefix=rec_prefix,
                source_type="repo_file",
                tags=tags,
                url=repo_url,
                chunk_chars=args.chunk_chars,
                overlap_chars=args.overlap_chars,
            )

    # Support docs: prefer rendered text/html when available.
    for doc in manifest.get("support_docs", []):
        doc_id = str(doc["id"])
        html_path = args.support_dir / f"{doc_id}.html"
        rendered_txt = args.support_dir / f"{doc_id}.rendered.txt"
        rendered_html = args.support_dir / f"{doc_id}.rendered.html"
        rendered_meta = read_json(args.support_dir / f"{doc_id}.rendered.json")
        raw_meta = read_json(args.support_dir / f"{doc_id}.json")
        verification_status = str(
            rendered_meta.get("status")
            or raw_meta.get("status")
            or "unknown"
        )

        if not html_path.exists() and not rendered_txt.exists() and not rendered_html.exists():
            continue

        if rendered_txt.exists() and verification_status == "verified":
            text = rendered_txt.read_text(encoding="utf-8", errors="replace")
            source_path = rendered_txt
        elif rendered_html.exists() and verification_status == "verified":
            raw_html = rendered_html.read_text(encoding="utf-8", errors="replace")
            text = strip_html_text(raw_html)
            source_path = rendered_html
        else:
            raw_html = html_path.read_text(encoding="utf-8", errors="replace")
            text = strip_html_text(raw_html)
            source_path = html_path

        tags = list(doc.get("topics", [])) + ["support", verification_status]
        if verification_status != "verified" or len(text) < 60:
            text = (
                "UNVERIFIED SUPPORT PAGE. Raw content is unavailable or blocked in this "
                "environment. Use the source URL directly or re-run verification from an "
                "allowed network."
            )
            tags.append("support_unverified")

        chunks = chunk_text(text, args.chunk_chars, args.overlap_chars)
        for idx, chunk in enumerate(chunks):
            records.append(
                make_record(
                    rec_id=f"support:{doc_id}:chunk-{idx:04d}",
                    title=str(doc.get("title", doc_id)),
                    source_type="support_doc",
                    text=chunk,
                    path=str(source_path),
                    url=str(doc.get("url", "")),
                    tags=tags,
                    rank=idx,
                    total_chunks=len(chunks),
                )
            )

    # Curated docs and pipeline docs.
    if args.docs_dir.exists():
        for doc_path in sorted(args.docs_dir.rglob("*.md")):
            if doc_path.name.lower().startswith("readme"):
                continue
            rel = doc_path.relative_to(args.docs_dir).as_posix()
            add_file_records(
                records=records,
                path=doc_path,
                rec_prefix=f"doc:{rel}",
                source_type="curated_doc",
                tags=["doc", "curated"],
                url=None,
                chunk_chars=args.chunk_chars,
                overlap_chars=args.overlap_chars,
            )

    # Skill instructions as explicit agent-facing data.
    if args.skills_dir.exists():
        for skill_path in sorted(args.skills_dir.rglob("*.md")):
            rel = skill_path.relative_to(args.skills_dir).as_posix()
            add_file_records(
                records=records,
                path=skill_path,
                rec_prefix=f"skill:{rel}",
                source_type="skill_doc",
                tags=["skill", "agent"],
                url=None,
                chunk_chars=args.chunk_chars,
                overlap_chars=args.overlap_chars,
            )

    # Source manifests/catalogs.
    if args.sources_dir.exists():
        for source_path in sorted(args.sources_dir.rglob("*")):
            if source_path.suffix.lower() not in {".yaml", ".yml", ".json", ".md"}:
                continue
            if not source_path.is_file():
                continue
            rel = source_path.relative_to(args.sources_dir).as_posix()
            add_file_records(
                records=records,
                path=source_path,
                rec_prefix=f"source:{rel}",
                source_type="source_manifest",
                tags=["source", "manifest"],
                url=None,
                chunk_chars=args.chunk_chars,
                overlap_chars=args.overlap_chars,
            )

    args.index_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with args.index_jsonl.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    with args.index_markdown.open("w", encoding="utf-8") as f:
        f.write("# Unitree G1 Local Knowledge Index\n\n")
        f.write(f"- Records: {len(records)}\n\n")
        f.write("| ID | Type | Title | Tags | Path |\n")
        f.write("| --- | --- | --- | --- | --- |\n")
        for rec in records[:1000]:
            preview_tags = ",".join(rec.get("tags", []))
            path = rec.get("path", "") or ""
            f.write(
                f"| {rec['id']} | {rec['source_type']} | {rec['title']} | "
                f"{preview_tags} | {path} |\n"
            )

    stats_by_type: dict[str, int] = {}
    for rec in records:
        stats_by_type[rec["source_type"]] = stats_by_type.get(rec["source_type"], 0) + 1

    meta = {
        "records": len(records),
        "by_source_type": stats_by_type,
        "manifest": str(args.manifest),
        "repos_indexed": len(manifest.get("repos", [])),
        "support_docs_indexed": len(manifest.get("support_docs", [])),
        "max_file_bytes": args.max_file_bytes,
        "chunk_chars": args.chunk_chars,
        "overlap_chars": args.overlap_chars,
    }
    args.index_meta.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"[OK] Wrote index JSONL: {args.index_jsonl}")
    print(f"[OK] Wrote index summary: {args.index_markdown}")
    print(f"[OK] Wrote index meta: {args.index_meta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
