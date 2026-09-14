# Evo2 integration

The core curation workflow is model-agnostic. The scripts in this directory are optional utilities for benchmarking sequence scores on real and perturbed windows.

This repository intentionally does **not** vendor Evo2, BioNeMo, model weights, or cluster-specific launch code. Provide an external scoring command that writes a CSV containing at least:

- `id`
- `length`
- `log_prob_seq`
- `log_prob_per_base`

Then use `analyze_real_vs_perturbed.py` to compare matched windows.

The original research workflow ran the scorer through SLURM on GPU infrastructure; adapt the template below to your environment.
