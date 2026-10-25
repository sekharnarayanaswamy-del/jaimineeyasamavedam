"""
Word-level diff between the decoded Grantha text and the SETHU reference.

    python pdfconverter/tools/diff_anuvaka.py 1 4 16
    python pdfconverter/tools/diff_anuvaka.py 1 1 1 --chars
    python pdfconverter/tools/diff_anuvaka.py --worst 5

`--chars` zooms into the differing words and marks the first character
difference, which is what identifies a bad map entry.
"""
from __future__ import annotations

import argparse
import difflib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_reference as A
import ganapathy_map as M

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRANTHA = os.path.join(HERE, "data", "input", "1st Paadam Final-Grantha-Cleaned.docx")
REF = os.path.join(HERE, "data", "input", "THAITHIREEYA SAMHITHA 1 (SETHU) प्रथम पादः .docx")


def decoded(key, grantha):
    raw = " ".join(grantha[key])
    text = A.normalize(M.decode_text(raw))
    if A.is_tamil(text):
        text = " ".join(w for w in text.split() if not A.is_tamil(w))
    return text


def show(key, grantha, ref, chars: bool, max_pairs: int) -> None:
    if key not in grantha or key not in ref:
        print(f"{key}: missing on one side")
        return
    ref_text = A.normalize(ref[key])
    dec_text = decoded(key, grantha)
    rw, dw = A.base_form(ref_text).split(), A.base_form(dec_text).split()
    sm = difflib.SequenceMatcher(None, rw, dw, autojunk=False)
    subs = [b for b in sm.get_opcodes() if b[0] != "equal"]
    print(f"\n=== K{key[0]}P{key[1]}A{key[2]}  ref words {len(rw)}  dec words {len(dw)}  "
          f"diff blocks {len(subs)}")
    shown = 0
    for tag, i1, i2, j1, j2 in subs:
        if shown >= max_pairs:
            print("  …")
            break
        shown += 1
        print(f"\n  [{tag}] ref: {' '.join(rw[i1:i2])}")
        print(f"           dec: {' '.join(dw[j1:j2])}")
        if chars and tag == "replace":
            for a, b in zip(rw[i1:i2], dw[j1:j2]):
                if a != b:
                    print(f"      ref {a}  vs  dec {b}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("kandam", nargs="?", type=int)
    ap.add_argument("prasna", nargs="?", type=int)
    ap.add_argument("anuvaka", nargs="?", type=int)
    ap.add_argument("--chars", action="store_true")
    ap.add_argument("--worst", type=int, default=0)
    ap.add_argument("--max-pairs", type=int, default=12)
    args = ap.parse_args()

    grantha = A.segment_grantha(GRANTHA)
    ref = A.segment_reference(REF)

    keys = []
    if args.worst:
        report = A.run(GRANTHA, REF)
        keys = [(r["kandam"], r["prasna"], r["anuvaka"])
                for r in sorted(report["anuvakas"], key=lambda r: -r["base_cer"])[:args.worst]]
    elif args.kandam is not None:
        keys = [(args.kandam, args.prasna or 1, args.anuvaka or 1)]
    else:
        keys = [k for k in sorted(grantha) if k in ref][:1]

    for key in keys:
        show(key, grantha, ref, args.chars, args.max_pairs)


if __name__ == "__main__":
    main()
