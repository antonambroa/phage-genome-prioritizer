#!/usr/bin/env python3

import argparse
import csv
import json
from pathlib import Path


def count_fasta(path):
    n = 0
    headers = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith(">"):
                n += 1
                headers.append(line[1:].strip())
    return n, headers


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fasta", required=True)
    parser.add_argument("--scores", required=True)
    parser.add_argument("--seq-idx-map", required=True)
    args = parser.parse_args()

    fasta_n, fasta_headers = count_fasta(args.fasta)

    with open(args.scores, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = reader.fieldnames or []

    with open(args.seq_idx_map, "r", encoding="utf-8") as handle:
        seq_map = json.load(handle)

    print("=== Evo2 smoke validation ===")
    print(f"FASTA records: {fasta_n}")
    print(f"Score rows: {len(rows)}")
    print(f"seq_idx_map type: {type(seq_map).__name__}")
    print(f"seq_idx_map entries: {len(seq_map)}")
    print("")
    print("Score columns:")
    for f in fields:
        print(f"- {f}")

    print("")
    print("First FASTA headers:")
    for h in fasta_headers[:5]:
        print(h)

    print("")
    print("First score rows:")
    for row in rows[:5]:
        print(row)

    print("")
    print("First seq_idx_map entries:")
    if isinstance(seq_map, dict):
        for i, (k, v) in enumerate(seq_map.items()):
            print(k, "=>", v)
            if i >= 4:
                break
    elif isinstance(seq_map, list):
        for i, v in enumerate(seq_map[:5]):
            print(i, "=>", v)

    print("")
    if fasta_n == len(rows):
        print("[OK] Number of score rows matches FASTA records.")
    else:
        print("[WARN] Number of score rows does not match FASTA records.")

    if fasta_n == len(seq_map):
        print("[OK] Number of seq_idx_map entries matches FASTA records.")
    else:
        print("[WARN] Number of seq_idx_map entries does not match FASTA records.")


if __name__ == "__main__":
    main()
