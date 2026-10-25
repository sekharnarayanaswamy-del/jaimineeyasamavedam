"""
Per-byte evidence: what does the reference say where this byte decoded to X?

For every aligned token pair, each decoder unit is located in the decoded
string; if the diff opcode covering that unit is not `equal`, the pair
(unit output, reference substring) is counted under the unit's source byte.
The top pairs per byte show exactly how the mapping is wrong, and the
confidence tells you whether it is systematic.

    python pdfconverter/tools/unit_evidence.py X { ! # Ÿ ?
    python pdfconverter/tools/unit_evidence.py --all --top 3
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

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def units_of(token: str):
    spans, pos = [], 0
    for src, out in M.decode_units(token):
        out = M.strip_accents(out)
        if not out:
            continue
        spans.append((src, pos, pos + len(out), out))
        pos += len(out)
    text = "".join(s[3] for s in spans)
    return spans, text


def collect(bytes_of_interest=None, min_ratio=0.35):
    grantha = A.segment_grantha(os.path.join(
        HERE, "data", "input", "1st Paadam Final-Grantha-Cleaned.docx"))
    ref = A.segment_reference(os.path.join(
        HERE, "data", "input", "THAITHIREEYA SAMHITHA 1 (SETHU) प्रथम पादः .docx"))
    pairs = collections.Counter()
    examples = collections.defaultdict(list)
    totals = collections.Counter()
    for key in (k for k in grantha if k in ref):
        toks = [w for w in " ".join(grantha[key]).replace("֍", " ").split()
                if not A.is_tamil(w)]
        refw = [w for w in A.base_form(A.normalize(ref[key])).split() if w]
        dec = [A.base_form(M.decode_text(t)) for t in toks]
        for ti, wj in align_tokens(dec, refw):
            if len(ti) != 1 or len(wj) != 1:
                continue
            tok, word = toks[ti[0]], refw[wj[0]]
            spans, text = units_of(tok)
            if not text or not word:
                continue
            if difflib.SequenceMatcher(None, text, word, autojunk=False).ratio() < min_ratio:
                continue
            sm = difflib.SequenceMatcher(None, text, word, autojunk=False)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag == "equal":
                    continue
                hit = [s for s in spans if s[1] < max(i2, i1 + 1) and s[2] > i1]
                for src, a, b, out in hit:
                    if bytes_of_interest and src not in bytes_of_interest:
                        continue
                    if len(src) > 1:
                        continue
                    pair = (out, word[j1:j2])
                    totals[src] += 1
                    if tag == "replace" and (i2 - i1) >= 3 and (j2 - j1) >= 3:
                        continue  # window too wide to be informative
                    pairs[(src,) + pair] += 1
                    if len(examples[(src,) + pair]) < 3:
                        examples[(src,) + pair].append((tok, text, word))
    return pairs, examples, totals


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bytes", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--min-count", type=int, default=3)
    args = ap.parse_args()

    wanted = None
    if args.bytes and not args.all:
        wanted = {b if len(b) == 1 else b.encode().decode("unicode_escape") for b in args.bytes}

    pairs, examples, totals = collect(wanted)
    if wanted is None:
        order = [b for b, _ in totals.most_common()]
    else:
        order = [b for b in wanted if totals[b]]

    for b in order:
        rows = [(k, n) for k, n in pairs.items() if k[0] == b]
        rows.sort(key=lambda r: -r[1])
        shown = [r for r in rows if r[1] >= args.min_count][:args.top]
        if not shown:
            continue
        print(f"\n=== {b!r}  ({totals[b]} misaligned units)")
        for (src, dec, ref), n in shown:
            print(f"   {n:>4}x  we say {dec!r}  ref {ref!r}")
            for tok, text, word in examples[(src, dec, ref)][:2]:
                print(f"         {tok:<32} -> {text:<24} ref {word}")
    print()


if __name__ == "__main__":
    main()
