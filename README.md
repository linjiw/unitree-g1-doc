# Unitree G1 Knowledge Hub

A local-first repository to collect, verify, index, and search Unitree G1 documentation and code.

## What This Repo Solves

- Keep official Unitree G1 docs and code references synchronized locally.
- Build an AI-friendly knowledge index with file-level citations.
- Provide a repeatable workflow for SDK, DDS, sim2sim/sim2real, and deployment questions.
- Publish a searchable demo website via GitHub Pages.

## Repository Map

```text
AGENTS.md                        # Agent operating contract
sources/unitree_g1_sources.yaml  # Canonical source manifest
sources/unitree_org_repo_catalog.json  # Full org repo catalog snapshot
scripts/                         # Sync, verify, index, query, and site build tools
docs/                            # Human docs, pipeline guides, verification reports
skills/unitree-g1-expert/        # Reusable Codex skill
site/                            # GitHub Pages demo site
data/                            # Generated artifacts (repos, mirrors, archives, docs snapshots, index)
```

## Quick Start (Human)

One-command bootstrap:

```bash
bash scripts/bootstrap.sh
```

Maximum collection mode (all org repos + mirrors + archives):

```bash
bash scripts/max_collect.sh
```

1. Install base dependencies:

```bash
pip install -r requirements.txt
```

2. Optional for JS-rendered Unitree docs:

```bash
pip install -r requirements-optional.txt
playwright install chromium
```

3. Discover, sync, verify, index:

```bash
python3 scripts/discover_unitree_repos.py --update-manifest
python3 scripts/sync_sources.py
python3 scripts/verify_g1_docs.py --update-manifest
python3 scripts/build_knowledge_index.py
python3 scripts/build_repo_lock.py
python3 scripts/build_coverage_report.py
```

4. Ask a question:

```bash
python3 scripts/query_index.py "how to deploy g1 policy on remote pc" --top-k 10
```

5. Build/update GitHub Pages data:

```bash
python3 scripts/build_site.py
```

## Quick Start (AI Agents)

1. Read [AGENTS.md](/Users/linji/projects/unitree-g1-doc/AGENTS.md).
2. Use [skills/unitree-g1-expert/SKILL.md](/Users/linji/projects/unitree-g1-doc/skills/unitree-g1-expert/SKILL.md).
3. Query [data/index/knowledge_index.jsonl](/Users/linji/projects/unitree-g1-doc/data/index/knowledge_index.jsonl) via `scripts/query_index.py`.
4. Ground answers with [docs/verification/g1_docs_verification.md](/Users/linji/projects/unitree-g1-doc/docs/verification/g1_docs_verification.md).

## Demo Website (GitHub Pages)

- Local preview entry: [site/index.html](/Users/linji/projects/unitree-g1-doc/site/index.html)
- Deploy workflow: [.github/workflows/pages.yml](/Users/linji/projects/unitree-g1-doc/.github/workflows/pages.yml)
- Site data payloads:
  - `site/data/search-index.json`
  - `site/data/overview.json`

## Core Commands

```bash
make discover-repos
make sync
make sync-strict
make sync-full
make verify-g1-docs
make verify-g1-docs-strict
make mirrors
make archives
make repo-lock
make max-collect
make index
make query q="g1 dds interface"
make site
```

## Important Documents

- Architecture: [docs/architecture.md](/Users/linji/projects/unitree-g1-doc/docs/architecture.md)
- Human quickstart: [docs/human-quickstart.md](/Users/linji/projects/unitree-g1-doc/docs/human-quickstart.md)
- AI quickstart: [docs/ai-agent-quickstart.md](/Users/linji/projects/unitree-g1-doc/docs/ai-agent-quickstart.md)
- GitHub Pages guide: [docs/github-pages.md](/Users/linji/projects/unitree-g1-doc/docs/github-pages.md)
- Source map: [docs/source-map.md](/Users/linji/projects/unitree-g1-doc/docs/source-map.md)
- Verification report: [docs/verification/g1_docs_verification.md](/Users/linji/projects/unitree-g1-doc/docs/verification/g1_docs_verification.md)
- Repo lock report: [docs/verification/repo_lock.md](/Users/linji/projects/unitree-g1-doc/docs/verification/repo_lock.md)
- Coverage report: [docs/verification/coverage_report.md](/Users/linji/projects/unitree-g1-doc/docs/verification/coverage_report.md)

## Scope and Completeness Notes

- This repo can continuously keep coverage high, but no static snapshot can guarantee forever-complete coverage because upstream Unitree docs/repos may change.
- Use `discover_unitree_repos.py --include-all`, mirror/archive sync, and `verify_g1_docs.py` before claiming complete coverage.
- For strict checks in CI, use `--fail-on-error` flags.
- If Unitree support pages are blocked by upstream security controls from your network, the verification report will mark URLs as `blocked_access` and fail strict verification.

## Current Verification Status

As of **February 23, 2026**, repository coverage is synchronized for discovered Unitree repos, but official support pages under `/home/en/G1_developer/` are currently blocked by Tencent EdgeOne from this environment during browser rendering. See [coverage_report.md](/Users/linji/projects/unitree-g1-doc/docs/verification/coverage_report.md) for exact counts.
