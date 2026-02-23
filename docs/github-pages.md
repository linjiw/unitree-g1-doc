# GitHub Pages Demo Site

## What It Is

A static site under `/site` that lets users search indexed Unitree G1 knowledge directly in the browser.

## Local Build

```bash
python3 scripts/build_site.py
```

Open `/site/index.html` locally.

## Deployment

- Workflow file: `/.github/workflows/pages.yml`
- Trigger: push to `main` or manual dispatch
- Published artifact: `/site`

## Data Files

- `/site/data/search-index.json`: Browser-searchable record subset
- `/site/data/overview.json`: Index and verification stats

## Note

If support docs are blocked from the current network, the site will display non-zero `Blocked support pages` in the stats pills.
