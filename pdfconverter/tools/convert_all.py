"""
Convert every chunk, audit it, and (optionally) build its review report.

One command for the whole pipeline after a decoder change:

    python pdfconverter/tools/convert_all.py            # convert + audit table
    python pdfconverter/tools/convert_all.py --review   # + grade + 3-way diff HTML

Each chunk is converted from its own `data/chunks/<name>.grantha.docx`; the
SETHU reference is only used for grading and for the review report, never as a
source of output text.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(HERE, "tools")
REPORTS = os.path.join(HERE, "reports")
MANIFEST = os.path.join(HERE, "data", "chunks", "manifest.json")

GATES = ["legacy_bytes", "dotted_circle", "double_nasal",
         "accent_before_virama", "latin_letters", "unknown_chars"]


def run(tool: str, *args: str) -> int:
    proc = subprocess.run([sys.executable, os.path.join(TOOLS, tool), *args],
                          capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        print(proc.stdout[-3000:])
        print(proc.stderr[-3000:])
    return proc.returncode


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--review", action="store_true",
                    help="also grade and write the three-way HTML report")
    ap.add_argument("--chunk", default=None, help="only this chunk")
    args = ap.parse_args()

    with open(MANIFEST, encoding="utf-8") as fh:
        manifest = json.load(fh)
    chunks = [c for c in manifest["chunks"]
              if args.chunk is None or c["name"] == args.chunk]
    os.makedirs(REPORTS, exist_ok=True)

    with open(os.path.join(HERE, "data", "reference", "sethu_anuvakas.json"),
              encoding="utf-8") as fh:
        oracle_keys = {(a["kandam"], a["prasna"]) for a in json.load(fh)["anuvakas"]}

    rows = []
    for chunk in chunks:
        name = chunk["name"]
        report = os.path.join(REPORTS, f"{name}.convert.json")
        if run("convert_chunk.py", "--chunk", name, "--json", report, "--no-fail"):
            rows.append((name, None))
            continue
        with open(report, encoding="utf-8") as fh:
            data = json.load(fh)
        rows.append((name, data))
        if args.review:
            if (chunk["kandam"], chunk["prasna"]) in oracle_keys:
                run("grade_chunk.py", "--chunk", name)
            run("diff_report.py", "--chunk", name)

    print(f"{'chunk':<9}" + "".join(f"{g:>21}" for g in GATES))
    dirty = False
    for name, data in rows:
        if data is None:
            print(f"{name:<9} CONVERSION FAILED")
            dirty = True
            continue
        audit = data["audit"]
        print(f"{name:<9}" + "".join(f"{audit[g]:>21}" for g in GATES))
        dirty = dirty or any(audit[g] for g in GATES)
    print("\nall gates clean" if not dirty else
          "\nsome gates are non-zero; see reports/<chunk>.diff.html for context")


if __name__ == "__main__":
    main()
