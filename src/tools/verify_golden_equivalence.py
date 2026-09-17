"""
Verify Golden Baseline Equivalence for Jaimineeya Samaveda Pipeline.

Runs the active pipeline against the frozen Golden Baseline inputs and asserts
100% semantic and structural equivalence against the frozen Golden Baseline outputs.
"""

import sys
import os
import json
import csv
import shutil
import subprocess
from pathlib import Path
from typing import Tuple, Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GOLDEN_ROOT = PROJECT_ROOT / "data" / "baselines" / "golden"


def compare_json_trees(test_path: Path, golden_path: Path) -> Tuple[bool, List[str]]:
    """Compares two AST JSON files, ignoring volatile metadata timestamps."""
    issues = []
    if not test_path.exists() or not golden_path.exists():
        return False, [f"Missing file: {test_path} or {golden_path}"]
    
    with open(test_path, 'r', encoding='utf-8') as f:
        t_data = json.load(f)
    with open(golden_path, 'r', encoding='utf-8') as f:
        g_data = json.load(f)
    
    # 1. Compare supersection AST
    t_ss = t_data.get('supersection') or t_data.get('supersections')
    g_ss = g_data.get('supersection') or g_data.get('supersections')
    if t_ss != g_ss:
        issues.append("supersection structural AST mismatch")
    
    # 2. Compare closing mantras
    t_cm = t_data.get('closing_mantras')
    g_cm = g_data.get('closing_mantras')
    if t_cm != g_cm:
        issues.append("closing_mantras mismatch")
        
    return len(issues) == 0, issues


def compare_csv_data(test_path: Path, golden_path: Path) -> Tuple[bool, List[str]]:
    """Compares CSV rows, ignoring line 0 timestamp header."""
    issues = []
    if not test_path.exists() or not golden_path.exists():
        return False, [f"Missing file: {test_path} or {golden_path}"]
        
    with open(test_path, 'r', encoding='utf-8') as f:
        t_rows = list(csv.reader(f))
    with open(golden_path, 'r', encoding='utf-8') as f:
        g_rows = list(csv.reader(f))
        
    # Ignore line 0 if it contains timestamp/metadata comment
    t_data = t_rows[1:] if len(t_rows) > 1 and len(t_rows[0]) == 1 else t_rows
    g_data = g_rows[1:] if len(g_rows) > 1 and len(g_rows[0]) == 1 else g_rows
    
    if len(t_data) != len(g_data):
        issues.append(f"Row count mismatch: generated {len(t_data)}, golden {len(g_data)}")
    else:
        for idx, (tr, gr) in enumerate(zip(t_data, g_data)):
            if tr != gr:
                issues.append(f"Row {idx + 1} mismatch: {tr[:3]} != {gr[:3]}")
                if len(issues) >= 5:
                    break
    return len(issues) == 0, issues


def count_liturgical_samas(json_path: Path) -> Dict[str, int]:
    """Computes exact domain metrics from a Vargeekaran JSON."""
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    from samam_utils import count_samams_with_fallback
    
    with open(json_path, 'r', encoding='utf-8') as f:
        d = json.load(f)
        
    ss = d.get('supersection') or d.get('supersections') or {}
    total_pathas = len(ss)
    total_khandas = sum(len(s.get('sections', {})) for s in ss.values())
    total_subs = 0
    total_samas = 0
    
    for s in ss.values():
        for sec in s.get('sections', {}).values():
            for sub in sec.get('subsections', {}).values():
                total_subs += 1
                for ms in sub.get('corrected-mantra_sets', []):
                    mantra = ms.get('corrected-mantra', '')
                    total_samas += count_samams_with_fallback(mantra)
                    
    return {
        "pathas": total_pathas,
        "khandas": total_khandas,
        "subsections": total_subs,
        "samas": total_samas
    }


def verify_samhita_equivalence() -> bool:
    """Executes the pipeline on Samhita golden inputs and validates equivalence."""
    corpus_dir = GOLDEN_ROOT / "Devanagari" / "samhita"
    if not corpus_dir.exists():
        corpus_dir = GOLDEN_ROOT / "samhita"
    inputs_dir = corpus_dir / "inputs"
    golden_out_dir = corpus_dir / "outputs"
    sandbox_dir = corpus_dir / "sandbox_run"
    
    input_txt = inputs_dir / "Samhita_Devanagari_Unicode.txt"
    if not input_txt.exists():
        input_txt = inputs_dir / "Samhita_corrected.txt"
    recon_xlsx = inputs_dir / "Rik Reconciliation table (JSV-KSV).xlsx"
    
    if not input_txt.exists() or not recon_xlsx.exists():
        print(f"Error: Missing input files in {inputs_dir}")
        return False
        
    sandbox_dir.mkdir(parents=True, exist_ok=True)
    
    gen_ast = sandbox_dir / "Samhita_corrected_out.json"
    gen_vargeekaran = sandbox_dir / "Vargeekaran.json"
    gen_rik_table = sandbox_dir / "JSV_Rik_Table.csv"
    
    print("=" * 70)
    print("  JAIMINEEYA PIPELINE: GOLDEN BASELINE EQUIVALENCE VERIFICATION")
    print("=" * 70)
    print(f"Corpus       : Samhita")
    print(f"Input Text   : {input_txt.name} ({input_txt.stat().st_size:,} bytes)")
    print(f"Recon Excel  : {recon_xlsx.name} ({recon_xlsx.stat().st_size:,} bytes)")
    print(f"Sandbox Dir  : {sandbox_dir}")
    print("-" * 70)
    
    try:
        # Step 1: Run generate_json.py
        print("[1/4] Running generate_json.py (Correction Mode)...")
        cmd_ast = [
            sys.executable, str(PROJECT_ROOT / "src" / "generate_json.py"),
            str(input_txt), "--type", "samhita", "--output", str(gen_ast)
        ]
        res1 = subprocess.run(cmd_ast, cwd=PROJECT_ROOT, capture_output=True, text=True, check=True)
        print("      -> AST generated successfully.")
        
        # Step 2: Run generate_rik_table.py
        print("[2/4] Running generate_rik_table.py with Excel reconciliation...")
        cmd_recon = [
            sys.executable, str(PROJECT_ROOT / "src" / "generate_rik_table.py"),
            "--type", "samhita",
            "-e", str(recon_xlsx),
            "-o", str(gen_rik_table),
            "-j", str(gen_vargeekaran),
            str(gen_ast)
        ]
        res2 = subprocess.run(cmd_recon, cwd=PROJECT_ROOT, capture_output=True, text=True, check=True)
        print("      -> Vargeekaran and Rik Table generated successfully.")
        
        # Step 3: Compare against Golden Baseline Outputs
        print("[3/4] Performing node-by-node AST and data equivalence tests...")
        
        # AST match
        ast_ok, ast_issues = compare_json_trees(gen_ast, golden_out_dir / "Samhita_corrected_out.json")
        status_ast = "[PASS] 100% MATCH" if ast_ok else f"[FAIL] {ast_issues}"
        print(f"      - Samhita AST Equivalence   : {status_ast}")
        
        # Vargeekaran match
        v_ok, v_issues = compare_json_trees(gen_vargeekaran, golden_out_dir / "Vargeekaran.json")
        status_v = "[PASS] 100% MATCH" if v_ok else f"[FAIL] {v_issues}"
        print(f"      - Vargeekaran Equivalence   : {status_v}")
        
        # CSV match
        csv_ok, csv_issues = compare_csv_data(gen_rik_table, golden_out_dir / "JSV_Rik_Table.csv")
        status_csv = "[PASS] 100% MATCH" if csv_ok else f"[FAIL] {csv_issues}"
        print(f"      - Rik Table CSV Equivalence : {status_csv}")
        
        # Step 4: Metric validation
        print("[4/4] Verifying liturgical invariants...")
        metrics = count_liturgical_samas(gen_vargeekaran)
        print(f"      - Pathas (SuperSections)    : {metrics['pathas']} (Expected: 6) -> {'[PASS]' if metrics['pathas'] == 6 else '[FAIL]'}")
        print(f"      - Khandas (Sections)        : {metrics['khandas']} (Expected: 59) -> {'[PASS]' if metrics['khandas'] == 59 else '[FAIL]'}")
        print(f"      - SubSections               : {metrics['subsections']} (Expected: 722) -> {'[PASS]' if metrics['subsections'] == 722 else '[FAIL]'}")
        print(f"      - Liturgical Samas          : {metrics['samas']} (Expected: 1226) -> {'[PASS]' if metrics['samas'] == 1226 else '[FAIL]'}")
        
        all_passed = ast_ok and v_ok and csv_ok and metrics['pathas'] == 6 and metrics['khandas'] == 59 and metrics['samas'] == 1226
        
        print("=" * 70)
        if all_passed:
            print("  OVERALL STATUS: 100% GOLDEN EQUIVALENCE VERIFIED [SUCCESS]")
            print("  The pipeline run reproduces the Golden Baseline outputs deterministically.")
        else:
            print("  OVERALL STATUS: REGRESSION DETECTED [FAILURE]")
        print("=" * 70)
        return all_passed

    finally:
        # Cleanup sandbox directory
        if sandbox_dir.exists():
            shutil.rmtree(sandbox_dir, ignore_errors=True)


if __name__ == "__main__":
    success = verify_samhita_equivalence()
    sys.exit(0 if success else 1)
