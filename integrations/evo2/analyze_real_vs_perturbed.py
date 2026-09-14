#!/usr/bin/env python3

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def parse_id(seq_id):
    parts = seq_id.split("|")
    perturb_type = "real"
    base_id = seq_id

    for p in parts:
        if p.startswith("perturb="):
            perturb_type = p.split("=", 1)[1]

    if perturb_type != "real":
        base_parts = [p for p in parts if not p.startswith("perturb=") and not p.startswith("seed=")]
        base_id = "|".join(base_parts)

    accession = parts[0] if parts else ""

    return {
        "id": seq_id,
        "base_window_id": base_id,
        "accession": accession,
        "perturb_type": perturb_type,
    }


def read_scores(path):
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            parsed = parse_id(row["id"])
            row.update(parsed)
            row["log_prob_seq"] = float(row["log_prob_seq"])
            row["log_prob_per_base"] = float(row["log_prob_per_base"])
            row["length"] = int(row["length"])
            rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", required=True)
    parser.add_argument("--output-annotated", required=True)
    parser.add_argument("--output-paired", required=True)
    parser.add_argument("--output-summary", required=True)
    args = parser.parse_args()

    rows = read_scores(args.scores)

    by_base = defaultdict(dict)
    for row in rows:
        by_base[row["base_window_id"]][row["perturb_type"]] = row

    annotated_fields = [
        "seq_idx",
        "id",
        "base_window_id",
        "accession",
        "perturb_type",
        "length",
        "log_prob_seq",
        "log_prob_per_base",
    ]

    out_annot = Path(args.output_annotated)
    out_pair = Path(args.output_paired)
    out_sum = Path(args.output_summary)
    out_annot.parent.mkdir(parents=True, exist_ok=True)
    out_pair.parent.mkdir(parents=True, exist_ok=True)
    out_sum.parent.mkdir(parents=True, exist_ok=True)

    with out_annot.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=annotated_fields, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({f: row.get(f, "") for f in annotated_fields})

    paired_fields = [
        "base_window_id",
        "accession",
        "perturb_type",
        "real_log_prob_per_base",
        "perturbed_log_prob_per_base",
        "delta_real_minus_perturbed",
        "real_higher_than_perturbed",
    ]

    paired_rows = []

    for base_id, group in by_base.items():
        if "real" not in group:
            continue

        real = group["real"]

        for perturb_type, pert in group.items():
            if perturb_type == "real":
                continue

            delta = real["log_prob_per_base"] - pert["log_prob_per_base"]

            paired_rows.append({
                "base_window_id": base_id,
                "accession": real["accession"],
                "perturb_type": perturb_type,
                "real_log_prob_per_base": real["log_prob_per_base"],
                "perturbed_log_prob_per_base": pert["log_prob_per_base"],
                "delta_real_minus_perturbed": delta,
                "real_higher_than_perturbed": "yes" if delta > 0 else "no",
            })

    with out_pair.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=paired_fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(paired_rows)

    by_perturb = defaultdict(list)
    for row in paired_rows:
        by_perturb[row["perturb_type"]].append(float(row["delta_real_minus_perturbed"]))

    with out_sum.open("w", encoding="utf-8") as handle:
        handle.write("metric\tvalue\n")
        handle.write(f"n_score_rows\t{len(rows)}\n")
        handle.write(f"n_base_windows\t{len(by_base)}\n")
        handle.write(f"n_paired_comparisons\t{len(paired_rows)}\n")

        counts = defaultdict(int)
        for row in rows:
            counts[row["perturb_type"]] += 1

        for k in sorted(counts):
            handle.write(f"n_{k}\t{counts[k]}\n")

        for perturb_type in sorted(by_perturb):
            values = by_perturb[perturb_type]
            n = len(values)
            mean_delta = sum(values) / n if n else 0
            n_real_higher = sum(1 for v in values if v > 0)

            handle.write(f"{perturb_type}_n_pairs\t{n}\n")
            handle.write(f"{perturb_type}_mean_delta_real_minus_perturbed\t{mean_delta}\n")
            handle.write(f"{perturb_type}_n_real_higher\t{n_real_higher}\n")
            handle.write(f"{perturb_type}_fraction_real_higher\t{n_real_higher / n if n else 0}\n")

    print(f"[INFO] Score rows: {len(rows)}")
    print(f"[INFO] Base windows: {len(by_base)}")
    print(f"[INFO] Paired comparisons: {len(paired_rows)}")
    print(f"[INFO] Annotated output: {out_annot}")
    print(f"[INFO] Paired output: {out_pair}")
    print(f"[INFO] Summary output: {out_sum}")


if __name__ == "__main__":
    main()
