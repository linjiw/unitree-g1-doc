# Architecture

This repo uses a repeatable three-stage pipeline:

1. `discover`: find additional Unitree G1-related repos and docs URLs.
2. `sync`: clone/pull Unitree repos and snapshot support URLs.
3. `verify`: browser-render and validate G1 docs coverage.
4. `index`: convert local sources into a single JSONL knowledge index.
5. `query`: answer questions by retrieving the best local evidence first.
6. `site`: export search payloads for GitHub Pages.

## Data Flow

```text
sources/unitree_g1_sources.yaml
    -> scripts/discover_unitree_repos.py
        -> sources/unitree_g1_sources.yaml (expanded repos)
    -> scripts/sync_sources.py
        -> data/repos/*
        -> data/support_pages/*.html + *.json
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
```

## Why This Design

- Keep raw upstream data out of git while preserving deterministic re-sync.
- Separate curated docs (`docs/`) from generated artifacts (`data/`).
- Make skill/MCP layers consume one normalized index instead of many formats.
