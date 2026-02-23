#!/usr/bin/env bash
set -euo pipefail

# Max-coverage collection pipeline for Unitree knowledge retention.
# Usage:
#   bash scripts/max_collect.sh
# Tunables:
#   INCLUDE_ARCHIVED=1      include archived repos in manifest selection
#   FULL_HISTORY=1          sync full git history in working clones
#   DOWNLOAD_ARCHIVES=1     download codeload tar.gz archives for all repos
#   SYNC_MIRRORS=1          sync bare git mirrors for all repos

INCLUDE_ARCHIVED=${INCLUDE_ARCHIVED:-0}
FULL_HISTORY=${FULL_HISTORY:-0}
DOWNLOAD_ARCHIVES=${DOWNLOAD_ARCHIVES:-1}
SYNC_MIRRORS=${SYNC_MIRRORS:-1}

DISCOVER_ARGS=(--include-all --update-manifest)
if [[ "$INCLUDE_ARCHIVED" == "1" ]]; then
  DISCOVER_ARGS+=(--include-archived)
fi

SYNC_ARGS=()
if [[ "$FULL_HISTORY" == "1" ]]; then
  SYNC_ARGS+=(--full-history)
fi

echo "[STEP] Discover all Unitree org repos"
python3 scripts/discover_unitree_repos.py "${DISCOVER_ARGS[@]}"

echo "[STEP] Sync working clones"
python3 scripts/sync_sources.py "${SYNC_ARGS[@]}"

if [[ "$SYNC_MIRRORS" == "1" ]]; then
  echo "[STEP] Sync bare mirrors"
  python3 scripts/sync_repo_mirrors.py
fi

if [[ "$DOWNLOAD_ARCHIVES" == "1" ]]; then
  echo "[STEP] Download tarball archives"
  python3 scripts/download_repo_archives.py
fi

echo "[STEP] Verify G1 support docs (best effort)"
python3 scripts/verify_g1_docs.py --update-manifest || true

echo "[STEP] Build index/site/reports"
python3 scripts/build_knowledge_index.py
python3 scripts/build_site.py
python3 scripts/build_repo_lock.py
python3 scripts/build_coverage_report.py

echo "[OK] Max collection complete"
