---
name: unitree-g1-expert
description: Ground Unitree G1 answers in local evidence from official Unitree docs and repositories. Use this skill for SDK2 usage, DDS/service interfaces, motion development, ROS/ROS2 integration, RL sim2sim/sim2real workflows, and onboard vs remote-PC deployment troubleshooting in this repository.
---

# Unitree G1 Expert

Use local indexed sources first, then provide a concise answer with explicit file/URL citations.

## Quick Workflow

1. Ensure local data is fresh:
   - Run `python3 scripts/discover_unitree_repos.py --include-all --update-manifest` for maximum repo coverage.
   - Run `python3 scripts/sync_sources.py` at repo root when sources may be stale.
   - Run `python3 scripts/sync_repo_mirrors.py` and `python3 scripts/download_repo_archives.py` for raw retention.
   - Run `python3 scripts/verify_g1_docs.py --update-manifest` to discover and verify G1 developer docs.
   - Run `python3 scripts/render_support_docs.py` when support pages are JS-rendered and text is missing.
   - Run `python3 scripts/build_knowledge_index.py` after sync.
   - Run `python3 scripts/build_coverage_report.py` before final high-confidence answers.
   - Run `python3 scripts/eval_retrieval.py --strict --fail-below 0.75` for regression checks.
2. Retrieve top local evidence:
   - Run `python3 scripts/query_index.py "<question>"`.
   - Optional model-eval gate: run `python3 scripts/eval_openai_compatible.py --strict --fail-below 0.70` when an OpenAI-compatible endpoint is configured.
3. Open and verify exact files for final grounding:
   - Prefer `docs/source-digests/*.md`, synced support pages, and README files in `data/repos/`.
4. Answer with:
   - clear recommendation
   - verified facts vs inference split
   - exact file paths and upstream URLs used

## Retrieval and Grounding Rules

1. Prioritize evidence in this order:
   - official support URLs from `sources/unitree_g1_sources.yaml`
   - official GitHub repositories from the same manifest
   - curated digests in `docs/source-digests/`
2. Mark statements as:
   - `Verified` when directly supported by a cited source
   - `Inference` when reasoned from architecture/constraints
3. If local index misses the answer, request a sync before guessing.
4. Always check `docs/verification/g1_docs_verification.md`, `docs/verification/repo_lock.md`, and `docs/verification/coverage_report.md` before claiming full docs coverage.

## Workflow Shortcuts

- For fast retrieval in this skill context:
  - Run `python3 skills/unitree-g1-expert/scripts/query_unitree.py "<question>"`.
- For deployment questions:
  - Open `docs/pipelines/deployment-onboard-vs-remote-pc.md`.
- For sim transfer questions:
  - Open `docs/pipelines/sim2sim-sim2real.md`.

## Reference Files

- [workflow.md](references/workflow.md)
- [source-priority.md](references/source-priority.md)
