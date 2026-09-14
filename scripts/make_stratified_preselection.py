#!/usr/bin/env python3

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path



def length_bin(length_bp):
    length_bp = int(float(length_bp))

    if length_bp < 40000:
        return "lt_40kb"
    if length_bp < 70000:
        return "40kb_70kb"
    if length_bp < 120000:
        return "70kb_120kb"
    return "120kb_300kb"


def gc_bin(gc_percent):
    gc = float(gc_percent)

    if gc < 40:
        return "gc_lt_40"
    if gc < 45:
        return "gc_40_45"
    if gc < 50:
        return "gc_45_50"
    if gc < 55:
        return "gc_50_55"
    return "gc_gt_55"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--quota-ecoli-shigella", type=int, default=250)
    parser.add_argument("--quota-klebsiella", type=int, default=250)
    parser.add_argument("--quota-pseudomonas", type=int, default=200)
    parser.add_argument("--quota-acinetobacter", type=int, default=150)
    args = parser.parse_args()

    random.seed(args.seed)
    quotas = {
        "ecoli_shigella": args.quota_ecoli_shigella,
        "klebsiella_pneumoniae": args.quota_klebsiella,
        "pseudomonas_aeruginosa": args.quota_pseudomonas,
        "acinetobacter_baumannii": args.quota_acinetobacter,
    }

    rows = []
    with open(args.input, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = reader.fieldnames

        for row in reader:
            row["length_bin_v0_1"] = length_bin(row["length_bp"])
            row["gc_bin_v0_1"] = gc_bin(row["gc_percent"])
            row["preselection_status_v0_1"] = "not_selected"
            row["preselection_reason_v0_1"] = ""
            rows.append(row)

    grouped = defaultdict(list)
    for row in rows:
        grouped[row["host_group"]].append(row)

    selected_accessions = set()

    for host_group, quota in quotas.items():
        host_rows = grouped.get(host_group, [])

        strata = defaultdict(list)
        for row in host_rows:
            key = (row["length_bin_v0_1"], row["gc_bin_v0_1"])
            strata[key].append(row)

        # Shuffle within each stratum for deterministic but unbiased-ish selection.
        for key in strata:
            random.shuffle(strata[key])

        selected = []

        # Round-robin across strata to avoid selecting only the largest length/GC class.
        strata_keys = sorted(strata.keys())
        while len(selected) < quota:
            added = False
            for key in strata_keys:
                if strata[key] and len(selected) < quota:
                    selected.append(strata[key].pop())
                    added = True
            if not added:
                break

        for row in selected:
            selected_accessions.add(row["accession"])

    for row in rows:
        if row["accession"] in selected_accessions:
            row["preselection_status_v0_1"] = "selected_preselection_v0_1"
            row["preselection_reason_v0_1"] = "host_length_gc_stratified_quota"
        else:
            row["preselection_status_v0_1"] = "not_selected_preselection_v0_1"
            row["preselection_reason_v0_1"] = "outside_host_quota"

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    new_fields = fieldnames + [
        "length_bin_v0_1",
        "gc_bin_v0_1",
        "preselection_status_v0_1",
        "preselection_reason_v0_1",
    ]

    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=new_fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    print(f"[INFO] Input rows: {len(rows)}")
    print(f"[INFO] Selected rows: {len(selected_accessions)}")
    print(f"[INFO] Output: {out}")


if __name__ == "__main__":
    main()
