#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path


def load_functional_summary(path):
    data = {}
    with open(path, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            data[row["accession"]] = row
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--functional-summary", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    functional = load_functional_summary(args.functional_summary)

    with open(args.inventory, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        old_fields = reader.fieldnames
        rows = list(reader)

    new_fields = old_fields + [
        "functional_has_annotation_record",
        "functional_n_cds",
        "functional_n_lifestyle_signal",
        "functional_n_safety_signal",
        "functional_n_mobile_element_signal",
        "functional_n_structural_module_signal",
        "functional_n_lysis_module_signal",
        "functional_n_replication_module_signal",
        "functional_keyword_hits",
        "functional_flagged_products",
        "functional_screen_decision_v0_1",
        "functional_screen_reason_v0_1",
    ]

    missing = 0

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8", newline="") as o:
        writer = csv.DictWriter(o, fieldnames=new_fields, delimiter="\t")
        writer.writeheader()

        for row in rows:
            acc = row["accession"]
            f = functional.get(acc)

            if f is None:
                missing += 1
                row.update({
                    "functional_has_annotation_record": "",
                    "functional_n_cds": "",
                    "functional_n_lifestyle_signal": "",
                    "functional_n_safety_signal": "",
                    "functional_n_mobile_element_signal": "",
                    "functional_n_structural_module_signal": "",
                    "functional_n_lysis_module_signal": "",
                    "functional_n_replication_module_signal": "",
                    "functional_keyword_hits": "",
                    "functional_flagged_products": "",
                    "functional_screen_decision_v0_1": "review_functional_screen_v0_1",
                    "functional_screen_reason_v0_1": "missing_functional_summary",
                })
            else:
                row.update({
                    "functional_has_annotation_record": f.get("has_annotation_record", ""),
                    "functional_n_cds": f.get("n_cds", ""),
                    "functional_n_lifestyle_signal": f.get("n_lifestyle_signal", ""),
                    "functional_n_safety_signal": f.get("n_safety_signal", ""),
                    "functional_n_mobile_element_signal": f.get("n_mobile_element_signal", ""),
                    "functional_n_structural_module_signal": f.get("n_structural_module_signal", ""),
                    "functional_n_lysis_module_signal": f.get("n_lysis_module_signal", ""),
                    "functional_n_replication_module_signal": f.get("n_replication_module_signal", ""),
                    "functional_keyword_hits": f.get("keyword_hits", ""),
                    "functional_flagged_products": f.get("flagged_products", ""),
                    "functional_screen_decision_v0_1": f.get("functional_screen_decision_v0_1", ""),
                    "functional_screen_reason_v0_1": f.get("functional_screen_reason_v0_1", ""),
                })

            writer.writerow(row)

    print(f"[INFO] Inventory rows: {len(rows)}")
    print(f"[INFO] Functional summary rows: {len(functional)}")
    print(f"[INFO] Missing functional rows: {missing}")
    print(f"[INFO] Output: {out}")


if __name__ == "__main__":
    main()
