#!/usr/bin/env python3

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-flagged", required=True)
    parser.add_argument("--output-selected", required=True)
    parser.add_argument("--seed", type=int, default=84)
    parser.add_argument("--quota-ecoli-shigella", type=int, default=60)
    parser.add_argument("--quota-klebsiella", type=int, default=60)
    parser.add_argument("--quota-pseudomonas", type=int, default=45)
    parser.add_argument("--quota-acinetobacter", type=int, default=35)
    args = parser.parse_args()

    random.seed(args.seed)
    quotas = {
        "ecoli_shigella": args.quota_ecoli_shigella,
        "klebsiella_pneumoniae": args.quota_klebsiella,
        "pseudomonas_aeruginosa": args.quota_pseudomonas,
        "acinetobacter_baumannii": args.quota_acinetobacter,
    }

    with open(args.input, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = reader.fieldnames
        rows = list(reader)

    for row in rows:
        row["precurated_status_v0_1"] = "not_selected_precurated_v0_1"
        row["precurated_reason_v0_1"] = "outside_host_length_gc_quota"

    grouped = defaultdict(list)
    for row in rows:
        # If Mash redundancy annotations are present, only cluster representatives
        # are eligible for the precurated set. This avoids re-selecting redundant
        # genomes after clustering.
        redundancy_status = row.get("mash_redundancy_status_v0_1", "")
        if redundancy_status and redundancy_status != "representative":
            row["precurated_reason_v0_1"] = "mash_redundant_non_representative"
            continue
        grouped[row["host_group"]].append(row)

    selected = []

    for host_group, quota in quotas.items():
        host_rows = grouped.get(host_group, [])

        strata = defaultdict(list)
        for row in host_rows:
            key = (
                row.get("length_bin_v0_1", ""),
                row.get("gc_bin_v0_1", "")
            )
            strata[key].append(row)

        for key in strata:
            random.shuffle(strata[key])

        host_selected = []
        strata_keys = sorted(strata.keys())

        while len(host_selected) < quota:
            added = False
            for key in strata_keys:
                if strata[key] and len(host_selected) < quota:
                    host_selected.append(strata[key].pop())
                    added = True
            if not added:
                break

        for row in host_selected:
            row["precurated_status_v0_1"] = "selected_precurated_v0_1"
            row["precurated_reason_v0_1"] = "mash_representative_host_length_gc_quota"

        selected.extend(host_selected)

    new_fields = fieldnames + [
        "precurated_status_v0_1",
        "precurated_reason_v0_1",
    ]

    flagged_out = Path(args.output_flagged)
    selected_out = Path(args.output_selected)
    flagged_out.parent.mkdir(parents=True, exist_ok=True)
    selected_out.parent.mkdir(parents=True, exist_ok=True)

    with flagged_out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=new_fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    with selected_out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=new_fields, delimiter="\t")
        writer.writeheader()
        writer.writerows([r for r in rows if r["precurated_status_v0_1"] == "selected_precurated_v0_1"])

    print(f"[INFO] Input rows: {len(rows)}")
    print(f"[INFO] Selected rows: {len(selected)}")
    print(f"[INFO] Flagged output: {flagged_out}")
    print(f"[INFO] Selected output: {selected_out}")


if __name__ == "__main__":
    main()
