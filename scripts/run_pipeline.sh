#!/usr/bin/env bash
set -euo pipefail

python3 scripts/sync_sources.py "$@"
if [[ "${VERIFY_G1_DOCS:-1}" == "1" ]]; then
  python3 scripts/verify_g1_docs.py --update-manifest
fi
if [[ "${RENDER_SUPPORT:-0}" == "1" ]]; then
  python3 scripts/render_support_docs.py
fi
python3 scripts/build_knowledge_index.py
if [[ "${BUILD_SITE:-1}" == "1" ]]; then
  python3 scripts/build_site.py
fi
python3 scripts/build_repo_lock.py
python3 scripts/build_coverage_report.py
