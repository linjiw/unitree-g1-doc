#!/usr/bin/env python3
"""Discover and verify Unitree G1 developer docs from support.unitree.com."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

try:
    import yaml
except ImportError as exc:  # pragma: no cover - runtime dependency check
    raise SystemExit(
        "Missing dependency: pyyaml. Install with `pip install pyyaml`."
    ) from exc

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ImportError as exc:  # pragma: no cover - runtime dependency check
    raise SystemExit(
        "Missing dependency: playwright. Install with `pip install playwright` and run `playwright install chromium`."
    ) from exc


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    clean_path = re.sub(r"/+", "/", parsed.path)
    return f"{parsed.scheme}://{parsed.netloc}{clean_path}"


def slug_from_url(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if not path:
        return "g1-developer-root"
    # Keep the significant suffix after G1_developer
    if "/G1_developer/" in path:
        suffix = path.split("/G1_developer/", 1)[1]
    else:
        suffix = path.replace("/", "-")
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", suffix).strip("-").lower()
    return slug or "g1-developer-root"


def infer_topics(url: str, title: str) -> list[str]:
    text = f"{url} {title}".lower()
    topics = ["g1"]
    for key in ["sdk", "dds", "motion", "simulation", "sim2real", "policy", "quick", "deploy"]:
        if key in text and key not in topics:
            topics.append(key)
    return topics


def is_access_blocked(text: str, title: str) -> bool:
    hay = f"{title} {text}".lower()
    markers = [
        "restricted access",
        "blocked you from further access",
        "edgeone",
        "security policy of this website",
        "request id:",
        "protected by tencent cloud",
    ]
    return any(marker in hay for marker in markers)


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Manifest must be a mapping: {path}")
    return data


def discover_g1_urls(page: Any, root_url: str) -> list[str]:
    page.goto(root_url, wait_until="networkidle", timeout=90_000)
    page.wait_for_timeout(2500)

    hrefs = page.eval_on_selector_all(
        "a[href]",
        "elements => elements.map(el => el.getAttribute('href'))",
    )

    urls: set[str] = set()
    for href in hrefs:
        if not href:
            continue
        full = normalize_url(urljoin(root_url, href))
        if "/home/en/G1_developer/" not in full:
            continue
        if "#" in full:
            full = full.split("#", 1)[0]
        if "?" in full:
            full = full.split("?", 1)[0]
        urls.add(full)

    # Keep root url for verification context as well.
    urls.add(normalize_url(root_url))
    return sorted(urls)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover and verify Unitree G1 docs")
    parser.add_argument(
        "--root-url",
        default="https://support.unitree.com/home/en/G1_developer/",
        help="Root Unitree G1 developer docs URL",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("sources/unitree_g1_sources.yaml"),
        help="Manifest path",
    )
    parser.add_argument(
        "--support-dir",
        type=Path,
        default=Path("data/support_pages"),
        help="Output directory for rendered docs",
    )
    parser.add_argument(
        "--report-md",
        type=Path,
        default=Path("docs/verification/g1_docs_verification.md"),
        help="Verification markdown report path",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=Path("docs/verification/g1_docs_verification.json"),
        help="Verification JSON report path",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=90_000,
        help="Playwright navigation timeout in milliseconds",
    )
    parser.add_argument(
        "--min-text-chars",
        type=int,
        default=300,
        help="Minimum extracted text length to consider a page verified",
    )
    parser.add_argument(
        "--update-manifest",
        action="store_true",
        help="Merge discovered pages into the support_docs section",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit non-zero when any page fails verification",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.support_dir.mkdir(parents=True, exist_ok=True)
    args.report_md.parent.mkdir(parents=True, exist_ok=True)
    manifest_data = load_manifest(args.manifest)
    url_to_doc = {
        normalize_url(str(doc.get("url", "")).strip()): doc
        for doc in manifest_data.get("support_docs", [])
        if str(doc.get("url", "")).strip()
    }
    manifest_urls = {
        normalize_url(str(doc.get("url", "")).strip())
        for doc in manifest_data.get("support_docs", [])
        if str(doc.get("url", "")).strip()
    }

    results: list[dict[str, Any]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"[DISCOVER] Crawling root: {args.root_url}")
        discovered_urls = discover_g1_urls(page, args.root_url)
        merged_urls = sorted(set(discovered_urls) | manifest_urls)
        print(
            f"[DISCOVER] Found {len(discovered_urls)} URLs under /home/en/G1_developer/. "
            f"Using {len(merged_urls)} URLs after merging manifest entries."
        )

        for url in merged_urls:
            mapped = url_to_doc.get(url)
            slug = str(mapped.get("id", "")).strip() if isinstance(mapped, dict) else ""
            if not slug:
                slug = slug_from_url(url)
            html_path = args.support_dir / f"{slug}.rendered.html"
            txt_path = args.support_dir / f"{slug}.rendered.txt"
            meta_path = args.support_dir / f"{slug}.rendered.json"

            record: dict[str, Any] = {
                "id": slug,
                "url": url,
                "status": "unknown",
                "render_time_unix": int(time.time()),
            }

            try:
                page.goto(url, wait_until="networkidle", timeout=args.timeout_ms)
                page.wait_for_timeout(2000)
                html_text = page.content()
                body_text = re.sub(r"\s+", " ", page.locator("body").inner_text()).strip()
                title = page.title().strip()

                html_path.write_text(html_text, encoding="utf-8")
                txt_path.write_text(body_text, encoding="utf-8")

                blocked = is_access_blocked(body_text, title)
                verified = len(body_text) >= args.min_text_chars and not blocked
                record.update(
                    {
                        "status": "verified" if verified else ("blocked_access" if blocked else "needs_review"),
                        "title": title,
                        "text_chars": len(body_text),
                        "html_file": str(html_path),
                        "text_file": str(txt_path),
                        "topics": infer_topics(url, title),
                    }
                )
            except PlaywrightTimeoutError:
                record.update({"status": "error", "error": "playwright timeout"})
            except Exception as exc:  # pragma: no cover - defensive runtime logging
                record.update({"status": "error", "error": str(exc)})

            meta_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
            results.append(record)

        browser.close()

    verified = [r for r in results if r.get("status") == "verified"]
    needs_review = [r for r in results if r.get("status") == "needs_review"]
    errors = [r for r in results if r.get("status") == "error"]
    blocked = [r for r in results if r.get("status") == "blocked_access"]

    manifest_updates: dict[str, Any] | None = None
    if args.update_manifest:
        manifest = load_manifest(args.manifest)
        existing = {
            str(doc.get("url", "")).strip(): doc
            for doc in manifest.get("support_docs", [])
            if str(doc.get("url", "")).strip()
        }

        merged: dict[str, dict[str, Any]] = dict(existing)
        for rec in results:
            if not rec.get("url"):
                continue
            if rec["url"] in merged:
                doc = merged[rec["url"]]
                if rec.get("status") == "verified" and rec.get("title"):
                    doc["title"] = rec["title"]
                if rec.get("status") == "verified" and rec.get("topics"):
                    doc["topics"] = rec["topics"]
                continue
            merged[rec["url"]] = {
                "id": rec["id"],
                "title": rec.get("title", rec["id"])
                if rec.get("status") == "verified"
                else rec["id"],
                "url": rec["url"],
                "topics": rec.get("topics", ["g1"]),
                "priority": "core",
            }

        support_docs = sorted(merged.values(), key=lambda x: str(x["url"]))
        manifest["support_docs"] = support_docs
        manifest["updated_at"] = time.strftime("%Y-%m-%d")
        args.manifest.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

        manifest_updates = {
            "support_docs": len(support_docs),
        }

    report = {
        "root_url": args.root_url,
        "timestamp_unix": int(time.time()),
        "total_urls": len(results),
        "manifest_urls": len(manifest_urls),
        "verified": len(verified),
        "needs_review": len(needs_review),
        "errors": len(errors),
        "blocked_access": len(blocked),
        "results": results,
    }
    if manifest_updates:
        report["manifest_updates"] = manifest_updates

    args.report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines: list[str] = []
    lines.append("# G1 Docs Verification Report")
    lines.append("")
    lines.append(f"- Root URL: {args.root_url}")
    lines.append(f"- Total discovered URLs: {len(results)}")
    lines.append(f"- Verified pages: {len(verified)}")
    lines.append(f"- Needs review: {len(needs_review)}")
    lines.append(f"- Blocked by website security: {len(blocked)}")
    lines.append(f"- Errors: {len(errors)}")
    if manifest_updates:
        lines.append(f"- Manifest support_docs entries: {manifest_updates['support_docs']}")
    lines.append("")
    lines.append("| Status | ID | Title | URL | Text chars |")
    lines.append("| --- | --- | --- | --- | ---: |")
    for rec in results:
        lines.append(
            "| "
            f"{rec.get('status','')} | {rec.get('id','')} | {rec.get('title','')} | "
            f"{rec.get('url','')} | {rec.get('text_chars', 0)} |"
        )

    args.report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[OK] Wrote report JSON: {args.report_json}")
    print(f"[OK] Wrote report MD: {args.report_md}")
    print(
        f"[SUMMARY] total={len(results)} verified={len(verified)} "
        f"needs_review={len(needs_review)} blocked_access={len(blocked)} errors={len(errors)}"
    )

    if args.fail_on_error and (needs_review or blocked or errors):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
