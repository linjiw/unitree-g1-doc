.PHONY: sync sync-strict sync-full discover-repos discover-repos-all verify-g1-docs verify-g1-docs-strict render-support index query site coverage mirrors archives repo-lock max-collect pipeline validate-skill eval-retrieval eval-agent

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
