#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path


def load_checkv(path):
    rows = {}
    with open(path, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            rows[row["contig_id"]] = row
    return rows


def parse_float(value):
    if value in ("", "NA", None):
        return None
    try:
        return float(value)
    except Exception:
        return None


def checkv_decision(row, min_completeness=90.0, max_contamination=0.0):
    quality = row.get("checkv_quality", "")
    contamination = parse_float(row.get("contamination", ""))
    completeness = parse_float(row.get("completeness", ""))
    provirus = row.get("provirus", "")

    reasons = []

    if quality not in {"Complete", "High-quality", "Medium-quality"}:
        reasons.append("checkv_quality_below_medium")

    if contamination is not None and contamination > max_contamination:
        reasons.append(f"checkv_contamination_gt_{max_contamination:g}")

    if completeness is not None and completeness < min_completeness:
        reasons.append(f"checkv_completeness_lt_{min_completeness:g}")

    if provirus == "Yes":
        reasons.append("checkv_predicted_provirus")

    if reasons:
        return "review_or_exclude_checkv_v0_1", ";".join(reasons)

    return "pass_checkv_v0_1", "pass"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--checkv-quality-summary", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--min-completeness", type=float, default=90.0,
                        help="Minimum CheckV completeness percentage (default: 90)")
    parser.add_argument("--max-contamination", type=float, default=0.0,
                        help="Maximum CheckV contamination percentage (default: 0)")
    args = parser.parse_args()

    checkv = load_checkv(args.checkv_quality_summary)

    with open(args.inventory, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        old_fields = reader.fieldnames
        rows = list(reader)

    new_fields = old_fields + [
        "checkv_contig_id",
        "checkv_contig_length",
        "checkv_provirus",
        "checkv_proviral_length",
        "checkv_gene_count",
        "checkv_viral_genes",
        "checkv_host_genes",
        "checkv_quality",
        "checkv_miuvig_quality",
        "checkv_completeness",
        "checkv_completeness_method",
        "checkv_contamination",
        "checkv_kmer_freq",
        "checkv_warnings",
        "checkv_decision_v0_1",
        "checkv_decision_reason_v0_1",
    ]

    missing = 0

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8", newline="") as o:
        writer = csv.DictWriter(o, fieldnames=new_fields, delimiter="\t")
        writer.writeheader()

        for row in rows:
            acc = row["accession"]
            cv = checkv.get(acc)

            if cv is None:
                missing += 1
                row.update({
                    "checkv_contig_id": "",
                    "checkv_contig_length": "",
                    "checkv_provirus": "",
                    "checkv_proviral_length": "",
                    "checkv_gene_count": "",
                    "checkv_viral_genes": "",
                    "checkv_host_genes": "",
                    "checkv_quality": "",
                    "checkv_miuvig_quality": "",
                    "checkv_completeness": "",
                    "checkv_completeness_method": "",
                    "checkv_contamination": "",
                    "checkv_kmer_freq": "",
                    "checkv_warnings": "",
                    "checkv_decision_v0_1": "review_checkv_missing",
                    "checkv_decision_reason_v0_1": "missing_in_checkv_quality_summary",
                })
            else:
                decision, reason = checkv_decision(cv, args.min_completeness, args.max_contamination)

                row.update({
                    "checkv_contig_id": cv.get("contig_id", ""),
                    "checkv_contig_length": cv.get("contig_length", ""),
                    "checkv_provirus": cv.get("provirus", ""),
                    "checkv_proviral_length": cv.get("proviral_length", ""),
                    "checkv_gene_count": cv.get("gene_count", ""),
                    "checkv_viral_genes": cv.get("viral_genes", ""),
                    "checkv_host_genes": cv.get("host_genes", ""),
                    "checkv_quality": cv.get("checkv_quality", ""),
                    "checkv_miuvig_quality": cv.get("miuvig_quality", ""),
                    "checkv_completeness": cv.get("completeness", ""),
                    "checkv_completeness_method": cv.get("completeness_method", ""),
                    "checkv_contamination": cv.get("contamination", ""),
                    "checkv_kmer_freq": cv.get("kmer_freq", ""),
                    "checkv_warnings": cv.get("warnings", ""),
                    "checkv_decision_v0_1": decision,
                    "checkv_decision_reason_v0_1": reason,
                })

            writer.writerow(row)

    print(f"[INFO] Inventory records: {len(rows)}")
    print(f"[INFO] CheckV records: {len(checkv)}")
    print(f"[INFO] Missing CheckV records: {missing}")
    print(f"[INFO] Output: {out}")


if __name__ == "__main__":
    main()
