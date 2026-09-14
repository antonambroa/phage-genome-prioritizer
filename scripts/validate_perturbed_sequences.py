#!/usr/bin/env python3

import argparse
from collections import Counter, defaultdict


def read_fasta(path):
    header = None
    chunks = []

    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip()
            if line.startswith(">"):
                if header is not None:
                    yield header[1:], "".join(chunks).upper()
                header = line
                chunks = []
            else:
                chunks.append(line.strip())

        if header is not None:
            yield header[1:], "".join(chunks).upper()


def base_id(seq_id):
    parts = [p for p in seq_id.split("|") if not p.startswith("perturb=") and not p.startswith("seed=")]
    return "|".join(parts)


def perturb_type(seq_id):
    for p in seq_id.split("|"):
        if p.startswith("perturb="):
            return p.split("=", 1)[1]
    return "real"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--real-fasta", required=True)
    parser.add_argument("--perturbed-fasta", required=True)
    args = parser.parse_args()

    real = {h: s for h, s in read_fasta(args.real_fasta)}

    perturbed = defaultdict(dict)
    for h, s in read_fasta(args.perturbed_fasta):
        perturbed[base_id(h)][perturb_type(h)] = s

    print("base_window_id\tperturb_type\tlength_equal\tsequence_equal\tcomposition_equal\thamming_fraction_different")

    n = 0
    for bid, rseq in real.items():
        if bid not in perturbed:
            continue

        for ptype, pseq in perturbed[bid].items():
            length_equal = len(rseq) == len(pseq)
            sequence_equal = rseq == pseq
            composition_equal = Counter(rseq) == Counter(pseq)

            if length_equal:
                diff = sum(1 for a, b in zip(rseq, pseq) if a != b) / len(rseq)
            else:
                diff = "NA"

            print(
                bid,
                ptype,
                length_equal,
                sequence_equal,
                composition_equal,
                diff,
                sep="\t"
            )
            n += 1

            if n >= 20:
                return


if __name__ == "__main__":
    main()
