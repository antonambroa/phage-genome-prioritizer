from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name, filename):
    spec = spec_from_file_location(name, ROOT / "scripts" / filename)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_host_group_normalization():
    m = load_script("hosts", "add_host_groups.py")
    assert m.normalize_host_group("Escherichia coli") == "ecoli_shigella"
    assert m.normalize_host_group("Shigella flexneri") == "ecoli_shigella"
    assert m.normalize_host_group("Klebsiella pneumoniae") == "klebsiella_pneumoniae"


def test_length_and_gc_bins():
    m = load_script("selection", "make_stratified_preselection.py")
    assert m.length_bin(39999) == "lt_40kb"
    assert m.length_bin(40000) == "40kb_70kb"
    assert m.gc_bin(44.9) == "gc_40_45"
    assert m.gc_bin(55) == "gc_gt_55"


def test_checkv_thresholds_are_configurable():
    m = load_script("checkv", "merge_checkv_results.py")
    row = {"checkv_quality": "High-quality", "contamination": "0.5", "completeness": "95", "provirus": "No"}
    decision, _ = m.checkv_decision(row, min_completeness=90, max_contamination=1)
    assert decision == "pass_checkv_v0_1"
    decision, reason = m.checkv_decision(row, min_completeness=96, max_contamination=1)
    assert decision != "pass_checkv_v0_1"
    assert "completeness" in reason


def test_union_find_clusters():
    m = load_script("mash", "build_mash_redundancy_clusters.py")
    uf = m.UnionFind()
    uf.union("A", "B")
    uf.union("B", "C")
    assert uf.find("A") == uf.find("C")
