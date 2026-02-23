#!/usr/bin/env bash
set -euo pipefail

python3 scripts/discover_unitree_repos.py --include-all --update-manifest
python3 scripts/sync_sources.py
python3 scripts/verify_g1_docs.py --update-manifest || true
python3 scripts/build_knowledge_index.py
python3 scripts/build_site.py
python3 scripts/build_repo_lock.py
python3 scripts/build_coverage_report.py

echo "[OK] Bootstrap complete. See docs/verification/coverage_report.md"
