"""
Attribute base-text errors back to the Grantha source byte that caused them.

The decoder already carries provenance (`decode_units` returns one
(source_bytes, output) pair per source unit).  This tool walks aligned
token pairs, diffs the *base* (accent-free) text, and charges every
insert / delete / replace to the source bytes covering that span.

Output is a ranked table: "which byte is costing me the most characters,
and what does it look like in context?"  That is the only reliable way to
pick the next map fix instead of guessing.

    python pdfconverter/tools/error_attribution.py
    python pdfconverter/tools/error_attribution.py --top 25 --examples 4
"""
from __future__ import annotations

import argparse
import collections
import difflib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_reference as A
import ganapathy_map as M
from induce_map import align_tokens


def base_spans(token: str) -> tuple[list[tuple[str, int, int]], str]:
    """[(source, start, end)] plus the accent-free decoded text of a token."""
    spans, pos = [], 0
    for src, out in M.decode_units(token):
        out = M.strip_accents(out)
        if not out:
            continue
        spans.append((src, pos, pos + len(out)))
        pos += len(out)
    return spans, "".join(
        M.strip_accents(out) for _, out in M.decode_units(token)
    )


def collect(min_ratio: float = 0.3):
    grantha = A.segment_grantha(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "data", "input", "1st Paadam Final-Grantha-Cleaned.docx"))
    ref = A.segment_reference(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "data", "input", "THAITHIREEYA SAMHITHA 1 (SETHU) प्रथम पादः .docx"))

    errors = collections.Counter()
    examples: dict[tuple, list[tuple]] = collections.defaultdict(list)
    for key in (k for k in grantha if k in ref):
        toks = [w for w in " ".join(grantha[key]).replace("֍", " ").split()
                if not A.is_tamil(w)]
        refw = [w for w in A.base_form(A.normalize(ref[key])).split() if w]
        dec = [A.base_form(M.decode_text(t)) for t in toks]
        for ti, wj in align_tokens(dec, refw):
            if len(ti) != 1 or len(wj) != 1:
                continue
            tok, word = toks[ti[0]], refw[wj[0]]
            spans, out = base_spans(tok)
            if not out or not word:
                continue
            if difflib.SequenceMatcher(None, out, word, autojunk=False).ratio() < min_ratio:
                continue
            sm = difflib.SequenceMatcher(None, out, word, autojunk=False)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag == "equal":
                    continue
                srcs = tuple(sorted({s for s, a, b in spans
                                     if a < max(i2, i1 + 1) and b > i1}))
                key_ = (srcs, tag, word[j1:j2], out[i1:i2])
                errors[key_] += max(i2 - i1, j2 - j1)
                if len(examples[key_]) < 3:
                    examples[key_].append((tok, out, word))
    return errors, examples


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--examples", type=int, default=3)
    ap.add_argument("--min-ratio", type=float, default=0.3)
    args = ap.parse_args()

    errors, examples = collect(args.min_ratio)
    total = sum(errors.values())
    print(f"{total} charged characters in {len(errors)} classes\n")

    for key, cost in errors.most_common(args.top):
        srcs, tag, ref_txt, dec_txt = key
        label = "".join(srcs) if srcs else "<none>"
        print(f"{cost:>5}  src={label!r:<12} {tag:<8} "
              f"ref {ref_txt!r} vs dec {dec_txt!r}")
        for tok, out, word in examples[key][:args.examples]:
            print(f"        {tok:<30} -> {out:<26} ref {word}")
    print()


if __name__ == "__main__":
    main()
