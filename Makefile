.PHONY: sync sync-strict sync-full discover-repos discover-repos-all verify-g1-docs verify-g1-docs-strict render-support index query site coverage mirrors archives repo-lock max-collect pipeline validate-skill eval-retrieval eval-agent eval-agent-ollama gen-questions-ollama eval-retrieval-ollama-qbank eval-agent-ollama-qbank eval-retrieval-codex-stretch eval-agent-ollama-codex-stretch

PYTHON ?= python3
ifneq ("$(wildcard .venv/bin/python)","")
PYTHON := .venv/bin/python
endif

sync:
	$(PYTHON) scripts/sync_sources.py

sync-strict:
	$(PYTHON) scripts/sync_sources.py --fail-on-error

sync-full:
	$(PYTHON) scripts/sync_sources.py --full-history

discover-repos:
	$(PYTHON) scripts/discover_unitree_repos.py --update-manifest

discover-repos-all:
	$(PYTHON) scripts/discover_unitree_repos.py --include-all --update-manifest

verify-g1-docs:
	$(PYTHON) scripts/verify_g1_docs.py --update-manifest

verify-g1-docs-strict:
	$(PYTHON) scripts/verify_g1_docs.py --update-manifest --fail-on-error

index:
	$(PYTHON) scripts/build_knowledge_index.py

render-support:
	$(PYTHON) scripts/render_support_docs.py

query:
	$(PYTHON) scripts/query_index.py "$(q)"

site:
	$(PYTHON) scripts/build_site.py

coverage:
	$(PYTHON) scripts/build_coverage_report.py

mirrors:
	$(PYTHON) scripts/sync_repo_mirrors.py

archives:
	$(PYTHON) scripts/download_repo_archives.py

repo-lock:
	$(PYTHON) scripts/build_repo_lock.py

max-collect:
	bash scripts/max_collect.sh

pipeline:
	bash scripts/run_pipeline.sh

validate-skill:
	$(PYTHON) /Users/linji/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/unitree-g1-expert

eval-retrieval:
	$(PYTHON) scripts/eval_retrieval.py --strict --fail-below 0.75

eval-agent:
	$(PYTHON) scripts/eval_openai_compatible.py --strict --fail-below 0.70

eval-agent-ollama:
	OPENAI_API_BASE=$${OPENAI_API_BASE:-http://127.0.0.1:11434/v1} \
	OPENAI_API_KEY=$${OPENAI_API_KEY:-ollama} \
	OPENAI_MODEL=$${OPENAI_MODEL:-llama3.1} \
	$(PYTHON) scripts/eval_openai_compatible.py --strict --fail-below 0.70

gen-questions-ollama:
	OPENAI_API_BASE=$${OPENAI_API_BASE:-http://127.0.0.1:11434/v1} \
	OPENAI_API_KEY=$${OPENAI_API_KEY:-ollama} \
	OPENAI_MODEL=$${OPENAI_MODEL:-llama3.1} \
	$(PYTHON) scripts/generate_question_bank.py --count 24
	$(PYTHON) scripts/build_question_benchmark.py --input benchmarks/ollama_question_bank.yaml --output benchmarks/ollama_question_benchmark.yaml

eval-retrieval-ollama-qbank:
	$(PYTHON) scripts/eval_retrieval.py \
		--benchmark benchmarks/ollama_question_benchmark.yaml \
		--json-out docs/verification/ollama_question_retrieval_eval.json \
		--md-out docs/verification/ollama_question_retrieval_eval.md \
		--strict --fail-below 0.70

eval-agent-ollama-qbank:
	OPENAI_API_BASE=$${OPENAI_API_BASE:-http://127.0.0.1:11434/v1} \
	OPENAI_API_KEY=$${OPENAI_API_KEY:-ollama} \
	OPENAI_MODEL=$${OPENAI_MODEL:-llama3.1} \
	$(PYTHON) scripts/eval_openai_compatible.py \
		--benchmark benchmarks/ollama_question_benchmark.yaml \
		--json-out docs/verification/ollama_agent_eval.json \
		--md-out docs/verification/ollama_agent_eval.md \
		--strict --fail-below 0.60

eval-retrieval-codex-stretch:
	$(PYTHON) scripts/eval_retrieval.py \
		--benchmark benchmarks/codex_agent_stretch_benchmark.yaml \
		--json-out docs/verification/codex_stretch_retrieval_eval.json \
		--md-out docs/verification/codex_stretch_retrieval_eval.md \
		--strict --fail-below 0.70

eval-agent-ollama-codex-stretch:
	OPENAI_API_BASE=$${OPENAI_API_BASE:-http://127.0.0.1:11434/v1} \
	OPENAI_API_KEY=$${OPENAI_API_KEY:-ollama} \
	OPENAI_MODEL=$${OPENAI_MODEL:-llama3.1} \
	$(PYTHON) scripts/eval_openai_compatible.py \
		--benchmark benchmarks/codex_agent_stretch_benchmark.yaml \
		--json-out docs/verification/codex_stretch_agent_eval.json \
		--md-out docs/verification/codex_stretch_agent_eval.md \
		--strict --fail-below 0.60
