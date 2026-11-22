"""
Grantha Pipeline Runner for Jaimineeya Samavedam.
-------------------------------------------------
Generates PDF, HTML, and TXT outputs for Samhita and Aranyakam (Aaranam)
transliterated into the Grantha script.
Explicitly excludes micro-website generation.
"""

import sys
import os
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

CORPORA = [
    {
        "name": "Aranyakam",
        "type": "aaranam",
        "input": "data/corpora/aaranam/02_ast/Aaranam_ast.json",
        "out_name": "Aaranam_Grantha",
        "expected_files": [
            "data/corpora/aaranam/05_renders/pdf/Aaranam_Grantha.pdf",
            "data/corpora/aaranam/05_renders/html/Aaranam_Grantha.html",
            "data/corpora/aaranam/05_renders/txt/Aaranam_Grantha_Unicode.txt",
        ]
    },
    {
        "name": "Samhita",
        "type": "samhita",
        "input": "data/corpora/samhita/02_ast/Samhita_ast.json",
        "out_name": "Samhita_Grantha",
        "expected_files": [
            "data/corpora/samhita/05_renders/pdf/Samhita_Grantha.pdf",
            "data/corpora/samhita/05_renders/html/Samhita_Grantha.html",
            "data/corpora/samhita/05_renders/txt/Samhita_Grantha_Unicode.txt",
        ]
    }
]

def run_grantha_pipeline():
    python_exe = sys.executable
    render_script = str(ROOT_DIR / "src" / "render.py")
    all_success = True

    print("=" * 70)
    print("JAIMINEEYA SAMAVEDAM - GRANTHA SCRIPT RENDERING PIPELINE")
    print("Targets: PDF (LuaLaTeX), HTML (VedaVMS Reader), TXT (Plain Unicode)")
    print("Corpora: Samhita and Aranyakam (Aaranam)")
    print("Note: Website generation is intentionally skipped.")
    print("=" * 70)

    for corpus in CORPORA:
        name = corpus["name"]
        inp = str(ROOT_DIR / corpus["input"])
        out = corpus["out_name"]
        ctype = corpus["type"]

        print(f"\n[>>>] Processing {name} ({ctype})...")
        cmd = [
            python_exe,
            render_script,
            inp,
            "--script", "grantha",
            "--type", ctype,
            "--flow",
            "-o", out
        ]

        res = subprocess.run(cmd, cwd=str(ROOT_DIR))
        if res.returncode != 0:
            print(f"[ERROR] Failed to render {name} in Grantha script (exit code {res.returncode})")
            all_success = False
        else:
            print(f"[OK] Render completed for {name}.")
            for exp in corpus["expected_files"]:
                exp_path = ROOT_DIR / exp
                if exp_path.exists():
                    print(f"     + {exp} ({exp_path.stat().st_size:,} bytes)")
                else:
                    print(f"     ! Missing expected file: {exp}")
                    all_success = False

    print("\n" + "=" * 70)
    if all_success:
        print("[SUCCESS] All Grantha renders generated and verified successfully!")
    else:
        print("[FAILURE] Some files failed to generate. Check logs above.")
    print("=" * 70)
    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(run_grantha_pipeline())
