.PHONY: sync sync-strict sync-full discover-repos discover-repos-all verify-g1-docs verify-g1-docs-strict render-support index query site coverage mirrors archives repo-lock max-collect pipeline validate-skill

sync:
	python3 scripts/sync_sources.py

sync-strict:
	python3 scripts/sync_sources.py --fail-on-error

sync-full:
	python3 scripts/sync_sources.py --full-history

discover-repos:
	python3 scripts/discover_unitree_repos.py --update-manifest

discover-repos-all:
	python3 scripts/discover_unitree_repos.py --include-all --update-manifest

verify-g1-docs:
	python3 scripts/verify_g1_docs.py --update-manifest

verify-g1-docs-strict:
	python3 scripts/verify_g1_docs.py --update-manifest --fail-on-error

index:
	python3 scripts/build_knowledge_index.py

render-support:
	python3 scripts/render_support_docs.py

query:
	python3 scripts/query_index.py "$(q)"

site:
	python3 scripts/build_site.py

coverage:
	python3 scripts/build_coverage_report.py

mirrors:
	python3 scripts/sync_repo_mirrors.py

archives:
	python3 scripts/download_repo_archives.py

repo-lock:
	python3 scripts/build_repo_lock.py

max-collect:
	bash scripts/max_collect.sh

pipeline:
	bash scripts/run_pipeline.sh

validate-skill:
	python3 /Users/linji/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/unitree-g1-expert
