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

## 3) Outputs

- `docs/verification/retrieval_eval.json`
- `docs/verification/retrieval_eval.md`
- `docs/verification/agent_eval.json`
- `docs/verification/agent_eval.md`

## 4) Suggested Quality Gates

- Retriever pass rate: `>= 0.75`
- Agent source-selection pass rate: `>= 0.70`
- Raise thresholds after adding more benchmark cases.
