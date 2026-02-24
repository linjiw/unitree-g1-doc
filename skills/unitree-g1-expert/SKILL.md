---
name: unitree-g1-expert
description: Ground Unitree G1 answers in local evidence from official Unitree docs and repositories. Use this skill for SDK2 usage, DDS/service interfaces, motion development, ROS/ROS2 integration, RL sim2sim/sim2real workflows, and onboard vs remote-PC deployment troubleshooting in this repository.
---

# Unitree G1 Expert

Use this skill to make Codex effective inside this repository: retrieve local evidence first, then answer with explicit citations and `Verified` vs `Inference`.

## Codex Runtime Intent

When Codex receives a Unitree G1 question, it should:
1. Determine intent type:
   - usage/how-to
   - architecture/workflow
   - verification/status
   - script/command ownership
2. Retrieve local evidence from index.
3. Open top candidate files and verify exact statements.
4. Answer with explicit source paths and confidence boundaries.

## Mandatory Workflow

1. Ensure data freshness:
   - `python3 scripts/discover_unitree_repos.py --include-all --update-manifest`
   - `python3 scripts/sync_sources.py`
   - `python3 scripts/sync_repo_mirrors.py`
   - `python3 scripts/download_repo_archives.py`
   - `python3 scripts/verify_g1_docs.py --update-manifest`
   - `python3 scripts/build_knowledge_index.py`
   - `python3 scripts/build_repo_lock.py`
   - `python3 scripts/build_coverage_report.py`
2. Retrieve evidence:
   - `python3 scripts/query_index.py "<question>" --format json`
3. Validate quality periodically:
   - `make eval-retrieval`
   - `make eval-agent-ollama`
   - `make eval-retrieval-ollama-qbank`
   - `make eval-agent-ollama-qbank`
   - `make eval-retrieval-codex-stretch`
   - `make eval-agent-ollama-codex-stretch`

## Retrieval and Grounding Rules

1. Prioritize evidence in this order:
   - official support URLs from `sources/unitree_g1_sources.yaml`
   - official GitHub repositories from the same manifest
   - curated digests in `docs/source-digests/`
2. Mark statements as:
   - `Verified` when directly supported by a cited source
   - `Inference` when reasoned from architecture/constraints
3. Never answer from memory when retrieval misses expected evidence.
4. If local index misses the answer, run refresh/index steps before guessing.
5. Always check `docs/verification/g1_docs_verification.md`, `docs/verification/repo_lock.md`, and `docs/verification/coverage_report.md` before claiming full docs coverage.

## Codex Answer Template

Use this structure for user-facing answers:
1. `Answer`: direct recommendation.
2. `Verified`: concrete facts with exact local paths/URLs.
3. `Inference`: reasoning not literally quoted from sources.
4. `Limitations`: blocked sources, stale index, unresolved ambiguity.

## Failure Handling

- If support docs are `blocked_access`, say so explicitly and fall back to local mirrors/curated docs.
- If benchmarks regress below gate, do not claim "best quality"; call out failed case IDs.
- If question is outside G1 scope, say out-of-scope and provide nearest grounded pointers.

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
