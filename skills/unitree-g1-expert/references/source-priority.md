# Source Priority

Always prefer these sources in order:

1. Official Unitree support pages listed in `sources/unitree_g1_sources.yaml`.
2. Official Unitree GitHub repositories listed in the same manifest.
3. Curated digests in `docs/source-digests/`.
4. Verification outputs in `docs/verification/`.

## Evidence Rules

- Label a statement as `Verified` only when directly supported by cited material.
- Label a statement as `Inference` when reasoning beyond explicit source text.
- If the answer depends on missing data, request `scripts/sync_sources.py` before finalizing.
