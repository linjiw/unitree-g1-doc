# Knowledge Index Guide

## Key Outputs

- Main JSONL index: `/data/index/knowledge_index.jsonl`
- Index metadata: `/data/index/knowledge_index.meta.json`
- Markdown index summary: `/data/index/knowledge_index.md`

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

## Regeneration

```bash
python3 scripts/build_knowledge_index.py
```
