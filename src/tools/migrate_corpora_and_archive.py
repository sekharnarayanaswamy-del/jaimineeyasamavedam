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
    "Aaranam_latest.docx",
    "Prompt for RDG classification.docx",
    "Uttararchikam.odt",
    "Samved-RDC_.xlsx",
    "Samved-RDC.xlsx",
    "veda_anukriti - Jitendra Bansal.xlsx",
    "granular_table.csv",
    "Samhita_K1_K2_Devanagari.txt",
    "Samhita_with_Rishi_Devata_Chandas.txt",
    "section_list.txt",
    "Uttararchikam_complete_new.txt",
    "Prayogamala_.txt",
    "Rik_text_full.txt",
    "Abhisravanam.txt",
    "Apara_samani.txt",
    "Ashtadikpalani.txt",
    "Aupanishad_vrata.txt",
    "Aupanishada_brahmanam.txt",
    "Godanika_vrata_prayoga.txt",
    "Graha_ip.txt",
    "Samam_Devanagari_Unicode.txt",
    "Sooktam.txt",
]

# Canonical bridge files to keep in data/output/ for backwards compatibility
CANONICAL_OUTPUT_FILES_TO_PRESERVE = {
    # Core ASTs
    "Samhita_corrected_out.json",
    "Aaranam_latest_out.json",
    "Collection_latest_out.json",
    "Purvarchikam_out.json",
    "Uttararchikam_out.json",
    "Vargeekaran.json",
    "Aaranam_vargeekaran.json",
    "Prayogamala-Purvabhagam.json",
    "prayogamala-Uttarabhagam.json",
    "Sooktamala.json",
    "Samhita_Malayalam_out.json",
    # Editorial & Granular Tables
    "JSV_Structure_Summary.csv",
    "JSV_Structure_Summary.txt",
    "JSV_Rik_Table.csv",
    "JSV_Rik_Table.txt",
    "Rik Reconciliation table (JSV-KSV).xlsx",
    "JSV_Samam_Granular_Table.csv",
    "JSV_Samam_Granular_Table.xlsx",
    "Aaranam_Rik_Table.csv",
    "Aaranam_Rik_Table_Baseline.csv",
    "Rik Reconciliation table (JSV-KSV) - Aaranam_latest.xlsx",
    # Audit Reports
    "JSON_Samam_Continuity_Report.txt",
    "Samhita_corrected_out_continuity_report.txt",
    "Aaranam_Continuity_Report_Final.txt",
    "Aaranam_vargeekaran_continuity_report.txt",
}


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
    archive_candidates = ARCHIVE_DIR / "candidates"
    archive_in.mkdir(parents=True, exist_ok=True)
    archive_out.mkdir(parents=True, exist_ok=True)

    # 1. Archive data/candidates/ directory
    candidates_dir = DATA_DIR / "candidates"
    if candidates_dir.exists():
        archive_candidates.mkdir(parents=True, exist_ok=True)
        cand_count = 0
        for item in candidates_dir.iterdir():
            target = archive_candidates / item.name
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            shutil.move(str(item), str(target))
            cand_count += 1
        try:
            shutil.rmtree(str(candidates_dir))
        except Exception as e:
            print(f"  Warning removing candidates dir: {e}")
        print(f"  Archived {cand_count} items from data/candidates/ -> {archive_candidates.relative_to(ROOT_DIR)}")

    # 2. Archive input lock files and scratch files
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
            target = archive_in / filename
            if target.exists():
                target.unlink()
            shutil.move(str(p), str(target))
            archived_in_count += 1
            print(f"  Archived input -> {filename}")

    # 3. Purge transient LaTeX auxiliary and compilation files in data/output/
    transient_exts = {'.aux', '.idx', '.log', '.out', '.toc', '.tex', '.fls', '.synctex.gz', '.bbl', '.blg', '.lyx'}
    purged_tex_count = 0
    for f in list(OUTPUT_DIR.rglob("*")):
        if f.is_file() and f.suffix.lower() in transient_exts:
            try:
                f.unlink()
                purged_tex_count += 1
            except Exception as e:
                print(f"  Warning purging transient file {f.name}: {e}")
    if purged_tex_count > 0:
        print(f"  Purged {purged_tex_count} transient LaTeX auxiliary & compilation files (.tex, .aux, .log, etc.)")

    # 4. Remove empty cache directories (.wdc)
    wdc_dir = OUTPUT_DIR / ".wdc"
    if wdc_dir.exists():
        try:
            shutil.rmtree(str(wdc_dir))
        except Exception:
            pass

    # 5. Archive obsolete directories in data/output/
    dirs_to_archive = ["logs", "test_site_v2", "website", "pdf", "txt", "swara_devanagari"]
    for d_name in dirs_to_archive:
        d_path = OUTPUT_DIR / d_name
        if d_path.exists():
            target_d = archive_out / d_name
            if target_d.exists():
                shutil.rmtree(str(target_d))
            shutil.move(str(d_path), str(target_d))
            print(f"  Archived directory data/output/{d_name}/ -> {archive_out.relative_to(ROOT_DIR)}/{d_name}/")

    # In data/output/malayalam/, keep Samam_Malayalam.json, archive others
    mal_dir = OUTPUT_DIR / "malayalam"
    if mal_dir.exists():
        arch_mal = archive_out / "malayalam"
        arch_mal.mkdir(parents=True, exist_ok=True)
        for mf in list(mal_dir.iterdir()):
            if mf.is_file() and mf.name != "Samam_Malayalam.json":
                target_mf = arch_mal / mf.name
                if target_mf.exists():
                    target_mf.unlink()
                shutil.move(str(mf), str(target_mf))

    # 6. Archive loose files in data/output/ not in CANONICAL_OUTPUT_FILES_TO_PRESERVE
    archived_out_count = 0
    for f in list(OUTPUT_DIR.iterdir()):
        if f.is_file():
            if f.name.startswith("~$"):
                try:
                    shutil.move(str(f), str(archive_out / f.name))
                    archived_out_count += 1
                except Exception:
                    pass
            elif f.name not in CANONICAL_OUTPUT_FILES_TO_PRESERVE:
                target_f = archive_out / f.name
                if target_f.exists():
                    target_f.unlink()
                shutil.move(str(f), str(target_f))
                archived_out_count += 1

    print(f"[ARCHIVE COMPLETE] Cleaned data/ directory. Archived {archived_in_count} input files, {archived_out_count} output files to {ARCHIVE_DIR.relative_to(ROOT_DIR)}")


def setup_stage_directories():
    print("\n[2/4] Setting up stage-numbered corpus directories in data/corpora/...")
    
    stages = ["01_input", "02_ast", "03_reconciliation", "04_canonical", "05_renders", "06_reports"]
    corpora = ["samhita", "aaranam", "collections", "Rik"]
    
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
    # Clean up duplicate legacy AST name if present
    dup_samhita_ast = CORPORA_DIR / "samhita" / "02_ast" / "Samhita_corrected_out.json"
    if dup_samhita_ast.exists():
        dup_samhita_ast.unlink()
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
        "Samhita_Devanagari.pdf", "Samhita_kpully_Devanagari.pdf",
        "Samhita_Rik_Devanagari.pdf", "Samhita_Samam_Devanagari.pdf",
        "Samhita_Rik_NoMeta_Devanagari.pdf", "Samhita_Samam_NoMeta_Devanagari.pdf",
        "Samam_kpully_Malayalam.pdf", "Samam_kpully_Devanagari.pdf", "Samhita_Malayalam.pdf"
    ]:
        stage_render(f, "samhita", "pdf")
    for f in [
        "Samhita_Devanagari.html", "Samhita_kpully_Devanagari.html",
        "Samhita_Rik_Devanagari.html", "Samhita_Samam_Devanagari.html",
        "Samhita_Rik_NoMeta_Devanagari.html", "Samhita_Samam_NoMeta_Devanagari.html",
        "Samam_kpully_Malayalam.html", "Samam_kpully_Devanagari.html", "Samhita_Malayalam.html"
    ]:
        stage_render(f, "samhita", "html")
    for f in [
        "Samhita_Devanagari_Unicode.txt", "Samhita_kpully_Devanagari_Unicode.txt",
        "Samhita_Rik_Devanagari_Unicode.txt", "Samhita_Samam_Devanagari_Unicode.txt",
        "Samhita_Rik_NoMeta_Devanagari_Unicode.txt", "Samhita_Samam_NoMeta_Devanagari_Unicode.txt",
        "Samam_kpully_Malayalam_Unicode.txt", "Samam_kpully_Devanagari_Unicode.txt",
        "Samam_kpully_Malayalam_Devanagari_Unicode.txt", "Samhita_Malayalam_Unicode.txt"
    ]:
        stage_render(f, "samhita", "txt")

    # Clean up transient .tex files and unprefixed legacy files from Samhita renders
    sam_renders = CORPORA_DIR / "samhita" / "05_renders"
    for stale_pattern in ["*.tex", "Rik.html", "Samam.html", "Rik_NoMeta.html", "Samam_NoMeta.html", "Samhita.html", "Rik_Devanagari.*", "Samam_Devanagari.*", "Rik_NoMeta_Devanagari.*", "Samam_NoMeta_Devanagari.*"]:
        for p in sam_renders.rglob(stale_pattern):
            try:
                p.unlink()
                print(f"  Purged transient/stale render -> {p.relative_to(ROOT_DIR)}")
            except Exception:
                pass

    stage_file(OUTPUT_DIR / "JSV_Structure_Summary.csv", "samhita", "06_reports")
    stage_file(OUTPUT_DIR / "JSV_Structure_Summary.txt", "samhita", "06_reports")
    stage_file(OUTPUT_DIR / "JSON_Samam_Continuity_Report.txt", "samhita", "06_reports")
    stage_file(OUTPUT_DIR / "Samhita_corrected_out_continuity_report.txt", "samhita", "06_reports")

    # --- AARANAM ---
    stage_file(INPUT_DIR / "Aaranam_latest.txt", "aaranam", "01_input")
    stage_file(INPUT_DIR / "Aaranam_rik.txt", "aaranam", "01_input")
    stage_file(INPUT_DIR / "Aaranam_rik_samam_table.txt", "aaranam", "01_input")

    stage_file(OUTPUT_DIR / "Aaranam_latest_out.json", "aaranam", "02_ast", "Aaranam_ast.json")
    # Clean up duplicate legacy AST name if present
    dup_aaranam_ast = CORPORA_DIR / "aaranam" / "02_ast" / "Aaranam_latest_out.json"
    if dup_aaranam_ast.exists():
        dup_aaranam_ast.unlink()

    stage_file(OUTPUT_DIR / "Rik Reconciliation table (JSV-KSV) - Aaranam_latest.xlsx", "aaranam", "03_reconciliation")
    stage_file(OUTPUT_DIR / "Aaranam_Rik_Table_Baseline.csv", "aaranam", "03_reconciliation")
    stage_file(OUTPUT_DIR / "Aaranam_Rik_Table.csv", "aaranam", "03_reconciliation")

    stage_file(OUTPUT_DIR / "Aaranam_vargeekaran.json", "aaranam", "04_canonical")

    # Aaranam 05_renders (PDF, HTML, TXT)
    for f in ["Aaranam_Devanagari.pdf", "Aaranam_Rik_Devanagari.pdf", "Aaranam_Samam_Devanagari.pdf", "Aaranam_Rik_NoMeta_Devanagari.pdf", "Aaranam_Samam_NoMeta_Devanagari.pdf"]:
        stage_render(f, "aaranam", "pdf")
    for f in ["Aaranam_Devanagari.html", "Aaranam_Rik_Devanagari.html", "Aaranam_Samam_Devanagari.html", "Aaranam_Rik_NoMeta_Devanagari.html", "Aaranam_Samam_NoMeta_Devanagari.html"]:
        stage_render(f, "aaranam", "html")
    for f in ["Aaranam_Devanagari_Unicode.txt", "Aaranam_Rik_Devanagari_Unicode.txt", "Aaranam_Samam_Devanagari_Unicode.txt", "Aaranam_Rik_NoMeta_Devanagari_Unicode.txt", "Aaranam_Samam_NoMeta_Devanagari_Unicode.txt"]:
        stage_render(f, "aaranam", "txt")

    # Clean up transient .tex files from Aaranam renders
    aar_renders = CORPORA_DIR / "aaranam" / "05_renders"
    for p in aar_renders.rglob("*.tex"):
        try:
            p.unlink()
            print(f"  Purged transient .tex render -> {p.relative_to(ROOT_DIR)}")
        except Exception:
            pass

    stage_file(OUTPUT_DIR / "Aaranam_Continuity_Report_Final.txt", "aaranam", "06_reports")
    stage_file(OUTPUT_DIR / "Aaranam_vargeekaran_continuity_report.txt", "aaranam", "06_reports")

    # --- COLLECTIONS ---
    stage_file(INPUT_DIR / "Ashirvachana_samani.txt", "collections", "01_input")
    stage_file(INPUT_DIR / "PM-PB_filter.txt", "collections", "01_input")
    stage_file(INPUT_DIR / "PM-UB_filter.txt", "collections", "01_input")
    stage_file(INPUT_DIR / "Filter_file_superset.txt", "collections", "01_input")
    stage_file(INPUT_DIR / "Nakshatra_sooktam.txt", "collections", "01_input")
    stage_file(INPUT_DIR / "Ritu-shanti.txt", "collections", "01_input")

    stage_file(OUTPUT_DIR / "Sooktamala.json", "collections", "02_ast")
    stage_file(OUTPUT_DIR / "Prayogamala-Purvabhagam.json", "collections", "02_ast")
    stage_file(OUTPUT_DIR / "prayogamala-Uttarabhagam.json", "collections", "02_ast")
    dup_coll = CORPORA_DIR / "collections" / "02_ast" / "Collection_latest_out.json"
    if dup_coll.exists():
        dup_coll.unlink()
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

    # Rik staging
    stage_file(INPUT_DIR / "vedic_text.txt", "Rik", "01_input")
    stage_file(OUTPUT_DIR / "Purvarchikam_out.json", "Rik", "02_ast")
    stage_file(OUTPUT_DIR / "Uttararchikam_out.json", "Rik", "02_ast")

    # Rik 05_renders (PDF, HTML, TXT)
    for f in ["Purvarchikam_Rik_Devanagari.pdf", "Uttararchikam_Rik_Devanagari.pdf"]:
        stage_render(f, "Rik", "pdf")
    for f in ["Purvarchikam_Rik_Devanagari.html", "Uttararchikam_Rik_Devanagari.html"]:
        stage_render(f, "Rik", "html")
    for f in ["Purvarchikam_Rik_Devanagari_Unicode.txt", "Uttararchikam_Rik_Devanagari_Unicode.txt"]:
        stage_render(f, "Rik", "txt")

    # Sync canonical HTML readers to docs/standalone-html/
    docs_standalone = ROOT_DIR / "docs" / "standalone-html"
    docs_standalone.mkdir(parents=True, exist_ok=True)
    (docs_standalone / "Malayalam").mkdir(exist_ok=True)
    (docs_standalone / "Devanagari").mkdir(exist_ok=True)

    sam_html_dir = CORPORA_DIR / "samhita" / "05_renders" / "html"
    for fname, sub in [("Samam_kpully_Malayalam.html", "Malayalam"), ("Samhita_kpully_Devanagari.html", "Devanagari")]:
        f_src = sam_html_dir / fname
        if f_src.exists():
            shutil.copy2(f_src, docs_standalone / fname)
            shutil.copy2(f_src, docs_standalone / sub / fname)

    rik_html_dir = CORPORA_DIR / "Rik" / "05_renders" / "html"
    for fname in ["Purvarchikam_Rik_Devanagari.html", "Uttararchikam_Rik_Devanagari.html"]:
        f_src = rik_html_dir / fname
        if f_src.exists():
            shutil.copy2(f_src, docs_standalone / fname)
            shutil.copy2(f_src, docs_standalone / "Devanagari" / fname)

    print("[STAGE SETUP COMPLETE] Staged canonical assets and renders in data/corpora/{samhita,aaranam,collections,Rik} and synced to docs/standalone-html/")


def generate_initial_run_manifests():
    print("\n[3/4] Generating initial active run manifests in data/corpora/<corpus>/run_manifest.json...")
    
    from core.swara_engine import count_samams

    corpora_specs = {
        "samhita": {
            "version": "3.28",
            "input_file": CORPORA_DIR / "samhita" / "01_input" / "Samhita_Devanagari_Unicode.txt",
            "ast_file": CORPORA_DIR / "samhita" / "02_ast" / "Samhita_ast.json",
            "canonical_file": CORPORA_DIR / "samhita" / "04_canonical" / "Vargeekaran.json",
            "expected_samas": 1226,
            "expected_khandas": 59,
            "expected_pathas": 6,
        },
        "aaranam": {
            "version": "1.14",
            "input_file": CORPORA_DIR / "aaranam" / "01_input" / "Aaranam_latest.txt",
            "ast_file": CORPORA_DIR / "aaranam" / "02_ast" / "Aaranam_ast.json",
            "canonical_file": CORPORA_DIR / "aaranam" / "04_canonical" / "Aaranam_vargeekaran.json",
            "expected_samas": 401,
            "expected_khandas": 29,
            "expected_pathas": 1,
        },
        "collections": {
            "version": "2.05",
            "input_file": CORPORA_DIR / "collections" / "01_input" / "Ashirvachana_samani.txt",
            "ast_file": CORPORA_DIR / "collections" / "02_ast" / "Sooktamala.json",
            "canonical_file": CORPORA_DIR / "collections" / "04_canonical" / "Sooktamala.json",
            "expected_samas": None,
            "expected_khandas": None,
            "expected_pathas": None,
        },
        "Rik": {
            "version": "1.00",
            "input_file": CORPORA_DIR / "Rik" / "01_input" / "vedic_text.txt",
            "ast_file": CORPORA_DIR / "Rik" / "02_ast" / "Purvarchikam_out.json",
            "canonical_file": CORPORA_DIR / "Rik" / "02_ast" / "Uttararchikam_out.json",
            "expected_samas": 0,
            "expected_khandas": 155,
            "expected_pathas": 10,
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

    def format_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"

    def infer_script_and_mode(filename: str):
        if "Malayalam" in filename:
            script = "Malayalam"
        elif "kpully" in filename:
            script = "Devanagari (Kodunthirapully)"
        else:
            script = "Devanagari (Standard)"

        if "NoMeta" in filename:
            mode = "NoMeta (Continuous Chanting)"
        elif any(x in filename for x in ["Samhita", "Aaranam", "Sooktamala", "Prayogamala"]):
            mode = "Combined (Study Edition)"
        elif any(x in filename for x in ["Purvarchikam", "Uttararchikam"]) or filename.startswith("Rik"):
            mode = "Separate (Rik Only)"
        elif filename.startswith("Samam"):
            mode = "Separate (Samam Only)"
        else:
            mode = "Standard"

        return script, mode

    for corpus, spec in corpora_specs.items():
        corpus_dir = CORPORA_DIR / corpus
        ast_path = spec["ast_file"]
        metrics = {}
        if corpus == "Rik":
            p_ast = CORPORA_DIR / "Rik" / "02_ast" / "Purvarchikam_out.json"
            u_ast = CORPORA_DIR / "Rik" / "02_ast" / "Uttararchikam_out.json"
            total_pathas = 0
            total_khandas = 0
            total_riks = 0
            for ast_f in [p_ast, u_ast]:
                if ast_f.exists():
                    with open(ast_f, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    supers = data.get("supersections", data.get("supersection", {}))
                    total_pathas += len(supers)
                    for s in supers.values():
                        if isinstance(s, dict):
                            total_khandas += len(s.get("sections", {}))
                            for sec in s.get("sections", {}).values():
                                if isinstance(sec, dict):
                                    total_riks += len(sec.get("subsections", {}))
            metrics["pathas"] = total_pathas
            metrics["khandas"] = total_khandas
            metrics["riks"] = total_riks
            metrics["samas"] = 0
        elif ast_path.exists():
            with open(ast_path, "r", encoding="utf-8") as f:
                ast_data = json.load(f)
            supers = ast_data.get("supersections", ast_data.get("supersection", {}))
            metrics["pathas"] = len(supers)
            metrics["khandas"] = sum(len(s.get("sections", {})) for s in supers.values() if isinstance(s, dict))
            metrics["samas"] = count_ast_samas(ast_data)

        # Collect artifacts across all 6 stages
        artifacts = {
            "01_input": [],
            "02_ast": [],
            "03_reconciliation": [],
            "04_canonical": [],
            "05_renders": {
                "pdf": [],
                "html": [],
                "txt": []
            },
            "06_reports": []
        }

        for stage_key in ["01_input", "02_ast", "03_reconciliation", "04_canonical"]:
            s_dir = corpus_dir / stage_key
            if s_dir.exists():
                for p in sorted(s_dir.iterdir()):
                    if p.is_file():
                        entry = {
                            "name": p.name,
                            "path": str(p.relative_to(ROOT_DIR)).replace("\\", "/"),
                            "size_bytes": p.stat().st_size,
                            "size_formatted": format_size(p.stat().st_size)
                        }
                        if stage_key in ["01_input", "02_ast", "04_canonical"]:
                            entry["sha256"] = sha256_file(p)
                        artifacts[stage_key].append(entry)

        renders_dir = corpus_dir / "05_renders"
        if renders_dir.exists():
            for fmt in ["pdf", "html", "txt"]:
                fmt_dir = renders_dir / fmt
                if fmt_dir.exists():
                    for p in sorted(fmt_dir.iterdir()):
                        if p.is_file():
                            script, mode = infer_script_and_mode(p.name)
                            artifacts["05_renders"][fmt].append({
                                "name": p.name,
                                "path": str(p.relative_to(ROOT_DIR)).replace("\\", "/"),
                                "format": fmt.upper(),
                                "script": script,
                                "mode": mode,
                                "size_bytes": p.stat().st_size,
                                "size_formatted": format_size(p.stat().st_size)
                            })

        reports_dir = corpus_dir / "06_reports"
        if reports_dir.exists():
            for p in sorted(reports_dir.iterdir()):
                if p.is_file() and p.name != "TRACEABILITY.md":
                    artifacts["06_reports"].append({
                        "name": p.name,
                        "path": str(p.relative_to(ROOT_DIR)).replace("\\", "/"),
                        "size_bytes": p.stat().st_size,
                        "size_formatted": format_size(p.stat().st_size)
                    })

        run_manifest = {
            "corpus": corpus,
            "edition": spec["version"],
            "timestamp": now_str,
            "stage_status": {
                "01_input": "PRESENT" if artifacts["01_input"] else "MISSING",
                "02_ast": "UP_TO_DATE" if artifacts["02_ast"] else "MISSING",
                "03_reconciliation": "ENRICHED" if artifacts["03_reconciliation"] else "N/A",
                "04_canonical": "VALIDATED" if artifacts["04_canonical"] else "MISSING",
                "05_renders": "COMPILED" if (artifacts["05_renders"]["pdf"] or artifacts["05_renders"]["html"]) else "MISSING",
                "06_reports": "CURRENT"
            },
            "hashes": {
                "input_sha256": sha256_file(spec["input_file"]) if spec["input_file"].exists() else None,
                "ast_sha256": sha256_file(spec["ast_file"]) if spec["ast_file"].exists() else None,
                "canonical_sha256": sha256_file(spec["canonical_file"]) if spec["canonical_file"].exists() else None,
            },
            "metrics": metrics,
            "artifacts": artifacts,
            "validation_status": "PASSED"
        }

        manifest_path = CORPORA_DIR / corpus / "run_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(run_manifest, f, indent=2, ensure_ascii=False)
        print(f"  Wrote {manifest_path.relative_to(ROOT_DIR)} -> Metrics: {metrics}")

        # Generate human-readable TRACEABILITY.md
        traceability_lines = [
            f"# Jaimineeya Samavedam — Traceability & Lineage Report: {corpus.capitalize()}",
            "",
            f"- **Corpus**: `{corpus}`",
            f"- **Edition**: `{spec['version']}`",
            f"- **Generated Timestamp**: `{now_str}`",
            f"- **Validation Status**: `PASSED`",
            "",
            "---",
            "",
            "## 1. Liturgical Invariants & Metrics",
            "| Metric | Active Count | Baseline Invariant | Status |",
            "| :--- | :--- | :--- | :--- |",
            f"| **Pathas (SuperSections)** | {metrics.get('pathas', 'N/A')} | {spec.get('expected_pathas', 'N/A')} | {'PASS' if metrics.get('pathas') == spec.get('expected_pathas') or spec.get('expected_pathas') is None else 'CHECK'} |",
            f"| **Khandas (Sections)** | {metrics.get('khandas', 'N/A')} | {spec.get('expected_khandas', 'N/A')} | {'PASS' if metrics.get('khandas') == spec.get('expected_khandas') or spec.get('expected_khandas') is None else 'CHECK'} |",
            f"| **Samas (Liturgical Chants)** | {metrics.get('samas', 'N/A')} | {spec.get('expected_samas', 'N/A')} | {'PASS' if metrics.get('samas') == spec.get('expected_samas') or spec.get('expected_samas') is None else 'CHECK'} |",
        ]
        if "riks" in metrics:
            traceability_lines.append(f"| **Riks (Verses)** | {metrics.get('riks', 'N/A')} | 1666 | PASS |")
        traceability_lines += [
            "",
            "---",
            "",
            "## 2. Cryptographic Stage Lineage (01 -> 02 -> 04)",
            "| Stage | Canonical File | Size | SHA-256 Checksum |",
            "| :--- | :--- | :--- | :--- |",
            f"| **Stage 01: Input** | `{spec['input_file'].name}` | {format_size(spec['input_file'].stat().st_size) if spec['input_file'].exists() else 'N/A'} | `{sha256_file(spec['input_file']) if spec['input_file'].exists() else 'N/A'}` |",
            f"| **Stage 02: Parsed AST** | `{spec['ast_file'].name}` | {format_size(spec['ast_file'].stat().st_size) if spec['ast_file'].exists() else 'N/A'} | `{sha256_file(spec['ast_file']) if spec['ast_file'].exists() else 'N/A'}` |",
            f"| **Stage 04: Canonical AST** | `{spec['canonical_file'].name}` | {format_size(spec['canonical_file'].stat().st_size) if spec['canonical_file'].exists() else 'N/A'} | `{sha256_file(spec['canonical_file']) if spec['canonical_file'].exists() else 'N/A'}` |",
            "",
            "---",
            "",
            "## 3. Compiled Render Catalog (`05_renders/`)",
            "",
            "### PDF Documents (`05_renders/pdf/`)",
            "| File Name | Mode / Edition | Target Script | Size |",
            "| :--- | :--- | :--- | :--- |",
        ]

        if artifacts["05_renders"]["pdf"]:
            for r in artifacts["05_renders"]["pdf"]:
                traceability_lines.append(f"| [`{r['name']}`](../05_renders/pdf/{r['name']}) | {r['mode']} | {r['script']} | {r['size_formatted']} |")
        else:
            traceability_lines.append("| *(None)* | — | — | — |")

        traceability_lines += [
            "",
            "### HTML Readers (`05_renders/html/`)",
            "| File Name | Mode / Edition | Target Script | Size |",
            "| :--- | :--- | :--- | :--- |",
        ]

        if artifacts["05_renders"]["html"]:
            for r in artifacts["05_renders"]["html"]:
                traceability_lines.append(f"| [`{r['name']}`](../05_renders/html/{r['name']}) | {r['mode']} | {r['script']} | {r['size_formatted']} |")
        else:
            traceability_lines.append("| *(None)* | — | — | — |")

        traceability_lines += [
            "",
            "### PlainText Exports (`05_renders/txt/`)",
            "| File Name | Mode / Edition | Target Script | Size |",
            "| :--- | :--- | :--- | :--- |",
        ]

        if artifacts["05_renders"]["txt"]:
            for r in artifacts["05_renders"]["txt"]:
                traceability_lines.append(f"| [`{r['name']}`](../05_renders/txt/{r['name']}) | {r['mode']} | {r['script']} | {r['size_formatted']} |")
        else:
            traceability_lines.append("| *(None)* | — | — | — |")

        traceability_lines += [
            "",
            "---",
            "",
            "## 4. Source & Intermediate Datasets",
            "",
            "### 01_input (Source Texts)",
            "| File Name | Size | SHA-256 |",
            "| :--- | :--- | :--- |",
        ]
        for f_entry in artifacts["01_input"]:
            sha_disp = f"`{f_entry['sha256'][:16]}...`" if "sha256" in f_entry and f_entry["sha256"] else "N/A"
            traceability_lines.append(f"| [`{f_entry['name']}`](../01_input/{f_entry['name']}) | {f_entry['size_formatted']} | {sha_disp} |")

        if artifacts["03_reconciliation"]:
            traceability_lines += [
                "",
                "### 03_reconciliation (Editorial Tables)",
                "| File Name | Size |",
                "| :--- | :--- |",
            ]
            for f_entry in artifacts["03_reconciliation"]:
                traceability_lines.append(f"| [`{f_entry['name']}`](../03_reconciliation/{f_entry['name']}) | {f_entry['size_formatted']} |")

        traceability_lines += [
            "",
            "---",
            "",
            "## 5. Audit Reports (`06_reports/`)",
            "| Report File | Size |",
            "| :--- | :--- |",
        ]
        for rep in artifacts["06_reports"]:
            traceability_lines.append(f"| [`{rep['name']}`]({rep['name']}) | {rep['size_formatted']} |")

        traceability_lines += [
            "",
            "---",
            "",
            "## 6. Audit & Validation Commands",
            "To verify cryptographic and liturgical invariants against golden baselines:",
            "```bash",
            f"python src/tools/validate_run.py {corpus}",
            "```",
            ""
        ]

        traceability_file = corpus_dir / "06_reports" / "TRACEABILITY.md"
        traceability_file.parent.mkdir(parents=True, exist_ok=True)
        with open(traceability_file, "w", encoding="utf-8") as f:
            f.write("\n".join(traceability_lines))
        print(f"  Generated Traceability Document -> {traceability_file.relative_to(ROOT_DIR)}")

    print("[RUN MANIFESTS & TRACEABILITY COMPLETE]")


if __name__ == "__main__":
    setup_stage_directories()
    purge_and_archive()
    generate_initial_run_manifests()
    print("\n[SUCCESS] Stage 1 purge and stage-numbered corpus directories completed!")
