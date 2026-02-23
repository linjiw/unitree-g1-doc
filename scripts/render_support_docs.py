#!/usr/bin/env python3
"""Render JS-heavy Unitree support pages with Playwright and save text snapshots."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

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


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Manifest must be a mapping: {path}")
    return data


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render support.unitree.com pages via Playwright")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("sources/unitree_g1_sources.yaml"),
        help="Path to source manifest",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/support_pages"),
        help="Output directory for rendered page text/html/json",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=60000,
        help="Navigation timeout in milliseconds",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for doc in manifest.get("support_docs", []):
            doc_id = str(doc["id"])
            url = str(doc["url"])
            html_path = args.out_dir / f"{doc_id}.rendered.html"
            txt_path = args.out_dir / f"{doc_id}.rendered.txt"
            meta_path = args.out_dir / f"{doc_id}.rendered.json"

            print(f"[RENDER] {doc_id} -> {url}")
            record: dict[str, Any] = {
                "id": doc_id,
                "url": url,
                "status": "unknown",
                "topics": list(doc.get("topics", [])),
                "render_time_unix": int(time.time()),
            }
            try:
                page.goto(url, wait_until="networkidle", timeout=args.timeout_ms)
                page.wait_for_timeout(2500)
                html_text = page.content()
                body_text = clean_text(page.locator("body").inner_text())
                title = page.title()

                html_path.write_text(html_text, encoding="utf-8")
                txt_path.write_text(body_text, encoding="utf-8")
                record.update(
                    {
                        "status": "rendered",
                        "title": title,
                        "text_chars": len(body_text),
                        "html_file": str(html_path),
                        "text_file": str(txt_path),
                    }
                )
            except PlaywrightTimeoutError:
                record.update({"status": "error", "error": "playwright timeout"})
            except Exception as exc:  # pragma: no cover - defensive runtime logging
                record.update({"status": "error", "error": str(exc)})

            meta_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
