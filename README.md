# phage-genome-prioritizer

A lightweight, reproducible workflow for **curating and prioritizing complete bacteriophage genomes** for downstream comparative genomics and sequence-model benchmarking.

The project grew out of a research workflow used to reduce a large public phage collection into a diverse, quality-controlled candidate set while keeping the selection process explicit and auditable.

## What it does

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

## Current scope

The core scripts use the Python standard library and are intentionally kept transparent rather than hidden behind a large framework. External tools are only needed for the stages that call them directly:

- **NCBI Datasets CLI** for metadata acquisition.
- **Mash** to generate similarity pairs used by the redundancy-clustering step.
- **CheckV** for viral genome QC.
- **Evo2/BioNeMo or another sequence scorer** only for the optional model-benchmarking integration.

No reference genomes, model weights, HPC paths, institutional configuration, or large result files are included.

## Quick start

### 1. Download public metadata

```bash
bash scripts/download_ncbi_caudoviricetes_metadata.sh data/raw/ncbi_virus
```

### 2. Add normalized host groups

```bash
python scripts/add_host_groups.py \
  --input examples/inventory.tsv \
  --output /tmp/inventory_grouped.tsv
```

### 3. Build a stratified preselection

For a small demo, lower the research-scale quotas:

```bash
python scripts/make_stratified_preselection.py \
  --input /tmp/inventory_grouped.tsv \
  --output /tmp/preselection.tsv \
  --quota-ecoli-shigella 2 \
  --quota-klebsiella 1 \
  --quota-pseudomonas 1 \
  --quota-acinetobacter 1
```

### 4. Build redundancy clusters

The input edge list must contain `accession_a` and `accession_b` columns. It is normally generated from a chosen Mash similarity threshold.

```bash
python scripts/build_mash_redundancy_clusters.py \
  --inventory /tmp/preselection.tsv \
  --pairs examples/mash_pairs.tsv \
  --clusters-output /tmp/mash_clusters.tsv \
  --flagged-inventory-output /tmp/preselection_mash.tsv
```

### 5. Merge CheckV results

```bash
python scripts/merge_checkv_results.py \
  --inventory /tmp/preselection_mash.tsv \
  --checkv-quality-summary examples/checkv_quality_summary.tsv \
  --output /tmp/checkv_merged.tsv \
  --min-completeness 90 \
  --max-contamination 0
```

## Repository layout

```text
scripts/            curation, QC, filtering and sequence utilities
slurm/              generic HPC submission templates
integrations/evo2/  optional sequence-model benchmarking helpers
examples/           tiny synthetic tabular examples
tests/              tests for core selection/QC logic
docs/               methodology and limitations
```

## Reproducibility choices

- Sampling operations use explicit random seeds.
- Stratified selection is performed across host, genome-length and GC bins.
- Redundancy clusters retain a deterministic representative.
- QC decisions are written back to the inventory together with machine-readable reasons.
- Perturbed and negative-control windows can be generated for score sanity checks.

## Biological interpretation

The functional annotation screen is deliberately conservative and keyword-based. It flags records for review; it does **not** establish lysogeny, virulence, antimicrobial resistance, host range, safety, or therapeutic suitability. See [`docs/methodology.md`](docs/methodology.md).

## Status

Research code being converted into a reusable public workflow. The scripts are suitable for transparent, reproducible curation experiments, but the complete pipeline is not yet packaged as a single workflow engine (Nextflow/Snakemake).
