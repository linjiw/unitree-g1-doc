# AGENTS

This repository is a local-first Unitree G1 knowledge base for both humans and AI agents.

## Prime Objective

Answer Unitree G1 questions with verifiable local evidence and source citations.

## Mandatory Workflow

1. Refresh sources when stale:
   - `python3 scripts/sync_sources.py`
2. For JS-heavy support pages:
   - `python3 scripts/verify_g1_docs.py --update-manifest`
   - `python3 scripts/build_knowledge_index.py`
   - `python3 scripts/build_coverage_report.py`
3. Retrieve evidence:
   - `python3 scripts/query_index.py "<question>" --format json`
4. Respond with:
   - direct answer
   - cited file paths/URLs
   - explicit `Verified` vs `Inference` labels

## Core Files for Agents

- Source manifest: `sources/unitree_g1_sources.yaml`
- Main index: `data/index/knowledge_index.jsonl`
- Verification report: `docs/verification/g1_docs_verification.md`
- Coverage report: `docs/verification/coverage_report.md`
- Skill instructions: `skills/unitree-g1-expert/SKILL.md`

## Reliability Rules

- Prefer official Unitree support docs and official Unitree GitHub repos.
- Never claim "fully complete forever" coverage. Upstream docs and repos can change.
- Use latest verification report timestamp before high-confidence claims.
- Use strict `--fail-on-error` for sync when you expect full direct access to all upstream sources.
- Use strict `--fail-on-error` on verification only when the network can access support pages without security blocking.
