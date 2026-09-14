# Methodology notes

This repository implements a **candidate curation and prioritization workflow**, not a validated clinical or therapeutic decision system.

## Main stages

1. Retrieve complete Caudoviricetes metadata from NCBI Datasets.
2. Build a tabular inventory and normalize selected host groups.
3. Create a host/length/GC-stratified preselection.
4. Collapse near-redundant genomes from externally generated Mash pair edges.
5. Select cluster representatives while preserving host/length/GC diversity.
6. Merge CheckV quality metrics and flag genomes using configurable completeness/contamination thresholds.
7. Apply a conservative annotation-keyword screen for lifestyle, safety, mobile-element, structural, lysis and replication signals.
8. Optionally create fixed-size sequence windows and negative/perturbed controls for model benchmarking.

## Important limitations

The annotation screen is intentionally heuristic. Keyword hits are **review signals**, not proof of phenotype, virulence, lysogeny, antimicrobial resistance, or therapeutic suitability. Results require biological interpretation and, where relevant, additional validated tools and experimental evidence.

Mash clustering is performed from a precomputed edge list (`accession_a`, `accession_b`). The similarity threshold and Mash command used to generate that list should be reported alongside results.

Default host quotas and QC thresholds reproduce one research use case and are exposed as command-line options where practical. They should not be treated as universal biological cutoffs.
