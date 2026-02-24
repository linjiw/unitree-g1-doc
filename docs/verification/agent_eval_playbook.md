# Agent Evaluation Playbook

Use this to benchmark whether an AI agent can select the right Unitree G1 sources for a user question.

## 1) Baseline Retriever Regression

```bash
.venv/bin/python scripts/eval_retrieval.py --strict --fail-below 0.75
```

This checks lexical retrieval only (no LLM).

## 2) OpenAI-Compatible Model Evaluation

```bash
OPENAI_API_BASE=http://localhost:8000/v1 \
OPENAI_API_KEY=EMPTY \
OPENAI_MODEL=your-model-name \
.venv/bin/python scripts/eval_openai_compatible.py --strict --fail-below 0.70
```

This checks whether the model can select relevant source paths from retrieved candidates.

### Ollama Shortcut

```bash
ollama serve
ollama pull llama3.1
make eval-agent-ollama
```

Uses:
- `OPENAI_API_BASE=http://127.0.0.1:11434/v1`
- `OPENAI_API_KEY=ollama`
- `OPENAI_MODEL=llama3.1`

## 3) Build More Questions (Ollama + Codex)

```bash
make gen-questions-ollama
```

Outputs:
- `benchmarks/ollama_question_bank.yaml`
- `docs/verification/ollama_question_bank.md`

## 4) Evaluate the Curated Ollama+Codex Question Set

Retriever-only:

```bash
make eval-retrieval-ollama-qbank
```

Model source-selection:

```bash
make eval-agent-ollama-qbank
```

## 5) Outputs

- `docs/verification/retrieval_eval.json`
- `docs/verification/retrieval_eval.md`
- `docs/verification/agent_eval.json`
- `docs/verification/agent_eval.md`
- `benchmarks/ollama_question_bank.yaml`
- `benchmarks/ollama_question_benchmark.yaml`
- `docs/verification/ollama_question_bank.md`
- `docs/verification/ollama_question_retrieval_eval.md`
- `docs/verification/ollama_agent_eval.md`
- `docs/verification/codex_stretch_retrieval_eval.md`
- `docs/verification/codex_stretch_agent_eval.md`

## 6) Codex Stretch Benchmark

Retriever-only:

```bash
make eval-retrieval-codex-stretch
```

Model source-selection:

```bash
make eval-agent-ollama-codex-stretch
```

Benchmark file:
- `benchmarks/codex_agent_stretch_benchmark.yaml`
- experiment design doc: `docs/verification/codex_agent_experiments.md`

## 7) Suggested Quality Gates

- Retriever pass rate: `>= 0.75`
- Agent source-selection pass rate: `>= 0.70`
- Codex stretch retriever pass rate: `>= 0.70`
- Codex stretch agent pass rate: `>= 0.60`
- Raise thresholds after adding more benchmark cases.
