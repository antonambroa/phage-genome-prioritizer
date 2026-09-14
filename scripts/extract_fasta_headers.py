#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path


def clean_phage_name(description):
    desc = description.strip()

    if desc.endswith(", complete genome"):
        desc = desc[:-len(", complete genome")]

    if desc.endswith(" complete genome"):
        desc = desc[:-len(" complete genome")]

    return desc.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fasta", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    fasta = Path(args.fasta)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    with fasta.open("r", encoding="utf-8") as handle, out.open("w", encoding="utf-8", newline="") as o:
        writer = csv.DictWriter(
            o,
            fieldnames=["accession", "fasta_description", "phage_name_from_fasta"],
            delimiter="\t"
        )
        writer.writeheader()

        for line in handle:
            if not line.startswith(">"):
                continue

            header = line[1:].strip()
            parts = header.split(maxsplit=1)
            accession = parts[0]
            description = parts[1] if len(parts) > 1 else ""

            writer.writerow({
                "accession": accession,
                "fasta_description": description,
                "phage_name_from_fasta": clean_phage_name(description),
            })


if __name__ == "__main__":
    main()
