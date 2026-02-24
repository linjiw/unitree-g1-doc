# Ollama Local Setup (Validated)

Last validated: **February 24, 2026** on macOS ARM with Ollama `0.16.0`.

## 1) Start Ollama and pull model

```bash
ollama serve
ollama pull llama3.1
ollama list
```

Expected model:

- `llama3.1:latest` (about 4.9 GB)

## 2) Run baseline retrieval regression

```bash
make eval-retrieval
```

Current result:

- `11/12` (`91.67%`) on `benchmarks/retrieval_benchmark.yaml`

## 3) Run Ollama agent evaluation (default benchmark)

```bash
make eval-agent-ollama
```

Current result:

- `10/12` (`83.33%`) on `benchmarks/retrieval_benchmark.yaml`
- Output: `docs/verification/agent_eval.md`

## 4) Generate and evaluate Ollama+Codex question bank

Question generation:

```bash
make gen-questions-ollama
```

Curated artifacts:

- `benchmarks/ollama_question_bank.yaml`
- `benchmarks/ollama_question_benchmark.yaml`
- `docs/verification/ollama_question_bank.md`

Retriever eval on curated set:

```bash
make eval-retrieval-ollama-qbank
```

Current result:

- `14/16` (`87.50%`)
- Output: `docs/verification/ollama_question_retrieval_eval.md`

Agent eval on curated set:

```bash
make eval-agent-ollama-qbank
```

Current result:

- `13/16` (`81.25%`)
- Output: `docs/verification/ollama_agent_eval.md`

## 5) Notes

- In this sandbox, localhost calls require elevated permissions. If a command fails with `Operation not permitted`, rerun with elevated local-network permission.
- First `ollama pull` may fail near completion due transient network/socket issues. Re-running `ollama pull llama3.1` usually resumes and completes quickly.
