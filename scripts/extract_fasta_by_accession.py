#!/usr/bin/env python3

import argparse
from pathlib import Path


def load_accessions(path):
    with open(path, "r", encoding="utf-8") as handle:
        return {line.strip() for line in handle if line.strip()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fasta", required=True)
    parser.add_argument("--accessions", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--missing-output", required=True)
    args = parser.parse_args()

    wanted = load_accessions(args.accessions)
    found = set()

    fasta = Path(args.fasta)
    out = Path(args.output)
    missing_out = Path(args.missing_output)

    out.parent.mkdir(parents=True, exist_ok=True)
    missing_out.parent.mkdir(parents=True, exist_ok=True)

    write_record = False

    with fasta.open("r", encoding="utf-8") as inp, out.open("w", encoding="utf-8") as o:
        for line in inp:
            if line.startswith(">"):
                acc = line[1:].strip().split()[0]
                write_record = acc in wanted
                if write_record:
                    found.add(acc)
                    o.write(line)
            else:
                if write_record:
                    o.write(line)

    missing = sorted(wanted - found)

    with missing_out.open("w", encoding="utf-8") as m:
        for acc in missing:
            m.write(acc + "\n")

    print(f"[INFO] Wanted: {len(wanted)}")
    print(f"[INFO] Found: {len(found)}")
    print(f"[INFO] Missing: {len(missing)}")
    print(f"[INFO] Output FASTA: {out}")
    print(f"[INFO] Missing list: {missing_out}")


if __name__ == "__main__":
    main()
