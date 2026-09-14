#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path


def normalize_host_group(host):
    h = host.strip().lower()

    if h in {"escherichia coli", "shigella"} or h.startswith("shigella"):
        return "ecoli_shigella"

    if h == "klebsiella pneumoniae":
        return "klebsiella_pneumoniae"

    if h == "pseudomonas aeruginosa":
        return "pseudomonas_aeruginosa"

    if h == "acinetobacter baumannii":
        return "acinetobacter_baumannii"

    return "other_or_unexpected"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    inp = Path(args.input)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    with inp.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        old_fields = reader.fieldnames

        new_fields = []
        inserted = False
        for f in old_fields:
            new_fields.append(f)
            if f == "host_organism_name":
                new_fields.append("host_group")
                inserted = True

        if not inserted:
            new_fields.append("host_group")

        with out.open("w", encoding="utf-8", newline="") as o:
            writer = csv.DictWriter(o, fieldnames=new_fields, delimiter="\t")
            writer.writeheader()

            for row in reader:
                row["host_group"] = normalize_host_group(row.get("host_organism_name", ""))
                writer.writerow(row)

    print(f"[INFO] Output: {out}")


if __name__ == "__main__":
    main()
