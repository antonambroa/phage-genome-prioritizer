#!/usr/bin/env python3

import argparse
import csv
import json
from pathlib import Path


def as_json(value):
    if value in (None, "", [], {}):
        return ""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def get_nested(d, keys, default=""):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    if cur in (None, "", [], {}):
        return default
    return cur


def clean_phage_name(description):
    desc = description.strip()
    if desc.endswith(", complete genome"):
        desc = desc[:-len(", complete genome")]
    if desc.endswith(" complete genome"):
        desc = desc[:-len(" complete genome")]
    return desc.strip()


def load_fasta_headers(fasta):
    headers = {}
    with open(fasta, "r", encoding="utf-8") as handle:
        for line in handle:
            if not line.startswith(">"):
                continue

            header = line[1:].strip()
            parts = header.split(maxsplit=1)
            accession = parts[0]
            description = parts[1] if len(parts) > 1 else ""

            headers[accession] = {
                "fasta_description": description,
                "phage_name_from_fasta": clean_phage_name(description),
            }

    return headers


def load_qc(qc_tsv):
    qc = {}
    with open(qc_tsv, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            qc[row["accession"]] = row
    return qc


def load_data_report(data_report_jsonl):
    records = {}

    with open(data_report_jsonl, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue

            rec = json.loads(line)
            accession = rec.get("accession", "")

            virus = rec.get("virus", {}) or {}
            host = rec.get("host", {}) or {}
            isolate = rec.get("isolate", {}) or {}
            submitter = rec.get("submitter", {}) or {}
            nucleotide = rec.get("nucleotide", {}) or {}

            records[accession] = {
                "accession": accession,
                "virus_organism_name": virus.get("organismName", ""),
                "virus_tax_id": virus.get("taxId", ""),
                "virus_lineage": as_json(virus.get("lineage", "")),
                "host_organism_name": host.get("organismName", ""),
                "host_tax_id": host.get("taxId", ""),
                "host_lineage": as_json(host.get("lineage", "")),
                "isolate_name": isolate.get("name", "") if isinstance(isolate, dict) else "",
                "completeness_ncbi": rec.get("completeness", ""),
                "is_annotated_ncbi": rec.get("isAnnotated", ""),
                "gene_count_ncbi": rec.get("geneCount", ""),
                "protein_count_ncbi": rec.get("proteinCount", ""),
                "length_reported_ncbi": rec.get("length", ""),
                "sequence_hash_ncbi": nucleotide.get("sequenceHash", "") if isinstance(nucleotide, dict) else "",
                "source_database": rec.get("sourceDatabase", ""),
                "release_date": rec.get("releaseDate", ""),
                "update_date": rec.get("updateDate", ""),
                "submitter_country": submitter.get("country", "") if isinstance(submitter, dict) else "",
                "submitter_affiliation": submitter.get("affiliation", "") if isinstance(submitter, dict) else "",
                "submitter_names": as_json(submitter.get("names", "")) if isinstance(submitter, dict) else "",
            }

    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-report", required=True)
    parser.add_argument("--qc-flagged", required=True)
    parser.add_argument("--fasta", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    meta = load_data_report(args.data_report)
    qc = load_qc(args.qc_flagged)
    headers = load_fasta_headers(args.fasta)

    accessions = sorted(qc.keys())

    fields = [
        "internal_id",
        "accession",
        "phage_name",
        "virus_organism_name",
        "virus_tax_id",
        "virus_lineage",
        "fasta_description",
        "phage_name_from_fasta",
        "host_organism_name",
        "host_tax_id",
        "host_lineage",
        "isolate_name",
        "completeness_ncbi",
        "is_annotated_ncbi",
        "gene_count_ncbi",
        "protein_count_ncbi",
        "length_reported_ncbi",
        "length_bp",
        "gc_percent",
        "n_count",
        "sequence_hash_ncbi",
        "source_database",
        "release_date",
        "update_date",
        "submitter_country",
        "submitter_affiliation",
        "submitter_names",
        "basic_qc_decision",
        "basic_qc_reason",
        "dataset_stage",
        "curation_status",
        "notes",
    ]

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    missing_meta = 0
    missing_header = 0

    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()

        for i, acc in enumerate(accessions, start=1):
            m = meta.get(acc, {})
            q = qc.get(acc, {})
            h = headers.get(acc, {})

            if not m:
                missing_meta += 1
            if not h:
                missing_header += 1

            virus_name = m.get("virus_organism_name", "")
            fasta_name = h.get("phage_name_from_fasta", "")
            phage_name = virus_name or fasta_name

            notes = []
            if not m:
                notes.append("metadata_not_found_in_data_report")
            if not h:
                notes.append("fasta_header_not_found")
            if virus_name and fasta_name and virus_name != fasta_name:
                notes.append("virus_name_differs_from_fasta_name")

            row = {
                "internal_id": f"PHG_RAW_{i:06d}",
                "accession": acc,
                "phage_name": phage_name,
                "virus_organism_name": virus_name,
                "virus_tax_id": m.get("virus_tax_id", ""),
                "virus_lineage": m.get("virus_lineage", ""),
                "fasta_description": h.get("fasta_description", ""),
                "phage_name_from_fasta": fasta_name,
                "host_organism_name": m.get("host_organism_name", ""),
                "host_tax_id": m.get("host_tax_id", ""),
                "host_lineage": m.get("host_lineage", ""),
                "isolate_name": m.get("isolate_name", ""),
                "completeness_ncbi": m.get("completeness_ncbi", ""),
                "is_annotated_ncbi": m.get("is_annotated_ncbi", ""),
                "gene_count_ncbi": m.get("gene_count_ncbi", ""),
                "protein_count_ncbi": m.get("protein_count_ncbi", ""),
                "length_reported_ncbi": m.get("length_reported_ncbi", ""),
                "length_bp": q.get("length_bp", ""),
                "gc_percent": q.get("gc_percent", ""),
                "n_count": q.get("n_count", ""),
                "sequence_hash_ncbi": m.get("sequence_hash_ncbi", ""),
                "source_database": m.get("source_database", ""),
                "release_date": m.get("release_date", ""),
                "update_date": m.get("update_date", ""),
                "submitter_country": m.get("submitter_country", ""),
                "submitter_affiliation": m.get("submitter_affiliation", ""),
                "submitter_names": m.get("submitter_names", ""),
                "basic_qc_decision": q.get("basic_qc_decision", ""),
                "basic_qc_reason": q.get("basic_qc_reason", ""),
                "dataset_stage": "priority_host_raw_v0_1",
                "curation_status": "not_yet_curated",
                "notes": ";".join(notes),
            }

            writer.writerow(row)

    print(f"[INFO] Metadata records: {len(meta)}")
    print(f"[INFO] QC records: {len(qc)}")
    print(f"[INFO] FASTA header records: {len(headers)}")
    print(f"[INFO] Output records: {len(accessions)}")
    print(f"[INFO] Missing metadata: {missing_meta}")
    print(f"[INFO] Missing FASTA headers: {missing_header}")
    print(f"[INFO] Output: {out}")


if __name__ == "__main__":
    main()
