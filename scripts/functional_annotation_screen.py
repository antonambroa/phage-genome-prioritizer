#!/usr/bin/env python3

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path


def load_accessions(path):
    with open(path, "r", encoding="utf-8") as handle:
        return {line.strip() for line in handle if line.strip()}


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def lower(s):
    return norm(s).lower()


def get_range_text(obj):
    ranges = obj.get("range", []) if isinstance(obj, dict) else []
    parts = []
    for r in ranges:
        b = r.get("begin", "")
        e = r.get("end", "")
        if b or e:
            parts.append(f"{b}-{e}")
    return ";".join(parts)


def classify_text(text):
    t = lower(text)

    # Stronger lifestyle / temperate markers
    lifestyle_terms = [
        "integrase",
        "excisionase",
        "lysogen",
        "lysogenic",
        "prophage",
        "repressor",
        "ci repressor",
        "c1 repressor",
        "cro repressor",
        "immunity repressor",
        "site-specific recombinase",
    ]

    # Safety-oriented markers
    safety_terms = [
        "toxin",
        "cytotoxin",
        "enterotoxin",
        "hemolysin",
        "haemolysin",
        "virulence",
        "pathogenicity",
        "resistance",
        "antibiotic",
        "beta-lactamase",
        "betalactamase",
        "carbapenemase",
        "aminoglycoside",
        "efflux",
    ]

    # Mobile element markers; review, not automatic exclusion
    mobile_terms = [
        "transposase",
        "insertion sequence",
        "resolvase",
        "recombinase",
        "conjug",
        "plasmid",
    ]

    structural_terms = [
        "terminase",
        "portal",
        "capsid",
        "head",
        "tail",
        "baseplate",
        "fiber",
        "fibres",
        "neck",
        "collar",
        "tape measure",
        "scaffold",
        "packaging",
    ]

    lysis_terms = [
        "holin",
        "endolysin",
        "lysin",
        "spanin",
        "amidase",
        "muramidase",
        "peptidoglycan",
    ]

    replication_terms = [
        "polymerase",
        "helicase",
        "primase",
        "ligase",
        "nuclease",
        "exonuclease",
        "ribonucleotide reductase",
        "replication",
        "dna-binding",
        "single-stranded dna-binding",
    ]

    def hits(terms):
        return [x for x in terms if x in t]

    lifestyle_hits = hits(lifestyle_terms)
    safety_hits = hits(safety_terms)
    mobile_hits = hits(mobile_terms)
    structural_hits = hits(structural_terms)
    lysis_hits = hits(lysis_terms)
    replication_hits = hits(replication_terms)

    flags = []
    if lifestyle_hits:
        flags.append("lifestyle_signal")
    if safety_hits:
        flags.append("safety_signal")
    if mobile_hits:
        flags.append("mobile_element_signal")
    if structural_hits:
        flags.append("structural_module_signal")
    if lysis_hits:
        flags.append("lysis_module_signal")
    if replication_hits:
        flags.append("replication_module_signal")

    keyword_hits = sorted(set(
        lifestyle_hits + safety_hits + mobile_hits +
        structural_hits + lysis_hits + replication_hits
    ))

    return ";".join(flags), ";".join(keyword_hits)


def iter_cds_records(annotation_record):
    accession = annotation_record.get("accession", "")
    isolate_name = annotation_record.get("isolateName", "")

    for gene in annotation_record.get("genes", []) or []:
        gene_name = gene.get("name", "")

        for cds in gene.get("cds", []) or []:
            cds_name = cds.get("name", "")

            nuc = cds.get("nucleotide", {}) or {}
            prot = cds.get("protein", {}) or {}

            nuc_acc = nuc.get("accessionVersion", "")
            nuc_seqid = nuc.get("seqId", "")
            nuc_range = get_range_text(nuc)
            nuc_title = nuc.get("title", "")

            protein_acc = prot.get("accessionVersion", "")
            protein_seqid = prot.get("seqId", "")
            protein_range = get_range_text(prot)
            protein_title = prot.get("title", "")

            combined_text = " | ".join([
                gene_name,
                cds_name,
                nuc_title,
                protein_title,
            ])

            flags, keyword_hits = classify_text(combined_text)

            yield {
                "accession": accession,
                "isolate_name": isolate_name,
                "gene_name": gene_name,
                "cds_name": cds_name,
                "nucleotide_accession": nuc_acc,
                "nucleotide_seqid": nuc_seqid,
                "nucleotide_range": nuc_range,
                "protein_accession": protein_acc,
                "protein_seqid": protein_seqid,
                "protein_range": protein_range,
                "product_text": combined_text,
                "category_flags": flags,
                "keyword_hits": keyword_hits,
            }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotation-report", required=True)
    parser.add_argument("--accessions", required=True)
    parser.add_argument("--output-cds", required=True)
    parser.add_argument("--output-summary", required=True)
    args = parser.parse_args()

    wanted = load_accessions(args.accessions)

    cds_rows = []
    summary = defaultdict(lambda: {
        "n_cds": 0,
        "n_lifestyle_signal": 0,
        "n_safety_signal": 0,
        "n_mobile_element_signal": 0,
        "n_structural_module_signal": 0,
        "n_lysis_module_signal": 0,
        "n_replication_module_signal": 0,
        "keyword_hits": set(),
        "flagged_products": set(),
        "has_annotation_record": False,
    })

    seen_annotation_records = set()

    with open(args.annotation_report, "r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue

            rec = json.loads(line)
            acc = rec.get("accession", "")

            if acc not in wanted:
                continue

            seen_annotation_records.add(acc)
            summary[acc]["has_annotation_record"] = True

            for row in iter_cds_records(rec):
                cds_rows.append(row)

                s = summary[acc]
                s["n_cds"] += 1

                flags = row["category_flags"].split(";") if row["category_flags"] else []
                kws = row["keyword_hits"].split(";") if row["keyword_hits"] else []

                for k in kws:
                    if k:
                        s["keyword_hits"].add(k)

                if "lifestyle_signal" in flags:
                    s["n_lifestyle_signal"] += 1
                    s["flagged_products"].add(row["product_text"])
                if "safety_signal" in flags:
                    s["n_safety_signal"] += 1
                    s["flagged_products"].add(row["product_text"])
                if "mobile_element_signal" in flags:
                    s["n_mobile_element_signal"] += 1
                    s["flagged_products"].add(row["product_text"])
                if "structural_module_signal" in flags:
                    s["n_structural_module_signal"] += 1
                if "lysis_module_signal" in flags:
                    s["n_lysis_module_signal"] += 1
                if "replication_module_signal" in flags:
                    s["n_replication_module_signal"] += 1

    out_cds = Path(args.output_cds)
    out_summary = Path(args.output_summary)
    out_cds.parent.mkdir(parents=True, exist_ok=True)
    out_summary.parent.mkdir(parents=True, exist_ok=True)

    cds_fields = [
        "accession",
        "isolate_name",
        "gene_name",
        "cds_name",
        "nucleotide_accession",
        "nucleotide_seqid",
        "nucleotide_range",
        "protein_accession",
        "protein_seqid",
        "protein_range",
        "product_text",
        "category_flags",
        "keyword_hits",
    ]

    with out_cds.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=cds_fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(cds_rows)

    summary_fields = [
        "accession",
        "has_annotation_record",
        "n_cds",
        "n_lifestyle_signal",
        "n_safety_signal",
        "n_mobile_element_signal",
        "n_structural_module_signal",
        "n_lysis_module_signal",
        "n_replication_module_signal",
        "keyword_hits",
        "flagged_products",
        "functional_screen_decision_v0_1",
        "functional_screen_reason_v0_1",
    ]

    with out_summary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=summary_fields, delimiter="\t")
        writer.writeheader()

        for acc in sorted(wanted):
            s = summary[acc]

            reasons = []
            if not s["has_annotation_record"]:
                reasons.append("missing_annotation_record")
            if s["n_cds"] == 0:
                reasons.append("no_cds_in_annotation_report")
            if s["n_lifestyle_signal"] > 0:
                reasons.append("lifestyle_signal_detected")
            if s["n_safety_signal"] > 0:
                reasons.append("safety_signal_detected")
            if s["n_mobile_element_signal"] > 0:
                reasons.append("mobile_element_signal_detected")

            if reasons:
                decision = "review_functional_screen_v0_1"
                reason = ";".join(reasons)
            else:
                decision = "pass_functional_screen_v0_1"
                reason = "pass"

            writer.writerow({
                "accession": acc,
                "has_annotation_record": s["has_annotation_record"],
                "n_cds": s["n_cds"],
                "n_lifestyle_signal": s["n_lifestyle_signal"],
                "n_safety_signal": s["n_safety_signal"],
                "n_mobile_element_signal": s["n_mobile_element_signal"],
                "n_structural_module_signal": s["n_structural_module_signal"],
                "n_lysis_module_signal": s["n_lysis_module_signal"],
                "n_replication_module_signal": s["n_replication_module_signal"],
                "keyword_hits": ";".join(sorted(s["keyword_hits"])),
                "flagged_products": " || ".join(sorted(s["flagged_products"])),
                "functional_screen_decision_v0_1": decision,
                "functional_screen_reason_v0_1": reason,
            })

    print(f"[INFO] Wanted accessions: {len(wanted)}")
    print(f"[INFO] Annotation records found: {len(seen_annotation_records)}")
    print(f"[INFO] CDS rows written: {len(cds_rows)}")
    print(f"[INFO] CDS output: {out_cds}")
    print(f"[INFO] Summary output: {out_summary}")


if __name__ == "__main__":
    main()
