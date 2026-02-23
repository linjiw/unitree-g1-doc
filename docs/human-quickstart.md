# Human Quickstart

## Install

```bash
pip install -r requirements.txt
```

Optional for JS-rendered support pages:

```bash
pip install -r requirements-optional.txt
playwright install chromium
```

## Sync + Verify + Index

One command:

```bash
bash scripts/bootstrap.sh
```

Step-by-step:

```bash
python3 scripts/sync_sources.py
python3 scripts/verify_g1_docs.py --update-manifest
python3 scripts/build_knowledge_index.py
python3 scripts/build_coverage_report.py
```

## Ask Questions

```bash
python3 scripts/query_index.py "how do I deploy g1 policy on remote pc" --top-k 10
```

Machine-readable result:

```bash
python3 scripts/query_index.py "g1 dds interface" --format json
```

## Build Demo Website

```bash
python3 scripts/build_site.py
```

Open `site/index.html` locally or publish `site/` via GitHub Pages.
