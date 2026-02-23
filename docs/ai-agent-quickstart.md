# AI Agent Quickstart

## Goal

Give any AI agent a deterministic path to answer Unitree G1 questions with local evidence.

## Minimal Steps

1. Read [AGENTS.md](/Users/linji/projects/unitree-g1-doc/AGENTS.md).
2. Refresh and verify data:
   - `python3 scripts/sync_sources.py`
   - `python3 scripts/verify_g1_docs.py --update-manifest`
   - `python3 scripts/build_knowledge_index.py`
   - `python3 scripts/build_coverage_report.py`
3. Retrieve evidence:
   - `python3 scripts/query_index.py "<question>" --format json`
4. Draft answer with:
   - direct recommendation
   - cited local files + upstream URL
   - `Verified` / `Inference` sections

## Grounding Priority

1. `support.unitree.com/home/en/G1_developer/*`
2. `github.com/unitreerobotics/*` repos
3. This repo's curated docs and skills

## Required Citations

- Local file path for every major claim.
- Upstream URL when source is external.
- If verification shows `blocked_access`, state that official support pages could not be fully validated from the current network.
- Use strict `--fail-on-error` only when full upstream network access is available.
