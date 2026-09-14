#!/usr/bin/env bash
set -euo pipefail

OUTDIR=${1:-data/raw/ncbi_virus}
mkdir -p "$OUTDIR"
DATE=$(date +%Y%m%d)
TAXON_ID=${CAUDOVIRICETES_TAXON_ID:-2731619}

echo "[INFO] Downloading complete Caudoviricetes metadata"
datasets summary virus genome taxon "$TAXON_ID" \
  --complete-only --as-json-lines \
  > "$OUTDIR/caudoviricetes_complete_${DATE}.jsonl"

for host in \
  "Escherichia coli" \
  "Shigella" \
  "Klebsiella pneumoniae" \
  "Pseudomonas aeruginosa" \
  "Acinetobacter baumannii"
do
  safe=$(printf '%s' "$host" | tr '[:upper:] ' '[:lower:]_' | tr -d '.')
  echo "[INFO] Host: $host"
  datasets summary virus genome taxon "$TAXON_ID" \
    --complete-only --host "$host" --as-json-lines \
    > "$OUTDIR/${safe}_caudoviricetes_complete_${DATE}.jsonl"
done

sha256sum "$OUTDIR"/*"${DATE}".jsonl > "$OUTDIR/sha256_${DATE}.txt"
echo "[INFO] Done: $OUTDIR"
