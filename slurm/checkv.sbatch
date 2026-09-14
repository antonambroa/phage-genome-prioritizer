#!/usr/bin/env bash
#SBATCH --job-name=phage_checkv
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=logs/checkv_%j.out
#SBATCH --error=logs/checkv_%j.err

set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: sbatch slurm/checkv.sbatch <input.fasta> <output_dir> <checkv_db>"
  exit 2
fi

INPUT_FASTA=$1
OUTDIR=$2
CHECKV_DB=$3
mkdir -p "$OUTDIR" logs

# Load CheckV according to your cluster/software environment before submission,
# or uncomment/adapt the module line below.
# module load checkv

checkv end_to_end "$INPUT_FASTA" "$OUTDIR" \
  -d "$CHECKV_DB" \
  -t "${SLURM_CPUS_PER_TASK:-8}"
