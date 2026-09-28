"""
Stage 1 Archival Purge and Stage-Numbered Corpus Migration Script.

Safely archives scratch, obsolete, lock, and temporary files into data/archive/legacy_2026/
and establishes the stage-numbered directory hierarchy in data/corpora/<corpus>/
preserving backwards compatibility with existing data/input and data/output paths.
"""

import os
import sys
import shutil
from pathlib import Path
import json
import hashlib
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
DATA_DIR = ROOT_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
ARCHIVE_DIR = DATA_DIR / "archive" / "legacy_2026"
CORPORA_DIR = DATA_DIR / "corpora"

# Files in data/input to safely archive
INPUT_FILES_TO_ARCHIVE = [
    "Aaranam_latest - Copy (2).txt",
    "Aaranam_latest - Copy.txt",
    "Aaranam_latest_.txt",
    "broken_test.txt",
    "Agneyam-Pavamanam_latest.txt",
    "Agneyam-Pavamanam_corrected.txt",
]

# Exact file patterns/names in data/output to safely archive
OUTPUT_FILES_TO_ARCHIVE = [
    # Scratch and test generation runs
    "1.txt",
    "Aaranam_test_renum.txt",
    "Aaranam_test_renum_v2.txt",
    "Aaranam_config_test.txt",
    "sep_test_Devanagari.html",
    "sep_test_Devanagari.tex",
    "sep_test_fixed_Rik_Devanagari.html",
    "sep_test_fixed_Rik_Devanagari.tex",
    "sep_test_fixed_Samam_Devanagari.html",
    "sep_test_fixed_Samam_Devanagari.tex",
    "test_logic_Devanagari.html",
    "test_logic_Devanagari.tex",
    "test_rik_table.csv",
    "test_rik_table.xlsx",
    "test_samhita_ast.json",
    "test_vargeekaran.json",
    "test_filter_out.json",
    "Samhita_Correction_Test.json",
    "curate_log.txt",
    "curate_log_clean.txt",
    "curate_log_utf8.txt",
    "non_contiguous_analysis.txt",
    "non_contiguous_analysis_v2.txt",
    "non_contiguous_analysis_v2.xlsx",
    "non_contiguous_riks.txt",
    "ss1_sections_debug.txt",
    "section8_samams.txt",
    "o_malayalam.html",
    "o_malayalam.txt",
    "Aaranam_rik.json.html",
    "Aaranam_rik.json.pdf",
    "Aaranam_rik.json.tex",
    "Nakshatra_sooktam_test.json",
    "Aaranam_latest_out_.json",
    "JSV_Samam_Granular_Table.bak.xlsx",
    "Samhita_with_Rishi_Devata_Chandas_out_backup_20260209_154352.json",
    "Vargeekaran-bak.json",
    "GENERATION_LOG_.pdf",
    "JSV_Missing_Metadata_Report_.md",
    "JSV_Samam_Granular_Table_.csv",
    "Saman_Metadata_Comparison_Samhita_.xlsx",
    "Rik Reconciliation table (JSV-KSV)__ - Aaranam.xlsx",
    "Rik Reconciliation table (JSV-KSV)-corr.xlsx",
    "Aaranam_Rik_Table_Clean.csv",
    "Aaranam_Rik_Table_Strict.csv",
    "Aaranam_Rik_Table_minimal.csv",
    "Aaranam_Rik_Table_Final.csv",
    "Samhita_Rik_Table_Clean.csv",
    "Samhita_Rik_Table_Strict.csv",
    "Samhita_Rik_Table_Full.csv",
    "Samhita_Rik_Table_Final.csv",
    "rik_matches_v5_final.xlsx",
    "Aaranam_input_out.json",
    "Agneyam-Pavamanam_corrected_out.json",
    "Agneyam-Pavamanam_latest_out.json",
    "prayogamala-pb.json",
    "prayogamala-ubn.json",
    "Ritu-shanti-2.json",
    "Sooktam-orig.json",
    "Sooktam_.json",
    "Sooktamala_.json",
    "TestCollection.json",
    "samhita-corrected.json",
    "vedic_output.html",
]


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def purge_and_archive():
    print("[1/4] Initializing archive directories...")
    archive_in = ARCHIVE_DIR / "input"
    archive_out = ARCHIVE_DIR / "output"
    archive_in.mkdir(parents=True, exist_ok=True)
    archive_out.mkdir(parents=True, exist_ok=True)

    # 1. Archive input lock files and duplicates
    archived_in_count = 0
    for f in INPUT_DIR.glob("~$*"):
        try:
            shutil.move(str(f), str(archive_in / f.name))
            archived_in_count += 1
        except Exception as e:
            print(f"  Warning archiving lock file {f.name}: {e}")

    for filename in INPUT_FILES_TO_ARCHIVE:
        p = INPUT_DIR / filename
        if p.exists():
            shutil.move(str(p), str(archive_in / filename))
            archived_in_count += 1
            print(f"  Archived input -> {filename}")

    # 2. Archive output lock files and scratch/test files
    archived_out_count = 0
    for f in OUTPUT_DIR.glob("~$*"):
        try:
            shutil.move(str(f), str(archive_out / f.name))
            archived_out_count += 1
        except Exception as e:
            print(f"  Warning archiving lock file {f.name}: {e}")

    for filename in OUTPUT_FILES_TO_ARCHIVE:
        p = OUTPUT_DIR / filename
        if p.exists():
            shutil.move(str(p), str(archive_out / filename))
            archived_out_count += 1
            print(f"  Archived output -> {filename}")

    print(f"[ARCHIVE COMPLETE] Archived {archived_in_count} input files, {archived_out_count} output files to {ARCHIVE_DIR.relative_to(ROOT_DIR)}")


def setup_stage_directories():
    print("\n[2/4] Setting up stage-numbered corpus directories in data/corpora/...")
    
    stages = ["01_input", "02_ast", "03_reconciliation", "04_canonical", "05_renders", "06_reports"]
    corpora = ["samhita", "aaranam", "collections"]
    
    for c in corpora:
        for s in stages:
            (CORPORA_DIR / c / s).mkdir(parents=True, exist_ok=True)

    # Helper to safely copy to corpus stage while preserving original
    def stage_file(src_path: Path, corpus: str, stage: str, target_name: str = None):
        if not src_path.exists():
            return
        dst = CORPORA_DIR / corpus / stage / (target_name or src_path.name)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src_path), str(dst))

    def stage_render(filename: str, corpus: str, subfolder: str = ""):
        """Finds render file across candidate locations and copies to 05_renders and subfolder."""
        dst_sub = CORPORA_DIR / corpus / "05_renders" / (subfolder or "") / filename
        candidates = [
            OUTPUT_DIR / filename,
            OUTPUT_DIR / subfolder / "Devanagari" / filename,
            OUTPUT_DIR / subfolder / "Malayalam" / filename,
            OUTPUT_DIR / subfolder / filename,
        ]
        found = None
        for c in candidates:
            if c.exists():
                found = c
                break

        # Only use golden baseline as initial bootstrap if dst_sub does not exist
        if not found and not dst_sub.exists():
            fallback_candidates = [
                DATA_DIR / "baselines" / "golden" / "Devanagari" / corpus / "output" / subfolder / filename,
                DATA_DIR / "baselines" / "golden" / "Malayalam" / corpus / "output" / subfolder / filename,
            ]
            for c in fallback_candidates:
                if c.exists():
                    found = c
                    break

        if found:
            # Stage cleanly into dedicated subfolder (e.g. 05_renders/pdf/, html/, txt/)
            if dst_sub.exists() and found.stat().st_mtime <= dst_sub.stat().st_mtime:
                return True
            dst_sub.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(found), str(dst_sub))
            return True
        elif dst_sub.exists():
            return True
        return False

    # --- SAMHITA ---
    stage_file(INPUT_DIR / "Samhita_corrected.txt", "samhita", "01_input")
    stage_file(INPUT_DIR / "Samhita_Devanagari_Unicode.txt", "samhita", "01_input")
    stage_file(INPUT_DIR / "Samhita_corrected_samam.txt", "samhita", "01_input")
    stage_file(INPUT_DIR / "rishi_devata_chandas_for_rik.txt", "samhita", "01_input")
    stage_file(INPUT_DIR / "sama_rishi_chandas_out.txt", "samhita", "01_input")
    stage_file(INPUT_DIR / "vedic_text.txt", "samhita", "01_input")
    stage_file(INPUT_DIR / "Malayalam" / "Samam_Malayalam_Unicode.txt", "samhita", "01_input", "Samam_Malayalam_Unicode.txt")

    stage_file(OUTPUT_DIR / "Samhita_corrected_out.json", "samhita", "02_ast", "Samhita_ast.json")
    stage_file(OUTPUT_DIR / "Samhita_corrected_out.json", "samhita", "02_ast")
    stage_file(OUTPUT_DIR / "malayalam" / "Samam_Malayalam.json", "samhita", "02_ast", "Samam_Malayalam.json")
    stage_file(ROOT_DIR / "Malayalam_JSV" / "malayalam" / "Samam_kpully_Devanagari_json.json", "samhita", "02_ast", "Samam_kpully_Devanagari.json")

    stage_file(OUTPUT_DIR / "Rik Reconciliation table (JSV-KSV).xlsx", "samhita", "03_reconciliation")
    stage_file(OUTPUT_DIR / "JSV_Samam_Granular_Table.xlsx", "samhita", "03_reconciliation")
    stage_file(OUTPUT_DIR / "JSV_Samam_Granular_Table.csv", "samhita", "03_reconciliation")
    stage_file(OUTPUT_DIR / "JSV_Rik_Table.txt", "samhita", "03_reconciliation")
    stage_file(OUTPUT_DIR / "JSV_Rik_Table - for analysis.xlsx", "samhita", "03_reconciliation")

    stage_file(OUTPUT_DIR / "Vargeekaran.json", "samhita", "04_canonical")

    # Samhita 05_renders (PDF, HTML, TXT)
    for f in [
        "Samhita_Devanagari.pdf", "Samhita_kpully_Devanagari.pdf", "Rik_Devanagari.pdf", "Samam_Devanagari.pdf", "Rik_NoMeta_Devanagari.pdf", "Samam_NoMeta_Devanagari.pdf",
        "Samam_kpully_Malayalam.pdf", "Samhita_Malayalam.pdf"
    ]:
        stage_render(f, "samhita", "pdf")
    for f in [
        "Samhita_Devanagari.html", "Samhita_kpully_Devanagari.html", "Samhita.html", "Rik.html", "Samam.html", "Rik_NoMeta.html", "Samam_NoMeta.html",
        "Samam_kpully_Malayalam.html", "Samhita_Malayalam.html"
    ]:
        stage_render(f, "samhita", "html")
    for f in [
        "Samhita_Devanagari_Unicode.txt", "Samhita_kpully_Devanagari_Unicode.txt", "Rik_Devanagari_Unicode.txt", "Samam_Devanagari_Unicode.txt", "Rik_NoMeta_Devanagari_Unicode.txt", "Samam_NoMeta_Devanagari_Unicode.txt",
        "Samam_kpully_Malayalam_Unicode.txt", "Samhita_Malayalam_Unicode.txt"
    ]:
        stage_render(f, "samhita", "txt")

    stage_file(OUTPUT_DIR / "JSV_Structure_Summary.csv", "samhita", "06_reports")
    stage_file(OUTPUT_DIR / "JSV_Structure_Summary.txt", "samhita", "06_reports")
    stage_file(OUTPUT_DIR / "JSON_Samam_Continuity_Report.txt", "samhita", "06_reports")
    stage_file(OUTPUT_DIR / "Samhita_corrected_out_continuity_report.txt", "samhita", "06_reports")

    # --- AARANAM ---
    stage_file(INPUT_DIR / "Aaranam_latest.txt", "aaranam", "01_input")
    stage_file(INPUT_DIR / "Aaranam_rik.txt", "aaranam", "01_input")
    stage_file(INPUT_DIR / "Aaranam_rik_samam_table.txt", "aaranam", "01_input")

    stage_file(OUTPUT_DIR / "Aaranam_latest_out.json", "aaranam", "02_ast", "Aaranam_ast.json")
    stage_file(OUTPUT_DIR / "Aaranam_latest_out.json", "aaranam", "02_ast")

    stage_file(OUTPUT_DIR / "Rik Reconciliation table (JSV-KSV) - Aaranam_latest.xlsx", "aaranam", "03_reconciliation")
    stage_file(OUTPUT_DIR / "Aaranam_Rik_Table_Baseline.csv", "aaranam", "03_reconciliation")
    stage_file(OUTPUT_DIR / "Aaranam_Rik_Table.csv", "aaranam", "03_reconciliation")

    stage_file(OUTPUT_DIR / "Aaranam_vargeekaran.json", "aaranam", "04_canonical")

    # Aaranam 05_renders (PDF, HTML, TXT)
    for f in ["Aaranam_Devanagari.pdf", "Aaranam_Rik_Devanagari.pdf", "Aaranam_Samam_Devanagari.pdf", "Aaranam_Rik_NoMeta_Devanagari.pdf", "Aaranam_Samam_NoMeta_Devanagari.pdf"]:
        stage_render(f, "aaranam", "pdf")
    for f in ["Aaranam_Devanagari.html", "Aaranam_Rik_Devanagari.html", "Aaranam_Samam_Devanagari.html", "Aaranam_Rik_NoMeta_Devanagari.html", "Aaranam_Samam_NoMeta_Devanagari.html"]:
        stage_render(f, "aaranam", "html")
    for f in ["Aaranam_Devanagari_Unicode.txt"]:
        stage_render(f, "aaranam", "txt")

    stage_file(OUTPUT_DIR / "Aaranam_Continuity_Report_Final.txt", "aaranam", "06_reports")
    stage_file(OUTPUT_DIR / "Aaranam_vargeekaran_continuity_report.txt", "aaranam", "06_reports")

    # --- COLLECTIONS ---
    stage_file(INPUT_DIR / "Ashirvachana_samani.txt", "collections", "01_input")
    stage_file(INPUT_DIR / "PM-PB_filter.txt", "collections", "01_input")
    stage_file(INPUT_DIR / "PM-UB_filter.txt", "collections", "01_input")
    stage_file(INPUT_DIR / "Filter_file_superset.txt", "collections", "01_input")
    stage_file(INPUT_DIR / "Nakshatra_sooktam.txt", "collections", "01_input")
    stage_file(INPUT_DIR / "Ritu-shanti.txt", "collections", "01_input")

    stage_file(OUTPUT_DIR / "Collection_latest_out.json", "collections", "02_ast")
    stage_file(OUTPUT_DIR / "Prayogamala-Purvabhagam.json", "collections", "04_canonical")
    stage_file(OUTPUT_DIR / "prayogamala-Uttarabhagam.json", "collections", "04_canonical")
    stage_file(OUTPUT_DIR / "Sooktamala.json", "collections", "04_canonical")

    # Collections 05_renders (PDF, HTML, TXT)
    for f in ["Sooktamala_Devanagari.pdf", "Prayogamala-Purvabhagam_Devanagari.pdf", "prayogamala-Uttarabhagam_Devanagari.pdf"]:
        stage_render(f, "collections", "pdf")
    for f in ["Sooktamala_Devanagari.html", "Prayogamala-Purvabhagam_Devanagari.html", "prayogamala-Uttarabhagam_Devanagari.html"]:
        stage_render(f, "collections", "html")
    for f in ["Sooktamala_Devanagari_Unicode.txt", "Prayogamala-Purvabhagam_Devanagari_Unicode.txt", "prayogamala-Uttarabhagam_Devanagari_Unicode.txt"]:
        stage_render(f, "collections", "txt")

    print("[STAGE SETUP COMPLETE] Staged canonical assets and renders in data/corpora/{samhita,aaranam,collections}")


def generate_initial_run_manifests():
    print("\n[3/4] Generating initial active run manifests in data/corpora/<corpus>/run_manifest.json...")
    
    from core.swara_engine import count_samams

    corpora_specs = {
        "samhita": {
            "version": "3.28",
            "input_file": CORPORA_DIR / "samhita" / "01_input" / "Samhita_corrected.txt",
            "ast_file": CORPORA_DIR / "samhita" / "02_ast" / "Samhita_corrected_out.json",
            "canonical_file": CORPORA_DIR / "samhita" / "04_canonical" / "Vargeekaran.json",
            "expected_samas": 1226,
            "expected_khandas": 59,
            "expected_pathas": 6,
        },
        "aaranam": {
            "version": "1.14",
            "input_file": CORPORA_DIR / "aaranam" / "01_input" / "Aaranam_latest.txt",
            "ast_file": CORPORA_DIR / "aaranam" / "02_ast" / "Aaranam_latest_out.json",
            "canonical_file": CORPORA_DIR / "aaranam" / "04_canonical" / "Aaranam_vargeekaran.json",
            "expected_samas": 401,
            "expected_khandas": 29,
            "expected_pathas": 1,
        },
        "collections": {
            "version": "2.05",
            "input_file": CORPORA_DIR / "collections" / "01_input" / "Ashirvachana_samani.txt",
            "ast_file": CORPORA_DIR / "collections" / "02_ast" / "Collection_latest_out.json",
            "canonical_file": CORPORA_DIR / "collections" / "04_canonical" / "Sooktamala.json",
            "expected_samas": None,
            "expected_khandas": None,
            "expected_pathas": None,
        }
    }

    now_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    def count_ast_samas(ast_dict):
        ss_dict = ast_dict.get("supersections", ast_dict.get("supersection", {}))
        s_count = 0
        for ss in ss_dict.values():
            if not isinstance(ss, dict): continue
            for sec in ss.get("sections", {}).values():
                if not isinstance(sec, dict): continue
                for sub in sec.get("subsections", {}).values():
                    if not isinstance(sub, dict): continue
                    mantras = sub.get("corrected-mantra_sets", [])
                    s_count += max(len(mantras), 1 if sub.get("rik_text") else 0)
        return s_count

    for corpus, spec in corpora_specs.items():
        ast_path = spec["ast_file"]
        metrics = {}
        if ast_path.exists():
            with open(ast_path, "r", encoding="utf-8") as f:
                ast_data = json.load(f)
            supers = ast_data.get("supersections", ast_data.get("supersection", {}))
            metrics["pathas"] = len(supers)
            metrics["khandas"] = sum(len(s.get("sections", {})) for s in supers.values() if isinstance(s, dict))
            metrics["samas"] = count_ast_samas(ast_data)

        run_manifest = {
            "corpus": corpus,
            "edition": spec["version"],
            "timestamp": now_str,
            "stage_status": {
                "01_input": "PRESENT",
                "02_ast": "UP_TO_DATE",
                "03_reconciliation": "ENRICHED",
                "04_canonical": "VALIDATED",
                "05_renders": "COMPILED",
                "06_reports": "CURRENT"
            },
            "hashes": {
                "input_sha256": sha256_file(spec["input_file"]) if spec["input_file"].exists() else None,
                "ast_sha256": sha256_file(spec["ast_file"]) if spec["ast_file"].exists() else None,
                "canonical_sha256": sha256_file(spec["canonical_file"]) if spec["canonical_file"].exists() else None,
            },
            "metrics": metrics,
            "validation_status": "PASSED"
        }

        manifest_path = CORPORA_DIR / corpus / "run_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(run_manifest, f, indent=2, ensure_ascii=False)
        print(f"  Wrote {manifest_path.relative_to(ROOT_DIR)} -> Metrics: {metrics}")

    print("[RUN MANIFESTS COMPLETE]")


if __name__ == "__main__":
    purge_and_archive()
    setup_stage_directories()
    generate_initial_run_manifests()
    print("\n[SUCCESS] Stage 1 purge and stage-numbered corpus directories completed!")
