# Publication checklist

Before making the repository public:

- [ ] Choose and add an explicit software license after confirming ownership/redistribution rights.
- [ ] Record tested versions of NCBI Datasets CLI, Mash and CheckV.
- [ ] Confirm the current NCBI Datasets JSONL schema against the inventory parsers.
- [ ] Document the Mash command and similarity threshold used to create redundancy edges.
- [ ] Review the default priority-host list and quotas; they reflect one research use case.
- [ ] Treat annotation-keyword flags as review signals only; validate important calls with dedicated tools/manual curation.
- [ ] Keep model weights, large FASTA files, raw outputs and HPC-specific configuration out of Git.
- [ ] If the Evo2 adapter is enabled, document the exact model/checkpoint and scoring implementation used.
