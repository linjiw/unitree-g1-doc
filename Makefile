.PHONY: sync sync-strict discover-repos verify-g1-docs verify-g1-docs-strict render-support index query site coverage pipeline validate-skill

sync:
	python3 scripts/sync_sources.py

sync-strict:
	python3 scripts/sync_sources.py --fail-on-error

discover-repos:
	python3 scripts/discover_unitree_repos.py --update-manifest

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

pipeline:
	bash scripts/run_pipeline.sh

validate-skill:
	python3 /Users/linji/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/unitree-g1-expert
