#!/usr/bin/env python3

import argparse
import random
from pathlib import Path


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


def write_record(handle, header, seq, width=80):
    handle.write(f">{header}\n")
    for i in range(0, len(seq), width):
        handle.write(seq[i:i+width] + "\n")


def random_uniform(n):
    return "".join(random.choice("ACGT") for _ in range(n))


def random_gc_matched(seq):
    n = len(seq)
    gc = (seq.count("G") + seq.count("C")) / n
    p_gc_each = gc / 2
    p_at_each = (1 - gc) / 2

    bases = []
    for _ in range(n):
        x = random.random()
        if x < p_at_each:
            bases.append("A")
        elif x < 2 * p_at_each:
            bases.append("T")
        elif x < 2 * p_at_each + p_gc_each:
            bases.append("G")
        else:
            bases.append("C")

    return "".join(bases)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-fasta", required=True)
    parser.add_argument("--output-fasta", required=True)
    parser.add_argument("--seed", type=int, default=456)
    parser.add_argument("--n", type=int, default=20)
    args = parser.parse_args()

    random.seed(args.seed)

    out = Path(args.output_fasta)
    out.parent.mkdir(parents=True, exist_ok=True)

    written_real = 0
    written_controls = 0

    with out.open("w", encoding="utf-8") as handle:
        for header, seq in read_fasta(args.input_fasta):
            if written_real >= args.n:
                break

            write_record(handle, header, seq)
            written_real += 1

            write_record(handle, f"{header}|perturb=random_uniform|seed={args.seed}", random_uniform(len(seq)))
            write_record(handle, f"{header}|perturb=random_gc_matched|seed={args.seed}", random_gc_matched(seq))
            write_record(handle, f"{header}|perturb=homopolymer_A", "A" * len(seq))
            written_controls += 3

    print(f"[INFO] Real windows written: {written_real}")
    print(f"[INFO] Controls written: {written_controls}")
    print(f"[INFO] Total: {written_real + written_controls}")
    print(f"[INFO] Output: {out}")


if __name__ == "__main__":
    main()
