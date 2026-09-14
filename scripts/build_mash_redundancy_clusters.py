#!/usr/bin/env python3

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from datetime import datetime


def parse_date(value):
    if not value:
        return datetime.min

    value = value.replace("Z", "")
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return datetime.min


class UnionFind:
    def __init__(self):
        self.parent = {}

    def add(self, x):
        if x not in self.parent:
            self.parent[x] = x

    def find(self, x):
        self.add(x)
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a, b):
        ra = self.find(a)
        rb = self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def load_inventory(path):
    rows = {}
    with open(path, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = reader.fieldnames
        for row in reader:
            rows[row["accession"]] = row
    return rows, fieldnames


def choose_representative(cluster_accessions, inventory):
    """
    Deterministic representative choice for redundancy clusters.

    Preference order:
    1. RefSeq over GenBank if present.
    2. Empty notes over non-empty notes.
    3. More recent update_date.
    4. Higher protein_count_ncbi.
    5. Lexicographically smallest accession.
    """
    def key(acc):
        row = inventory.get(acc, {})
        source = row.get("source_database", "")
        notes = row.get("notes", "")
        update_date = parse_date(row.get("update_date", ""))
        try:
            protein_count = int(float(row.get("protein_count_ncbi", 0) or 0))
        except Exception:
            protein_count = 0

        is_refseq = 1 if source.lower() == "refseq" else 0
        notes_empty = 1 if notes == "" else 0

        return (
            is_refseq,
            notes_empty,
            update_date,
            protein_count,
            "".join(chr(255 - ord(c)) for c in acc)
        )

    return max(cluster_accessions, key=key)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--pairs", required=True)
    parser.add_argument("--clusters-output", required=True)
    parser.add_argument("--flagged-inventory-output", required=True)
    args = parser.parse_args()

    inventory, inventory_fields = load_inventory(args.inventory)

    uf = UnionFind()

    # Add all preselection accessions, including singletons.
    for acc in inventory:
        uf.add(acc)

    # Add redundancy edges.
    with open(args.pairs, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            a = row["accession_a"]
            b = row["accession_b"]
            uf.union(a, b)

    clusters = defaultdict(list)
    for acc in inventory:
        root = uf.find(acc)
        clusters[root].append(acc)

    # Sort clusters by size descending, then first accession.
    cluster_items = sorted(
        clusters.values(),
        key=lambda x: (-len(x), sorted(x)[0])
    )

    cluster_id_by_acc = {}
    representative_by_cluster = {}
    cluster_size_by_cluster = {}

    clusters_out = Path(args.clusters_output)
    clusters_out.parent.mkdir(parents=True, exist_ok=True)

    with clusters_out.open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "mash_cluster_id",
            "cluster_size",
            "representative_accession",
            "accession",
            "is_representative",
            "host_group",
            "phage_name",
            "length_bp",
            "gc_percent",
            "source_database",
            "update_date",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()

        for idx, accessions in enumerate(cluster_items, start=1):
            cluster_id = f"MASHC_{idx:05d}"
            rep = choose_representative(accessions, inventory)
            size = len(accessions)

            representative_by_cluster[cluster_id] = rep
            cluster_size_by_cluster[cluster_id] = size

            for acc in sorted(accessions):
                cluster_id_by_acc[acc] = cluster_id
                row = inventory.get(acc, {})
                writer.writerow({
                    "mash_cluster_id": cluster_id,
                    "cluster_size": size,
                    "representative_accession": rep,
                    "accession": acc,
                    "is_representative": "yes" if acc == rep else "no",
                    "host_group": row.get("host_group", ""),
                    "phage_name": row.get("phage_name", ""),
                    "length_bp": row.get("length_bp", ""),
                    "gc_percent": row.get("gc_percent", ""),
                    "source_database": row.get("source_database", ""),
                    "update_date": row.get("update_date", ""),
                })

    flagged_out = Path(args.flagged_inventory_output)
    flagged_out.parent.mkdir(parents=True, exist_ok=True)

    new_fields = inventory_fields + [
        "mash_cluster_id_v0_1",
        "mash_cluster_size_v0_1",
        "mash_representative_accession_v0_1",
        "mash_redundancy_status_v0_1",
    ]

    with flagged_out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=new_fields, delimiter="\t")
        writer.writeheader()

        for acc, row in inventory.items():
            cluster_id = cluster_id_by_acc[acc]
            size = cluster_size_by_cluster[cluster_id]
            rep = representative_by_cluster[cluster_id]

            row = dict(row)
            row["mash_cluster_id_v0_1"] = cluster_id
            row["mash_cluster_size_v0_1"] = size
            row["mash_representative_accession_v0_1"] = rep
            row["mash_redundancy_status_v0_1"] = (
                "representative" if acc == rep else "redundant_non_representative"
            )

            writer.writerow(row)

    n_clusters = len(cluster_items)
    n_singletons = sum(1 for c in cluster_items if len(c) == 1)
    n_redundant_clusters = sum(1 for c in cluster_items if len(c) > 1)
    largest = max(len(c) for c in cluster_items)

    print(f"[INFO] Inventory records: {len(inventory)}")
    print(f"[INFO] Clusters: {n_clusters}")
    print(f"[INFO] Singleton clusters: {n_singletons}")
    print(f"[INFO] Redundant clusters: {n_redundant_clusters}")
    print(f"[INFO] Largest cluster size: {largest}")
    print(f"[INFO] Clusters output: {clusters_out}")
    print(f"[INFO] Flagged inventory output: {flagged_out}")


if __name__ == "__main__":
    main()
