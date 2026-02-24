# AGENTS

This repository is designed to be a **Codex-first Unitree G1 workspace**.

## Prime Objective

Enable Codex (and similar coding agents) to answer Unitree G1 questions with high accuracy, local evidence, and explicit citations.

## Codex-First Success Criteria

1. Codex can run entirely inside this repo and find relevant evidence quickly.
2. Answers are grounded in local files first, then upstream URLs when needed.
3. Output clearly separates:
   - `Verified` facts (directly cited)
   - `Inference` (reasoned conclusions)
4. Benchmark pass rates remain above quality gates and improve over time.

## Domain Coverage Targets

The agent should be able to handle questions spanning:
- SDK2 and SDK2 Python usage
- DDS/service interfaces
- ROS2 examples and control pathways
- Sim2Sim/Sim2Real workflows
- Onboard vs remote-PC deployment
- Verification/coverage/repo-lock status
- Skill and workflow usage for grounded answers

## Mandatory Workflow

1. Refresh sources when stale:
   - `python3 scripts/discover_unitree_repos.py --include-all --update-manifest`
   - `python3 scripts/sync_sources.py`
   - `python3 scripts/sync_repo_mirrors.py`
   - `python3 scripts/download_repo_archives.py`
2. Verify/index curated + support docs:
   - `python3 scripts/verify_g1_docs.py --update-manifest`
   - `python3 scripts/build_knowledge_index.py`
   - `python3 scripts/build_repo_lock.py`
   - `python3 scripts/build_coverage_report.py`
3. Retrieve evidence:
   - `python3 scripts/query_index.py "<question>" --format json`
4. Run quality checks (periodic/CI):
   - `python3 scripts/eval_retrieval.py --strict --fail-below 0.75`
   - `python3 scripts/eval_openai_compatible.py --strict --fail-below 0.70` (when model endpoint is available)
   - `make eval-agent-ollama`
   - `make eval-retrieval-ollama-qbank`
   - `make eval-agent-ollama-qbank`
   - `make eval-retrieval-codex-stretch`
   - `make eval-agent-ollama-codex-stretch`
   - `make eval-retrieval-codex-hardneg`
   - `make eval-agent-ollama-codex-hardneg`
5. Respond with:
   - direct answer
   - exact cited file paths/URLs
   - explicit `Verified` and `Inference` sections

## Required Answer Contract

Every production answer should include:
1. **Answer**: concise recommendation or result.
2. **Verified**: bullet facts with citations.
3. **Inference**: assumptions or reasoning not directly stated in sources.
4. **Limitations**: missing evidence, blocked pages, stale artifacts, or uncertainty.

## Core Files for Agents

- Source manifest: `sources/unitree_g1_sources.yaml`
- Main index: `data/index/knowledge_index.jsonl`
- Verification report: `docs/verification/g1_docs_verification.md`
- Repo lock report: `docs/verification/repo_lock.md`
- Coverage report: `docs/verification/coverage_report.md`
- Skill instructions: `skills/unitree-g1-expert/SKILL.md`
- Eval playbook: `docs/verification/agent_eval_playbook.md`
- Codex experiment plan: `docs/verification/codex_agent_experiments.md`

## Reliability Rules

- Prefer official Unitree support docs and official Unitree GitHub repos.
- Never claim permanent/full coverage; upstream docs and repos can change.
- Use latest verification timestamps before high-confidence claims.
- Use strict `--fail-on-error` only when full upstream network access is expected.
- If support pages are blocked, explicitly state this and rely on local mirror/index evidence.
- If retrieval misses expected evidence, refresh and rebuild index before answering from memory.
