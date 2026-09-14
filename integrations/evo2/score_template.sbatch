#!/usr/bin/env bash
#SBATCH --job-name=evo2_score
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
#SBATCH --time=02:00:00
#SBATCH --output=logs/evo2_%j.out
#SBATCH --error=logs/evo2_%j.err

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: sbatch integrations/evo2/score_template.sbatch <input.fasta> <output_dir>"
  exit 2
fi

: "${EVO2_SCORE_CMD:?Set EVO2_SCORE_CMD to your local Evo2 FASTA scoring wrapper}"
INPUT_FASTA=$1
OUTDIR=$2
mkdir -p "$OUTDIR" logs

"$EVO2_SCORE_CMD" "$INPUT_FASTA" "$OUTDIR"
