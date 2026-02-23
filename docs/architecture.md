# Architecture

This repo uses a repeatable max-coverage pipeline:

1. `discover`: find additional Unitree G1-related repos and docs URLs.
2. `sync`: clone/pull Unitree repos and snapshot support URLs.
3. `mirror`: maintain bare git mirrors for full raw history retention.
4. `archive`: download raw tarball snapshots with checksums.
5. `verify`: browser-render and validate G1 docs coverage.
6. `index`: convert local sources into a single JSONL knowledge index.
7. `query`: answer questions by retrieving the best local evidence first.
8. `site`: export search payloads for GitHub Pages.
9. `lock/report`: build repo lock and coverage reports.

## Data Flow

```text
sources/unitree_g1_sources.yaml
    -> scripts/discover_unitree_repos.py
        -> sources/unitree_g1_sources.yaml (expanded repos)
    -> scripts/sync_sources.py
        -> data/repos/*
        -> data/support_pages/*.html + *.json
    -> scripts/sync_repo_mirrors.py
        -> data/repo_mirrors/*.git
    -> scripts/download_repo_archives.py
        -> data/repo_archives/*.tar.gz
    -> scripts/verify_g1_docs.py
        -> docs/verification/g1_docs_verification.*
        -> data/support_pages/*.rendered.*
    -> scripts/render_support_docs.py (optional fallback)
    -> scripts/build_knowledge_index.py
        -> data/index/knowledge_index.jsonl
    -> scripts/query_index.py
        -> ranked local evidence for any Unitree question
    -> scripts/build_site.py
        -> site/data/search-index.json
    -> scripts/build_repo_lock.py + scripts/build_coverage_report.py
        -> docs/verification/repo_lock.*
        -> docs/verification/coverage_report.md
```

## Why This Design

- Keep raw upstream data out of git while preserving deterministic re-sync.
- Separate curated docs (`docs/`) from generated artifacts (`data/`).
- Make skill/MCP layers consume one normalized index instead of many formats.
