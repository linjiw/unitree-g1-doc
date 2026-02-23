# Knowledge Index Guide

## Key Outputs

- Main JSONL index: `/data/index/knowledge_index.jsonl`
- Index metadata: `/data/index/knowledge_index.meta.json`
- Markdown index summary: `/data/index/knowledge_index.md`
- Repo lock report: `/docs/verification/repo_lock.md`
- Full org catalog snapshot: `/sources/unitree_org_repo_catalog.json`
- Raw mirrors: `/data/repo_mirrors/*.git` (generated, gitignored)
- Raw tar archives: `/data/repo_archives/*.tar.gz` (generated, gitignored)

## Query Interfaces

- Text mode:
  - `python3 scripts/query_index.py "<question>"`
- JSON mode for agents:
  - `python3 scripts/query_index.py "<question>" --format json`
- Markdown mode for reports:
  - `python3 scripts/query_index.py "<question>" --format markdown`

## What Is Indexed

- Unitree repo files (`repo_file`)
- Verified support docs (`support_doc`)
- Curated docs under `/docs` (`curated_doc`)
- Skill markdown under `/skills` (`skill_doc`)
- Source manifests/catalogs under `/sources` (`source_manifest`)

## Regeneration

```bash
python3 scripts/build_knowledge_index.py
```
