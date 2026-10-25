"""
Export the SETHU ground truth to versioned JSON.

`*.docx` is git-ignored, so the only copy of the oracle is an ignored binary
with a Devanagari filename.  This tool freezes exactly the text the grader
uses into `data/reference/sethu_anuvakas.json` (Kandam 1 Prasnas 1-4, one
record per anuvaka) so that:

  * the oracle is reviewable and diffable in git,
  * the grader can run without the .docx present,
  * a changed oracle shows up as a diff instead of silently moving the goalposts.

    python pdfconverter/tools/export_reference.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_reference as A


def export(ref_path: str) -> dict:
    ref = A.segment_reference(ref_path)
    records = []
    for (kandam, prasna, anuvaka), text in sorted(ref.items()):
        clean = A.normalize(text)
        records.append({
            "kandam": kandam,
            "prasna": prasna,
            "anuvaka": anuvaka,
            "text": clean,
            "words": len(clean.split()),
            "characters": len(clean.replace(" ", "")),
        })
    with open(ref_path, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    return {
        "source": os.path.basename(ref_path),
        "source_sha256": digest,
        "anuvaka_count": len(records),
        "words": sum(r["words"] for r in records),
        "characters": sum(r["characters"] for r in records),
        "anuvakas": records,
    }


def main() -> None:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ref", default=os.path.join(
        here, "data", "input", "THAITHIREEYA SAMHITHA 1 (SETHU) प्रथम पादः .docx"))
    ap.add_argument("--out", default=os.path.join(
        here, "data", "reference", "sethu_anuvakas.json"))
    args = ap.parse_args()

    data = export(args.ref)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(f"{data['anuvaka_count']} anuvakas, {data['words']} words, "
          f"{data['characters']} chars -> {args.out}")
    print(f"source sha256 {data['source_sha256'][:16]}...")


if __name__ == "__main__":
    main()
