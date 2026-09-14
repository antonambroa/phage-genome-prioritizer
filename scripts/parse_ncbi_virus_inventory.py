#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
import csv
from typing import Any


def find_first(obj, candidate_keys):
    """
    Recursively search for the first value associated with any candidate key.
    This is intentionally permissive because NCBI Datasets JSON schemas may vary.
    """
    if isinstance(obj, dict):
        for key in candidate_keys:
            if key in obj and obj[key] not in (None, "", [], {}):
                return obj[key]
        for value in obj.values():
            found = find_first(value, candidate_keys)
            if found not in (None, "", [], {}):
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_first(item, candidate_keys)
            if found not in (None, "", [], {}):
                return found
    return None


def stringify(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input NCBI Datasets JSONL file")
    parser.add_argument("--output-tsv", required=True, help="Output TSV inventory")
    parser.add_argument("--source-label", required=True, help="Label for the source subset")
    args = parser.parse_args()

    infile = Path(args.input)
    outfile = Path(args.output_tsv)
    outfile.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "internal_id",
        "source_label",
        "accession",
        "accession_version",
        "organism_name",
        "tax_id",
        "host",
        "isolate",
        "biosample",
        "bioproject",
        "geo_location",
        "collection_date",
        "genome_length",
        "is_complete",
        "is_annotated",
        "nuc_completeness",
        "assembly_level",
        "genbank_accession",
        "refseq_accession",
        "raw_json_compact",
    ]

    accession_seen = set()
    rows = []

    with infile.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue

            rec = json.loads(line)

            accession = find_first(rec, [
                "accession",
                "nucleotide_accession",
                "genbankAccession",
                "genbank_accession",
                "refseqAccession",
                "refseq_accession",
            ])

            accession_version = find_first(rec, [
                "accessionVersion",
                "accession_version",
                "nucleotide_accession_version",
            ])

            organism_name = find_first(rec, [
                "organismName",
                "organism_name",
                "virus_name",
                "sci_name",
                "scientificName",
                "title",
            ])

            tax_id = find_first(rec, [
                "taxId",
                "tax_id",
                "taxid",
            ])

            host = find_first(rec, [
                "host",
                "hosts",
                "hostName",
                "host_name",
            ])

            isolate = find_first(rec, [
                "isolate",
                "strain",
            ])

            biosample = find_first(rec, [
                "biosample",
                "biosampleAccession",
                "biosample_accession",
            ])

            bioproject = find_first(rec, [
                "bioproject",
                "bioprojectAccession",
                "bioproject_accession",
            ])

            geo_location = find_first(rec, [
                "geoLocation",
                "geo_location",
                "country",
                "location",
            ])

            collection_date = find_first(rec, [
                "collectionDate",
                "collection_date",
                "isolation_date",
            ])

            genome_length = find_first(rec, [
                "length",
                "genomeLength",
                "genome_length",
                "sequenceLength",
                "sequence_length",
            ])

            is_complete = find_first(rec, [
                "isComplete",
                "is_complete",
                "complete",
            ])

            is_annotated = find_first(rec, [
                "isAnnotated",
                "is_annotated",
                "annotated",
            ])

            nuc_completeness = find_first(rec, [
                "nucCompleteness",
                "nuc_completeness",
                "completeness",
            ])

            assembly_level = find_first(rec, [
                "assemblyLevel",
                "assembly_level",
            ])

            genbank_accession = find_first(rec, [
                "genbankAccession",
                "genbank_accession",
            ])

            refseq_accession = find_first(rec, [
                "refseqAccession",
                "refseq_accession",
            ])

            acc_key = stringify(accession or accession_version or genbank_accession or refseq_accession)

            if acc_key and acc_key in accession_seen:
                continue
            if acc_key:
                accession_seen.add(acc_key)

            internal_id = f"NCBI_CAUDO_{len(rows)+1:06d}"

            row = {
                "internal_id": internal_id,
                "source_label": args.source_label,
                "accession": stringify(accession),
                "accession_version": stringify(accession_version),
                "organism_name": stringify(organism_name),
                "tax_id": stringify(tax_id),
                "host": stringify(host),
                "isolate": stringify(isolate),
                "biosample": stringify(biosample),
                "bioproject": stringify(bioproject),
                "geo_location": stringify(geo_location),
                "collection_date": stringify(collection_date),
                "genome_length": stringify(genome_length),
                "is_complete": stringify(is_complete),
                "is_annotated": stringify(is_annotated),
                "nuc_completeness": stringify(nuc_completeness),
                "assembly_level": stringify(assembly_level),
                "genbank_accession": stringify(genbank_accession),
                "refseq_accession": stringify(refseq_accession),
                "raw_json_compact": json.dumps(rec, ensure_ascii=False, separators=(",", ":")),
            }
            rows.append(row)

    with outfile.open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    print(f"[INFO] Input: {infile}")
    print(f"[INFO] Output: {outfile}")
    print(f"[INFO] Rows written: {len(rows)}")


if __name__ == "__main__":
    main()
