#!/usr/bin/env python3

import argparse
from pathlib import Path


def read_fasta(path):
    header = None
    chunks = []

    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip()
            if line.startswith(">"):
                if header is not None:
                    yield header, "".join(chunks)
                header = line
                chunks = []
            else:
                chunks.append(line)

        if header is not None:
            yield header, "".join(chunks)


def write_record(handle, header, seq, width=80):
    handle.write(header + "\n")
    for i in range(0, len(seq), width):
        handle.write(seq[i:i+width] + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--n", type=int, required=True)
    args = parser.parse_args()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    count = 0

    with out.open("w", encoding="utf-8") as handle:
        for header, seq in read_fasta(args.input):
            if count >= args.n:
                break
            write_record(handle, header, seq)
            count += 1

    print(f"[INFO] Written records: {count}")
    print(f"[INFO] Output: {out}")


if __name__ == "__main__":
    main()
