# phage-genome-prioritizer

[![tests](https://github.com/antonambroa/phage-genome-prioritizer/actions/workflows/tests.yml/badge.svg)](https://github.com/antonambroa/phage-genome-prioritizer/actions/workflows/tests.yml)

Scripts for curating and prioritizing complete bacteriophage genomes before comparative genomics or sequence-model analysis.

This repository grew out of a working pipeline for reducing a large public phage collection to a smaller, diverse and quality-controlled candidate set while keeping each filtering decision traceable.

## Workflow

```text
NCBI Virus metadata / FASTA
          │
          ▼
   inventory + QC
          │
          ▼
      host groups
          │
          ▼
length/GC stratified preselection
          │
          ▼
  Mash redundancy clusters
          │
          ▼
 cluster representatives
          │
          ▼
      CheckV merge
          │
          ▼
 heuristic annotation screen
          │
          └──────────────► curated candidate table
                           │
                           ▼
                optional sequence windows
                           │
                           ▼
               model/score benchmarking
```

The core scripts use the Python standard library. Additional tools are needed only for the stages that use them directly: NCBI Datasets CLI for data acquisition, Mash for similarity calculations, CheckV for viral genome QC, and Evo2/BioNeMo or another scorer for the optional model-benchmarking stage.

No reference genomes, model weights, cluster-specific paths or large result files are included.

## Quick start

The example files are synthetic and small enough to run locally.

```bash
python scripts/add_host_groups.py \
  --input examples/inventory.tsv \
  --output /tmp/inventory_grouped.tsv

python scripts/make_stratified_preselection.py \
  --input /tmp/inventory_grouped.tsv \
  --output /tmp/preselection.tsv \
  --quota-ecoli-shigella 2 \
  --quota-klebsiella 1 \
  --quota-pseudomonas 1 \
  --quota-acinetobacter 1

python scripts/build_mash_redundancy_clusters.py \
  --inventory /tmp/preselection.tsv \
  --pairs examples/mash_pairs.tsv \
  --clusters-output /tmp/mash_clusters.tsv \
  --flagged-inventory-output /tmp/preselection_mash.tsv

python scripts/merge_checkv_results.py \
  --inventory /tmp/preselection_mash.tsv \
  --checkv-quality-summary examples/checkv_quality_summary.tsv \
  --output /tmp/checkv_merged.tsv \
  --min-completeness 90 \
  --max-contamination 0
```

The same example can be run in one go with:

```bash
bash examples/run_demo.sh
```

## Repository layout

```text
scripts/            curation, QC, filtering and sequence utilities
slurm/              generic HPC submission templates
integrations/evo2/  optional sequence-model benchmarking helpers
examples/           small synthetic inputs
tests/              tests for core selection/QC logic
docs/               methodology and limitations
```

## Reproducibility

Sampling uses explicit random seeds, stratified selection is performed across host/length/GC bins, Mash clusters retain a deterministic representative, and QC decisions are written back to the inventory with machine-readable reasons. Perturbed and negative-control windows are also available for model-score sanity checks.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
bash examples/run_demo.sh
```

The same checks run automatically on pushes and pull requests through GitHub Actions.

## Biological interpretation

The functional annotation screen is deliberately conservative and keyword-based. It flags records for review; it does **not** establish lysogeny, virulence, antimicrobial resistance, host range, safety or therapeutic suitability. See [`docs/methodology.md`](docs/methodology.md).

## Status

The individual stages are usable as standalone scripts. The full workflow is still script-based rather than wrapped in Nextflow or Snakemake.
