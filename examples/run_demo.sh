#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
WORK=${1:-/tmp/phage-prioritizer-demo}
rm -rf "$WORK"
mkdir -p "$WORK"

python "$ROOT/scripts/add_host_groups.py" \
  --input "$ROOT/examples/inventory.tsv" \
  --output "$WORK/inventory_grouped.tsv"

python "$ROOT/scripts/make_stratified_preselection.py" \
  --input "$WORK/inventory_grouped.tsv" \
  --output "$WORK/preselection.tsv" \
  --quota-ecoli-shigella 2 \
  --quota-klebsiella 1 \
  --quota-pseudomonas 1 \
  --quota-acinetobacter 1

python "$ROOT/scripts/build_mash_redundancy_clusters.py" \
  --inventory "$WORK/preselection.tsv" \
  --pairs "$ROOT/examples/mash_pairs.tsv" \
  --clusters-output "$WORK/mash_clusters.tsv" \
  --flagged-inventory-output "$WORK/preselection_mash.tsv"

python "$ROOT/scripts/make_precurated_set.py" \
  --input "$WORK/preselection_mash.tsv" \
  --output-flagged "$WORK/precurated_flagged.tsv" \
  --output-selected "$WORK/precurated.tsv" \
  --quota-ecoli-shigella 2 \
  --quota-klebsiella 1 \
  --quota-pseudomonas 1 \
  --quota-acinetobacter 1

python "$ROOT/scripts/merge_checkv_results.py" \
  --inventory "$WORK/precurated.tsv" \
  --checkv-quality-summary "$ROOT/examples/checkv_quality_summary.tsv" \
  --output "$WORK/checkv_merged.tsv"

echo
echo "Demo complete: $WORK"
echo "Selected candidate genomes:"
cut -f1,3,14,16 "$WORK/precurated.tsv" | column -t -s $'\t' 2>/dev/null || cat "$WORK/precurated.tsv"
