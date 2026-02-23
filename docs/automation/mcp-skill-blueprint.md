# MCP + Skill Blueprint

Goal: make this repository answer Unitree questions automatically with grounded local evidence.

## Automation Loop

1. Run `scripts/discover_unitree_repos.py --update-manifest` daily/weekly.
2. Run `scripts/sync_sources.py` on schedule.
3. Run `scripts/verify_g1_docs.py --update-manifest` for JS-rendered support pages.
4. Run `scripts/build_knowledge_index.py` right after sync/verify.
5. Run `scripts/build_site.py` to refresh GitHub Pages search payloads.
6. Run retrieval (`scripts/query_index.py`) for incoming questions.
7. Route top matches to a skill prompt that enforces citation-first answers.

## Recommended Scheduling

- `daily`: sync + index refresh.
- `on-demand`: force sync before high-stakes debugging.
- `pre-release`: pin a snapshot summary in `data/snapshots/`.

## MCP Server Design

Expose at least three tools:

1. `search_unitree(query, top_k)`
2. `open_record(record_id)`
3. `list_sources(filter_topic)`

Each tool should read from `data/index/knowledge_index.jsonl` and return file paths/URLs used for the answer.

## Skill Design

The included `unitree-g1-expert` skill should:

1. Query local index first.
2. Ask for missing runtime facts only when local data is insufficient.
3. Output exact paths to docs/source files.
4. Distinguish verified facts vs engineering inference.
