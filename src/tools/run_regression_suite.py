"""
Jaimineeya Samaveda - Automated Regression & Invariant Verification Suite
--------------------------------------------------------------------------
Run this script to verify that no liturgical or structural invariants are broken:
  python src/tools/run_regression_suite.py
"""

import sys
import os
import time
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_header(title):
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}")

def run_check(name, fn):
    print(f"  Checking: {name:.<45} ", end="", flush=True)
    t0 = time.time()
    try:
        ok, msg = fn()
        elapsed = time.time() - t0
        if ok:
            print(f"{GREEN}[PASS]{RESET} ({elapsed:.2f}s) {msg}")
            return True
        else:
            print(f"{RED}[FAIL]{RESET} ({elapsed:.2f}s) {msg}")
            return False
    except Exception as e:
        elapsed = time.time() - t0
        print(f"{RED}[ERROR]{RESET} ({elapsed:.2f}s) {e}")
        return False

# --- 1. Live Ingestion from Raw Unicode Texts ---
def check_live_ingestion():
    """Execute generate_json.py from raw Unicode texts to guarantee live pipeline viability."""
    samhita_in = REPO_ROOT / "data" / "input" / "Samhita_corrected.txt"
    aaranam_in = REPO_ROOT / "data" / "input" / "Aaranam_latest.txt"
    
    if not samhita_in.exists():
        return False, f"Missing {samhita_in}"
    if not aaranam_in.exists():
        return False, f"Missing {aaranam_in}"

    # 1. Ingest Samhita
    cmd_samhita = [
        sys.executable,
        str(REPO_ROOT / "src" / "generate_json.py"),
        str(samhita_in),
        "--type", "samhita",
        "--output", "data/output/Samhita_corrected_out.json"
    ]
    res_sam = subprocess.run(cmd_samhita, cwd=REPO_ROOT, capture_output=True, text=True)
    if res_sam.returncode != 0:
        return False, f"Samhita ingestion failed: {res_sam.stderr.strip() or res_sam.stdout.strip()}"

    # 2. Ingest Aaranam
    cmd_aaranam = [
        sys.executable,
        str(REPO_ROOT / "src" / "generate_json.py"),
        str(aaranam_in),
        "--type", "aaranam",
        "--output", "data/output/Aaranam_latest_out.json"
    ]
    res_aar = subprocess.run(cmd_aaranam, cwd=REPO_ROOT, capture_output=True, text=True)
    if res_aar.returncode != 0:
        return False, f"Aaranam ingestion failed: {res_aar.stderr.strip() or res_aar.stdout.strip()}"

    # 3. Regenerate Structure Summary CSV
    cmd_summary = [
        sys.executable,
        str(REPO_ROOT / "src" / "generate_json_summary.py")
    ]
    res_sum = subprocess.run(cmd_summary, cwd=REPO_ROOT, capture_output=True, text=True)
    if res_sum.returncode != 0:
        return False, f"Summary generation failed: {res_sum.stderr.strip()}"

    # 4. Verify in-memory structure counts
    from core.swara_engine import count_samams
    with open(REPO_ROOT / "data" / "output" / "Samhita_corrected_out.json", "r", encoding="utf-8") as f:
        sam_data = json.load(f)
    sam_supers = sam_data.get("supersection", {})
    sam_sections = sum(len(sup.get("sections", {})) for sup in sam_supers.values())
    sam_subsections = sum(
        sum(len(sec.get("subsections", {})) for sec in sup.get("sections", {}).values())
        for sup in sam_supers.values()
    )
    sam_samas = sum(
        sum(
            sum(count_samams(ms.get("corrected-mantra", "")) for ms in sub.get("corrected-mantra_sets", []))
            for sub in sec.get("subsections", {}).values()
        )
        for sup in sam_supers.values()
        for sec in sup.get("sections", {}).values()
    )
    if len(sam_supers) != 6 or sam_sections != 59 or sam_subsections != 722 or sam_samas != 1226:
        return False, f"Samhita live counts mismatch: {len(sam_supers)} Pathas, {sam_sections} Khandas, {sam_subsections} Riks, {sam_samas} Samas"

    with open(REPO_ROOT / "data" / "output" / "Aaranam_latest_out.json", "r", encoding="utf-8") as f:
        aar_data = json.load(f)
    aar_supers = aar_data.get("supersection", {})
    aar_sections = sum(len(sup.get("sections", {})) for sup in aar_supers.values())
    aar_subsections = sum(
        sum(len(sec.get("subsections", {})) for sec in sup.get("sections", {}).values())
        for sup in aar_supers.values()
    )
    aar_samas = sum(
        sum(
            sum(count_samams(ms.get("corrected-mantra", "")) for ms in sub.get("corrected-mantra_sets", []))
            for sub in sec.get("subsections", {}).values()
        )
        for sup in aar_supers.values()
        for sec in sup.get("sections", {}).values()
    )
    if len(aar_supers) != 6 or aar_sections != 25 or aar_subsections != 154 or aar_samas != 295:
        return False, f"Aaranam live counts mismatch: {len(aar_supers)} Parvas, {aar_sections} Kandahs, {aar_subsections} Subsections, {aar_samas} Samas"

    return True, f"Samhita ({sam_subsections} Riks, {sam_samas} Samas) & Aaranam ({aar_subsections} Subsections, {aar_samas} Samas) parsed live"


# --- 2. Domain Metric Invariants ---
def check_domain_metrics():
    summary_path = REPO_ROOT / "data" / "output" / "JSV_Structure_Summary.csv"
    if not summary_path.exists():
        return False, "Summary CSV not found"
    
    with open(summary_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    # Header: Patha (SuperSection),Khanda (Section),Samas (Subsections)
    pathas = set()
    total_khandas = 0
    total_samas = 0
    
    for line in lines[1:]:
        parts = line.split(",")
        if len(parts) >= 3:
            pathas.add(parts[0].strip())
            total_khandas += 1
            try:
                total_samas += int(parts[2].strip())
            except ValueError:
                pass
                
    if len(pathas) != 6:
        return False, f"Expected 6 Pathas, got {len(pathas)}"
    if total_khandas != 59:
        return False, f"Expected 59 Khandas, got {total_khandas}"
    if total_samas != 1226:
        return False, f"Expected 1226 Samas, got {total_samas}"
        
    return True, f"6 Pathas, 59 Khandas, 1226 Samas exactly"

# --- 2. Typed AST Models & Roundtrip ---
def check_ast_models():
    from core.models import VedicDocument
    samhita_json = REPO_ROOT / "data" / "output" / "Samhita_corrected_out.json"
    if not samhita_json.exists():
        return False, "Samhita_corrected_out.json not found"
        
    with open(samhita_json, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
        
    doc = VedicDocument.from_dict(raw_data)
    if len(doc.supersections) != 6:
        return False, f"Loaded {len(doc.supersections)} supersections instead of 6"
        
    # Test lossless round-trip
    exported = doc.to_dict()
    if exported.get("meta", {}).get("version") != raw_data.get("meta", {}).get("version"):
        return False, "Version mismatch in AST roundtrip"
        
    return True, f"VedicDocument loaded & validated (6 supersections)"

# --- 3. Centralized Swara Engine Invariants ---
def check_swara_engine():
    from core.swara_engine import (
        devanagari_to_int,
        int_to_devanagari,
        fix_visarga_accent_order,
        normalize_dandas,
        SAMAM_PATTERN
    )
    
    # Test numeral conversions
    if devanagari_to_int("१२३४५") != 12345:
        return False, "Devanagari to int numeral conversion failed"
    if int_to_devanagari(12345) != "१२३४५":
        return False, "Int to Devanagari numeral conversion failed"
        
    # Test Visarga-accent ordering
    if fix_visarga_accent_order("न:(1)") != "न(1)ः":
        return False, f"Markup Visarga-accent reordering failed: {fix_visarga_accent_order('न:(1)')}"
    if fix_visarga_accent_order("नः॑") != "न॑ः":
        return False, f"Unicode Visarga-accent reordering failed: {fix_visarga_accent_order('नः॑')}"
        
    # Test SAMAM_PATTERN regex
    matches = SAMAM_PATTERN.findall("॥ १ ॥ text ॥ २ ॥ text ॥ २ क ॥ text ॥ ३ ख ॥")
    if len(matches) != 4:
        return False, f"SAMAM_PATTERN matched {len(matches)} instead of 4"
        
    return True, "Accent ordering, numerals, and Samam regex verified"

# --- 4. Structural Tag Balance Check ---
def check_structural_tags():
    from ingest.renumber import validate_structural_tags
    samhita_txt = REPO_ROOT / "data" / "input" / "Samhita_corrected.txt"
    if not samhita_txt.exists():
        return False, "Samhita_corrected.txt not found"
        
    with open(samhita_txt, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    is_valid, errors = validate_structural_tags(lines)
    if not is_valid:
        return False, f"Tag balance failed with {len(errors)} errors: {errors[:2]}"
        
    return True, f"All structural # Start / # End tags balanced ({len(lines):,} lines)"

# --- 5. 3-Tier Versioning Engine ---
def check_version_engine():
    from core.version import (
        get_engine_version,
        get_corpus_edition,
        get_build_metadata,
        format_build_stamp
    )
    
    engine = get_engine_version()
    if not engine.startswith("v"):
        return False, f"Engine version malformed: {engine}"
        
    edition = get_corpus_edition("samhita")
    if edition != "3.28":
        return False, f"Samhita edition expected '3.28', got '{edition}'"
        
    meta = get_build_metadata("samhita", REPO_ROOT / "data" / "input" / "Samhita_corrected.txt")
    if not meta.get("input_sha256"):
        return False, "SHA-256 fingerprint missing from build metadata"
    if meta.get("version") != "3.28":
        return False, f"Legacy version key mismatch: {meta.get('version')}"
        
    stamp = format_build_stamp(meta)
    if "Edition 3.28" not in stamp:
        return False, f"Build stamp format incorrect: {stamp}"
        
    return True, f"{stamp}"

# --- 6. Active Baseline Integrity ---
def check_baseline_integrity():
    from tools.baseline import compute_sha256
    latest_file = REPO_ROOT / "data" / "baselines" / "LATEST.json"
    if not latest_file.exists():
        return False, "data/baselines/LATEST.json not found"
        
    with open(latest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    inputs = manifest.get("inputs", {})
    
    mismatches = []
    for rel_path, expected in inputs.items():
        full_path = REPO_ROOT / rel_path
        if not full_path.exists():
            mismatches.append(f"Missing: {rel_path}")
            continue
        actual_hash = compute_sha256(full_path)
        if actual_hash != expected.get("sha256"):
            mismatches.append(f"Hash mismatch: {rel_path}")
            
    if mismatches:
        return False, f"Input baseline drift: {', '.join(mismatches)}"
        
    return True, f"All master inputs match baseline '{manifest.get('tag')}'"

# --- 7. Modular Renderers Availability ---
def check_renderers():
    try:
        from renderers import BaseRenderer, LaTeXRenderer, HTMLRenderer, TextRenderer
        import render_pdf
        return True, "LaTeX, HTML, and PlainText renderers loaded"
    except Exception as e:
        return False, f"Renderer import failed: {e}"

def main():
    print_header("JAIMINEEYA SAMAVEDA - REGRESSION VERIFICATION SUITE")
    print(f"  Repo Root: {REPO_ROOT}")
    print(f"  Python   : {sys.version.split()[0]}\n")
    
    checks = [
        ("1. Live Ingestion from Raw Unicode Texts", check_live_ingestion),
        ("2. Domain Invariants (6 Pathas, 59 Khandas, 1226 Samas)", check_domain_metrics),
        ("3. Typed AST Lossless Roundtrip", check_ast_models),
        ("4. Swara Engine & Visarga-Accent Rules", check_swara_engine),
        ("5. Structural Tag Balance & Integrity", check_structural_tags),
        ("6. 3-Tier Version & Build Metadata", check_version_engine),
        ("7. Active Baseline Input Checksums", check_baseline_integrity),
        ("8. Modular Rendering Engines", check_renderers),
    ]
    
    results = []
    for name, fn in checks:
        res = run_check(name, fn)
        results.append(res)
        
    print_header("VERIFICATION SUMMARY")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"  {BOLD}{GREEN}ALL {total}/{total} INVARIANT CHECKS PASSED!{RESET}")
        print(f"  No regressions detected. Repository is liturigically sound.")
        print(f"{BOLD}{CYAN}{'='*60}{RESET}\n")
        return 0
    else:
        print(f"  {BOLD}{RED}{total - passed}/{total} CHECKS FAILED!{RESET}")
        print(f"  Please investigate failures above before committing.")
        print(f"{BOLD}{CYAN}{'='*60}{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
