# Codex Agent Experiments

## Goal

Make this repository the best workspace for Codex-style coding agents to answer Unitree G1 questions with grounded citations.

## What We Are Measuring

1. Retrieval quality: can top local results include the expected evidence paths?
2. Agent source-selection quality: can the model select the right files from candidates?
3. Grounding behavior: are answers structured as `Verified` vs `Inference` with citations?
4. Reliability awareness: does the agent correctly report blocked pages / coverage limits?

## Benchmark Tracks

### 1) Baseline Regression

- Benchmark: `benchmarks/retrieval_benchmark.yaml`
- Commands:
  - `make eval-retrieval`
  - `make eval-agent-ollama`
- Gates:
  - Retriever: `>= 0.75`
  - Agent: `>= 0.70`

### 2) Curated Ollama+Codex Set

- Benchmark: `benchmarks/ollama_question_benchmark.yaml`
- Commands:
  - `make eval-retrieval-ollama-qbank`
  - `make eval-agent-ollama-qbank`
- Gates:
  - Retriever: `>= 0.70`
  - Agent: `>= 0.60`

### 3) Codex Stretch Set

- Benchmark: `benchmarks/codex_agent_stretch_benchmark.yaml`
- Commands:
  - `make eval-retrieval-codex-stretch`
  - `make eval-agent-ollama-codex-stretch`
- Intent:
  - hard operational questions (workflow/commands/verification constraints)
  - codex-specific behavior (answer contract, source priority, reliability caveats)
  - repo-internal navigation (scripts/docs/site payload relationships)
- Initial gates:
  - Retriever: `>= 0.70`
  - Agent: `>= 0.60`

### 4) Codex Hard-Negative Set

- Benchmark: `benchmarks/codex_agent_hardneg_benchmark.yaml`
- Commands:
  - `make eval-retrieval-codex-hardneg`
  - `make eval-agent-ollama-codex-hardneg`
- Intent:
  - detect ranking leakage/noise with `forbidden_path_patterns`
  - force multi-evidence retrieval with `require_all_expected`
  - validate robustness beyond top-1 keyword matches
- Initial gates:
  - Retriever: `>= 0.75`
  - Agent: `>= 0.65`

## Outputs

- `docs/verification/retrieval_eval.md`
- `docs/verification/agent_eval.md`
- `docs/verification/ollama_question_retrieval_eval.md`
- `docs/verification/ollama_agent_eval.md`
- `docs/verification/codex_stretch_retrieval_eval.md`
- `docs/verification/codex_stretch_agent_eval.md`

## Current Baseline (February 24, 2026)

- Codex stretch retriever: `18/18` (`100.00%`) on `benchmarks/codex_agent_stretch_benchmark.yaml`
- Codex hard-negative retriever: `7/8` (`87.50%`) on `benchmarks/codex_agent_hardneg_benchmark.yaml`
- Baseline retriever: `9/12` (`75.00%`) on `benchmarks/retrieval_benchmark.yaml`
- Codex stretch agent: unavailable in this run (model endpoint blocked in sandbox)

This indicates stretch retrieval is now strong, while hard-negative and agent tracks remain the key improvement frontier.

## What We Changed (Optimization Pass)

1. Expanded index coverage for Codex-facing files:
   - root governance files (`AGENTS.md`, `README.md`, `Makefile`)
   - operational scripts in `scripts/`
   - benchmark specs in `benchmarks/`
   - website methodology/example files in `site/`
2. Added shared retrieval scoring with:
   - stopword handling and intent-aware boosts
   - path-level weighting (scripts/docs/sources/site priorities)
   - noise penalties for third-party/vendor paths
3. Improved evaluation validity:
   - benchmark leakage guard: benchmark YAML excluded unless explicitly expected
   - retrieval path deduplication (chunk duplicates no longer consume top-k)
   - optional hard-negative checks (`forbidden_path_patterns`, `require_all_expected`)

## Experiment Loop

1. Run all benchmark tracks.
2. Extract failed case IDs from JSON outputs.
3. Classify failures:
   - retrieval miss
   - ranking noise
   - model selection miss
   - weak/ambiguous expected patterns
4. Apply focused repo improvements:
   - improve docs/skill wording
   - add missing digests
   - tighten AGENTS workflow language
   - enrich benchmark questions
   - reduce retrieval noise from unrelated large repo files
5. Re-run and compare pass-rate deltas.

## Quality Discipline

- Do not claim "handles any question" unless all benchmark tracks pass and out-of-scope handling is explicit.
- Treat support-page blocking as a first-class reliability signal.
- Prefer transparent limitations over overconfident answers.

## Next Optimization Plan

1. Lift baseline retriever from `75%` to `>80%` by improving non-Codex generic query coverage.
2. Raise hard-negative retriever from `87.5%` to `>90%`, especially site payload/script co-retrieval.
3. Run agent benchmarks on a reachable local endpoint (Ollama or compatible server) and track precision/recall deltas.
4. Add adversarial cases where distractor files share tokens but wrong intent, then gate on forbidden-hit limits.
