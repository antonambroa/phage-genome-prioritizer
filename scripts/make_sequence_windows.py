#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path


def read_fasta(path):
    name = None
    desc = None
    chunks = []

    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip()
            if line.startswith(">"):
                if name is not None:
                    yield name, desc, "".join(chunks)
                header = line[1:].strip()
                parts = header.split(maxsplit=1)
                name = parts[0]
                desc = parts[1] if len(parts) > 1 else ""
                chunks = []
            else:
                chunks.append(line.strip())

        if name is not None:
            yield name, desc, "".join(chunks)


def write_fasta_record(handle, header, seq, width=80):
    handle.write(f">{header}\n")
    for i in range(0, len(seq), width):
        handle.write(seq[i:i+width] + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-fasta", required=True)
    parser.add_argument("--output-fasta", required=True)
    parser.add_argument("--metadata-tsv", required=True)
    parser.add_argument("--window-size", type=int, default=8192)
    parser.add_argument("--step-size", type=int, default=4096)
    parser.add_argument("--min-window-size", type=int, default=8192)
    args = parser.parse_args()

    out_fasta = Path(args.output_fasta)
    out_meta = Path(args.metadata_tsv)
    out_fasta.parent.mkdir(parents=True, exist_ok=True)
    out_meta.parent.mkdir(parents=True, exist_ok=True)

    n_windows = 0

    with out_fasta.open("w", encoding="utf-8") as fa, out_meta.open("w", encoding="utf-8", newline="") as meta:
        fields = [
            "window_id",
            "accession",
            "source_description",
            "genome_length",
            "window_start_1based",
            "window_end_1based",
            "window_length",
            "window_type",
        ]
        writer = csv.DictWriter(meta, fieldnames=fields, delimiter="\t")
        writer.writeheader()

        for acc, desc, seq in read_fasta(args.input_fasta):
            seq = seq.upper()
            genome_len = len(seq)

            if genome_len < args.min_window_size:
                continue

            starts = list(range(0, genome_len - args.window_size + 1, args.step_size))

            # Ensure last full-size window reaches the end if not already covered.
            last_start = genome_len - args.window_size
            if last_start >= 0 and (not starts or starts[-1] != last_start):
                starts.append(last_start)

            for idx, start in enumerate(starts, start=1):
                end = start + args.window_size
                window_seq = seq[start:end]

                if len(window_seq) < args.min_window_size:
                    continue

                n_windows += 1
                window_id = f"{acc}|win{idx:04d}|{start+1}-{end}"

                write_fasta_record(fa, window_id, window_seq)

                writer.writerow({
                    "window_id": window_id,
                    "accession": acc,
                    "source_description": desc,
                    "genome_length": genome_len,
                    "window_start_1based": start + 1,
                    "window_end_1based": end,
                    "window_length": len(window_seq),
                    "window_type": "real",
                })

    print(f"[INFO] Windows written: {n_windows}")
    print(f"[INFO] FASTA: {out_fasta}")
    print(f"[INFO] Metadata: {out_meta}")


if __name__ == "__main__":
    main()
