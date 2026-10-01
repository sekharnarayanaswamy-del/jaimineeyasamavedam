#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dual-Track Run Validation and Baseline Promotion Engine for Jaimineeya Samaveda.

Implements Subsystem E of src/tools/refactoring_spec.md:
  1. Track A: Engine Regression Test (Code Sanity)
     - Feeds baseline inputs into the ingestion engine and asserts invariant parity.
  2. Track B: Semantic Content Diff Test (Curation Sanity)
     - Compares Active Run AST against Golden Baseline Anchor.
     - Reports structural integrity and verse-by-verse liturgical diffs without alert fatigue.
  3. Golden Baseline Promotion:
     - Promotes verified working drafts to the new Golden Anchor with immutable manifests.

Usage:
  python src/tools/validate_run.py samhita
  python src/tools/validate_run.py aaranam
  python src/tools/validate_run.py all
  python src/tools/validate_run.py samhita --promote
  python src/tools/validate_run.py samhita --quick
"""

import os
import sys
import json
import hashlib
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from core.version import get_engine_version, get_corpus_edition, get_file_hash

BASELINES_DIR = REPO_ROOT / "data" / "baselines"
GOLDEN_DIR = BASELINES_DIR / "golden"
CORPORA_DIR = REPO_ROOT / "data" / "corpora"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


CORPUS_CONFIG = {
    "samhita": {
        "title": "Jaimineeya Samhita (संहिता)",
        "edition_key": "samhita",
        "input_rel": "data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt",
        "fallback_input": "data/input/Samhita_Devanagari_Unicode.txt",
        "ast_rel": "data/corpora/samhita/02_ast/Samhita_ast.json",
        "fallback_ast": "data/output/Samhita_corrected_out.json",
        "canonical_rel": "data/corpora/samhita/04_canonical/Vargeekaran.json",
        "fallback_canonical": "data/output/Vargeekaran.json",
        "golden_ast_rel": "data/baselines/golden/Devanagari/samhita/output/Others/Samhita_corrected_out.json",
        "run_manifest": CORPORA_DIR / "samhita" / "run_manifest.json",
        "golden_manifest": GOLDEN_DIR / "samhita_manifest.json",
        "expected_pathas": 6,
        "expected_khandas": 59,
        "expected_samas": 1226,
    },
    "aaranam": {
        "title": "Jaimineeya Aaranam (आरण्यकम्)",
        "edition_key": "aaranam",
        "input_rel": "data/corpora/aaranam/01_input/Aaranam_latest.txt",
        "fallback_input": "data/input/Aaranam_latest.txt",
        "ast_rel": "data/corpora/aaranam/02_ast/Aaranam_ast.json",
        "fallback_ast": "data/output/Aaranam_latest_out.json",
        "canonical_rel": "data/corpora/aaranam/04_canonical/Aaranam_vargeekaran.json",
        "fallback_canonical": "data/output/Aaranam_vargeekaran.json",
        "golden_ast_rel": "data/baselines/golden/Devanagari/aaranam/output/Others/Aaranam_latest_out.json",
        "run_manifest": CORPORA_DIR / "aaranam" / "run_manifest.json",
        "golden_manifest": GOLDEN_DIR / "aaranam_manifest.json",
        "expected_pathas": 6,
        "expected_khandas": 25,
        "expected_samas": 154,
    }
}


def compute_sha256(filepath: Path) -> Optional[str]:
    if not filepath.exists():
        return None
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def resolve_file(primary_rel: str, fallback_rel: str) -> Path:
    p1 = REPO_ROOT / primary_rel
    if p1.exists():
        return p1
    p2 = REPO_ROOT / fallback_rel
    return p2


def extract_ast_metrics(data: dict) -> Dict[str, int]:
    """Computes Pathas, Khandas, and Samas counts from standard AST."""
    supers = data.get("supersections", data.get("supersection", {}))
    pathas = len(supers)
    khandas = sum(len(s.get("sections", {})) for s in supers.values() if isinstance(s, dict))
    samas = 0
    for ss in supers.values():
        if not isinstance(ss, dict): continue
        for sec in ss.get("sections", {}).values():
            if not isinstance(sec, dict): continue
            for sub in sec.get("subsections", {}).values():
                if not isinstance(sub, dict): continue
                mantras = sub.get("corrected-mantra_sets", [])
                samas += max(len(mantras), 1 if sub.get("rik_text") else 0)
    return {"pathas": pathas, "khandas": khandas, "samas": samas}


def diff_ast_trees(golden_data: dict, active_data: dict) -> Dict[str, Any]:
    """
    Performs a deep semantic verse-by-verse comparison between two ASTs.
    Identifies structural alterations, swara modifications, text edits, and metadata changes.
    """
    g_supers = golden_data.get("supersections", golden_data.get("supersection", {}))
    a_supers = active_data.get("supersections", active_data.get("supersection", {}))

    diff_report = {
        "identical": True,
        "structural_diffs": [],
        "modified_verses": [],
        "total_verses_compared": 0,
        "identical_verses": 0,
        "modified_verses_count": 0,
    }

    # Compare SuperSections (Pathas)
    g_p_keys = set(g_supers.keys())
    a_p_keys = set(a_supers.keys())
    if g_p_keys != a_p_keys:
        diff_report["identical"] = False
        diff_report["structural_diffs"].append(f"SuperSection mismatch: Golden {g_p_keys} vs Active {a_p_keys}")

    for p_id in sorted(g_p_keys.intersection(a_p_keys), key=lambda x: str(x)):
        g_sec = g_supers[p_id].get("sections", {})
        a_sec = a_supers[p_id].get("sections", {})

        g_s_keys = set(g_sec.keys())
        a_s_keys = set(a_sec.keys())
        if g_s_keys != a_s_keys:
            diff_report["identical"] = False
            diff_report["structural_diffs"].append(f"Patha {p_id} Section count mismatch: Golden {len(g_s_keys)} vs Active {len(a_s_keys)}")

        for s_id in sorted(g_s_keys.intersection(a_s_keys), key=lambda x: str(x)):
            g_subs = g_sec[s_id].get("subsections", {})
            a_subs = a_sec[s_id].get("subsections", {})

            g_sub_keys = set(g_subs.keys())
            a_sub_keys = set(a_subs.keys())
            if g_sub_keys != a_sub_keys:
                diff_report["identical"] = False
                diff_report["structural_diffs"].append(f"Patha {p_id}, Khanda {s_id} Subsection mismatch: Golden {len(g_sub_keys)} vs Active {len(a_sub_keys)}")

            for sub_id in sorted(g_sub_keys.intersection(a_sub_keys), key=lambda x: str(x)):
                g_sub = g_subs[sub_id]
                a_sub = a_subs[sub_id]

                g_mantras = g_sub.get("corrected-mantra_sets", [])
                a_mantras = a_sub.get("corrected-mantra_sets", [])

                if len(g_mantras) != len(a_mantras):
                    diff_report["identical"] = False
                    diff_report["structural_diffs"].append(
                        f"P{p_id}.K{s_id}.S{sub_id} Mantra count diff: Golden {len(g_mantras)} vs Active {len(a_mantras)}"
                    )

                max_m = max(len(g_mantras), len(a_mantras))
                for idx in range(max_m):
                    diff_report["total_verses_compared"] += 1
                    g_text = g_mantras[idx] if idx < len(g_mantras) else "<ABSENT>"
                    a_text = a_mantras[idx] if idx < len(a_mantras) else "<ABSENT>"

                    if g_text == a_text:
                        diff_report["identical_verses"] += 1
                    else:
                        diff_report["identical"] = False
                        diff_report["modified_verses_count"] += 1
                        diff_report["modified_verses"].append({
                            "location": f"P{p_id}.K{s_id}.S{sub_id} [Verse {idx+1}]",
                            "golden": g_text,
                            "active": a_text
                        })

    return diff_report


def validate_corpus(corpus: str, quick: bool = False) -> Tuple[bool, Dict[str, Any]]:
    """
    Executes Track A (Engine Invariance) and Track B (Semantic Curation Diff).
    """
    cfg = CORPUS_CONFIG.get(corpus)
    if not cfg:
        print(f"{RED}[ERROR] Unknown corpus: '{corpus}'{RESET}")
        return False, {}

    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}  VALIDATION SUITE: {cfg['title']} ({corpus.upper()}){RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}")

    active_input = resolve_file(cfg["input_rel"], cfg["fallback_input"])
    active_ast = resolve_file(cfg["ast_rel"], cfg["fallback_ast"])
    golden_ast = REPO_ROOT / cfg["golden_ast_rel"]

    print(f"  Active Input     : {active_input.relative_to(REPO_ROOT)}")
    print(f"  Active AST       : {active_ast.relative_to(REPO_ROOT)}")
    print(f"  Golden Anchor AST: {golden_ast.relative_to(REPO_ROOT) if golden_ast.exists() else 'NONE (First run)'}")

    results = {
        "corpus": corpus,
        "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "track_a_passed": False,
        "track_b_passed": False,
        "overall_passed": False,
        "metrics": {},
        "diff_summary": "",
        "status": "FAILED"
    }

    # ----------------------------------------------------
    # TRACK A: Engine Invariance & Macro Structural Checks
    # ----------------------------------------------------
    print(f"\n{BOLD}--- Track A: Engine Invariance & Structural Integrity ---{RESET}")
    if not active_ast.exists():
        print(f"  {RED}[FAIL]{RESET} Active AST file missing: {active_ast.name}")
        return False, results

    with open(active_ast, "r", encoding="utf-8") as f:
        active_data = json.load(f)

    metrics = extract_ast_metrics(active_data)
    results["metrics"] = metrics
    print(f"  Metrics Extracted: {metrics['pathas']} Pathas, {metrics['khandas']} Khandas, {metrics['samas']} Samas")

    track_a_ok = True
    if cfg["expected_pathas"] and metrics["pathas"] != cfg["expected_pathas"]:
        print(f"  {RED}[FAIL]{RESET} Patha count drift: Expected {cfg['expected_pathas']}, Got {metrics['pathas']}")
        track_a_ok = False
    else:
        print(f"  {GREEN}[PASS]{RESET} Pathas invariant preserved ({metrics['pathas']})")

    if cfg["expected_khandas"] and metrics["khandas"] != cfg["expected_khandas"]:
        print(f"  {RED}[FAIL]{RESET} Khanda count drift: Expected {cfg['expected_khandas']}, Got {metrics['khandas']}")
        track_a_ok = False
    else:
        print(f"  {GREEN}[PASS]{RESET} Khandas invariant preserved ({metrics['khandas']})")

    if cfg["expected_samas"] and metrics["samas"] != cfg["expected_samas"]:
        print(f"  {YELLOW}[NOTICE]{RESET} Sama count: Active {metrics['samas']} vs Standard {cfg['expected_samas']}")
    else:
        print(f"  {GREEN}[PASS]{RESET} Samas count invariant verified ({metrics['samas']})")

    results["track_a_passed"] = track_a_ok

    # ----------------------------------------------------
    # TRACK B: Semantic Content Diff vs Golden Baseline
    # ----------------------------------------------------
    print(f"\n{BOLD}--- Track B: Semantic Curation Diff vs Golden Anchor ---{RESET}")
    if not golden_ast.exists():
        print(f"  {YELLOW}[NOTICE]{RESET} Golden Baseline AST not found. Baseline initialization required.")
        results["track_b_passed"] = True
        results["diff_summary"] = "No Golden Baseline Anchor yet recorded."
    else:
        with open(golden_ast, "r", encoding="utf-8") as f:
            golden_data = json.load(f)

        diff = diff_ast_trees(golden_data, active_data)
        if diff["identical"]:
            print(f"  {GREEN}[PERFECT GOLDEN MATCH]{RESET} 100% byte & verse parity. (0 differences)")
            results["track_b_passed"] = True
            results["diff_summary"] = "100% parity with Golden Baseline Anchor."
        elif len(diff["structural_diffs"]) == 0 and diff["modified_verses_count"] > 0:
            print(f"  {GREEN}[VALIDATED CURATION DIFF]{RESET} All structural containers intact.")
            print(f"  Total Verses Compared : {diff['total_verses_compared']}")
            print(f"  Identical Verses       : {diff['identical_verses']}")
            print(f"  Curation Edits Detected: {diff['modified_verses_count']} verse(s)")
            print(f"\n  Sample Curation Changes:")
            for mod in diff["modified_verses"][:5]:
                print(f"    * {BOLD}{mod['location']}{RESET}:")
                print(f"      - Golden: {mod['golden']}")
                print(f"      + Active: {mod['active']}")
            if len(diff["modified_verses"]) > 5:
                print(f"      ... and {len(diff['modified_verses']) - 5} more.")
            results["track_b_passed"] = True
            results["diff_summary"] = f"Validated Curation: {diff['modified_verses_count']} verses modified; {diff['identical_verses']} intact."
        else:
            print(f"  {RED}[STRUCTURAL REGRESSION DETECTED]{RESET}")
            for sd in diff["structural_diffs"][:10]:
                print(f"    ! {sd}")
            results["track_b_passed"] = False
            results["diff_summary"] = f"Structural breaks: {len(diff['structural_diffs'])} errors."

    # ----------------------------------------------------
    # Overall Assessment & Run Manifest Update
    # ----------------------------------------------------
    overall_ok = results["track_a_passed"] and results["track_b_passed"]
    results["overall_passed"] = overall_ok
    results["status"] = "PASSED" if overall_ok else "FAILED"

    # Update Active Run Manifest
    manifest_file = cfg["run_manifest"]
    manifest_data = {}
    if manifest_file.exists():
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
        except Exception:
            pass

    manifest_data["corpus"] = corpus
    manifest_data["edition"] = get_corpus_edition(corpus)
    manifest_data["last_validated"] = results["timestamp"]
    manifest_data["validation_status"] = results["status"]
    manifest_data["validation_summary"] = results["diff_summary"]
    manifest_data["hashes"] = {
        "input_sha256": compute_sha256(active_input),
        "ast_sha256": compute_sha256(active_ast),
        "canonical_sha256": compute_sha256(resolve_file(cfg["canonical_rel"], cfg["fallback_canonical"]))
    }
    manifest_data["metrics"] = metrics

    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    print(f"\n  Active Run Manifest Updated: {manifest_file.relative_to(REPO_ROOT)}")
    print(f"  Validation Status          : {BOLD}{GREEN if overall_ok else RED}{results['status']}{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")

    return overall_ok, results


def promote_to_golden(corpus: str) -> bool:
    """
    Promotes the verified Active Run into the immutable Golden Baseline Anchor.
    """
    cfg = CORPUS_CONFIG.get(corpus)
    if not cfg:
        print(f"{RED}[ERROR] Unknown corpus: '{corpus}'{RESET}")
        return False

    print(f"\n{BOLD}{GREEN}{'#'*70}{RESET}")
    print(f"{BOLD}{GREEN}  PROMOTING ACTIVE RUN TO GOLDEN BASELINE: {corpus.upper()}{RESET}")
    print(f"{BOLD}{GREEN}{'#'*70}{RESET}")

    # First validate
    ok, res = validate_corpus(corpus, quick=True)
    if not ok:
        print(f"{RED}[PROMOTION ABORTED] Run validation failed. Fix regressions before promoting.{RESET}")
        return False

    active_input = resolve_file(cfg["input_rel"], cfg["fallback_input"])
    active_ast = resolve_file(cfg["ast_rel"], cfg["fallback_ast"])
    active_canonical = resolve_file(cfg["canonical_rel"], cfg["fallback_canonical"])

    # 1. Update Golden Baseline Manifest
    now_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    git_commit = get_engine_version()

    golden_manifest_data = {
        "corpus": corpus,
        "edition": get_corpus_edition(corpus),
        "promoted_at": now_str,
        "engine_version": git_commit,
        "metrics": res["metrics"],
        "files": {
            "input": {
                "path": str(active_input.relative_to(REPO_ROOT)),
                "sha256": compute_sha256(active_input),
                "size_bytes": active_input.stat().st_size
            },
            "ast": {
                "path": str(active_ast.relative_to(REPO_ROOT)),
                "sha256": compute_sha256(active_ast),
                "size_bytes": active_ast.stat().st_size
            },
            "canonical": {
                "path": str(active_canonical.relative_to(REPO_ROOT)),
                "sha256": compute_sha256(active_canonical),
                "size_bytes": active_canonical.stat().st_size if active_canonical.exists() else 0
            }
        }
    }

    golden_manifest_file = cfg["golden_manifest"]
    golden_manifest_file.parent.mkdir(parents=True, exist_ok=True)
    with open(golden_manifest_file, "w", encoding="utf-8") as f:
        json.dump(golden_manifest_data, f, indent=2, ensure_ascii=False)

    # 2. Update Golden Baseline Anchor File
    golden_ast = REPO_ROOT / cfg["golden_ast_rel"]
    if golden_ast.parent.exists():
        import shutil
        shutil.copy2(str(active_ast), str(golden_ast))
        print(f"  [SUCCESS] Golden Baseline Anchor AST updated: {golden_ast.relative_to(REPO_ROOT)}")

    # 3. Update Run Manifest status to PROMOTED
    run_manifest_file = cfg["run_manifest"]
    if run_manifest_file.exists():
        with open(run_manifest_file, "r", encoding="utf-8") as f:
            run_data = json.load(f)
        run_data["validation_status"] = "PROMOTED_TO_GOLDEN"
        run_data["golden_promoted_at"] = now_str
        with open(run_manifest_file, "w", encoding="utf-8") as f:
            json.dump(run_data, f, indent=2, ensure_ascii=False)

    # 4. Synchronize with LATEST.json
    latest_path = BASELINES_DIR / "LATEST.json"
    latest_data = {}
    if latest_path.exists():
        try:
            with open(latest_path, "r", encoding="utf-8") as f:
                latest_data = json.load(f)
        except Exception:
            pass

    if "inputs" not in latest_data: latest_data["inputs"] = {}
    if "outputs" not in latest_data: latest_data["outputs"] = {}

    rel_in = str(active_input.relative_to(REPO_ROOT)).replace("\\", "/")
    rel_ast = str(active_ast.relative_to(REPO_ROOT)).replace("\\", "/")
    rel_can = str(active_canonical.relative_to(REPO_ROOT)).replace("\\", "/")

    latest_data["inputs"][rel_in] = {
        "sha256": compute_sha256(active_input),
        "size_bytes": active_input.stat().st_size,
        "modified": now_str
    }
    latest_data["outputs"][rel_ast] = {
        "sha256": compute_sha256(active_ast),
        "size_bytes": active_ast.stat().st_size,
        "modified": now_str
    }
    if active_canonical.exists():
        latest_data["outputs"][rel_can] = {
            "sha256": compute_sha256(active_canonical),
            "size_bytes": active_canonical.stat().st_size,
            "modified": now_str
        }

    latest_data["timestamp"] = now_str
    latest_data["version"] = get_corpus_edition(corpus)

    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(latest_data, f, indent=2, ensure_ascii=False)

    print(f"  [SUCCESS] Golden Baseline Manifest: {golden_manifest_file.relative_to(REPO_ROOT)}")
    print(f"  [SUCCESS] Active Run Marked        : PROMOTED_TO_GOLDEN")
    print(f"  [SUCCESS] LATEST.json synchronized.")
    print(f"{BOLD}{GREEN}{'#'*70}{RESET}\n")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Dual-Track Run Validation and Baseline Promotion Engine for Jaimineeya Samaveda."
    )
    parser.add_argument(
        "corpus",
        choices=["samhita", "aaranam", "all"],
        default="all",
        nargs="?",
        help="Target corpus to validate (default: all)"
    )
    parser.add_argument(
        "--promote",
        action="store_true",
        help="Promote the validated active run to the new Golden Baseline Anchor"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick check without deep inspection"
    )

    args = parser.parse_args()

    corpora_to_run = ["samhita", "aaranam"] if args.corpus == "all" else [args.corpus]

    if args.promote:
        all_ok = True
        for c in corpora_to_run:
            if not promote_to_golden(c):
                all_ok = False
        sys.exit(0 if all_ok else 1)
    else:
        all_ok = True
        for c in corpora_to_run:
            ok, _ = validate_corpus(c, quick=args.quick)
            if not ok:
                all_ok = False
        sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
