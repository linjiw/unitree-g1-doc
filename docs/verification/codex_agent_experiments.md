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

## Outputs

- `docs/verification/retrieval_eval.md`
- `docs/verification/agent_eval.md`
- `docs/verification/ollama_question_retrieval_eval.md`
- `docs/verification/ollama_agent_eval.md`
- `docs/verification/codex_stretch_retrieval_eval.md`
- `docs/verification/codex_stretch_agent_eval.md`

## Current Baseline (February 24, 2026)

- Codex stretch retriever: `6/18` (`33.33%`) on `benchmarks/codex_agent_stretch_benchmark.yaml`
- Codex stretch agent: unavailable in this run when model endpoint was unreachable

This indicates the stretch set is currently useful as a stress test but not yet passing.

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
