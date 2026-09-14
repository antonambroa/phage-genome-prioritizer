#!/usr/bin/env python3

import argparse
import random
from pathlib import Path


def read_fasta(path):
    name = None
    chunks = []

    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip()
            if line.startswith(">"):
                if name is not None:
                    yield name, "".join(chunks)
                name = line[1:].strip()
                chunks = []
            else:
                chunks.append(line.strip())

        if name is not None:
            yield name, "".join(chunks)


def write_fasta_record(handle, header, seq, width=80):
    handle.write(f">{header}\n")
    for i in range(0, len(seq), width):
        handle.write(seq[i:i+width] + "\n")


def mono_shuffle(seq):
    chars = list(seq)
    random.shuffle(chars)
    return "".join(chars)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-fasta", required=True)
    parser.add_argument("--output-fasta", required=True)
    parser.add_argument("--seed", type=int, default=123)
    args = parser.parse_args()

    random.seed(args.seed)

    out = Path(args.output_fasta)
    out.parent.mkdir(parents=True, exist_ok=True)

    n_real = 0
    n_out = 0

    with out.open("w", encoding="utf-8") as handle:
        for header, seq in read_fasta(args.input_fasta):
            n_real += 1
            seq = seq.upper()

            shuffled = mono_shuffle(seq)
            reversed_seq = seq[::-1]

            write_fasta_record(
                handle,
                f"{header}|perturb=shuffle_mono|seed={args.seed}",
                shuffled
            )
            n_out += 1

            write_fasta_record(
                handle,
                f"{header}|perturb=reverse",
                reversed_seq
            )
            n_out += 1

    print(f"[INFO] Real input windows: {n_real}")
    print(f"[INFO] Perturbed windows written: {n_out}")
    print(f"[INFO] Output FASTA: {out}")


if __name__ == "__main__":
    main()
