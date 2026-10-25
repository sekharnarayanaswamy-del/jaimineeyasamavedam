"""
Induce the Ganapathy byte map from the SETHU ground truth.

Unlike `learn_map.py` (which only shows proposals), this tool produces a
per-byte **vote table**: for every grantha source unit it reports which
Devanagari characters the reference actually aligns to, how often, and with
what confidence.  That turns "I think `J` is त्व" into "J -> भ 312/318".

Method
------
1. Split both documents into anuvakas and align *tokens* with a DP that
   allows 1:1, 1:2 and 2:1 (grantha tokens are sometimes split or merged
   differently from the reference words).
2. For each accepted pair, decode the token into `(source_span, output)`
   units, strip swaras, and align the decoded characters to the reference
   word with difflib.
3. Equal (and same-length replace) blocks cast a vote for `source -> char`.

    python pdfconverter/tools/induce_map.py
    python pdfconverter/tools/induce_map.py --min-pairs 3 --csv reports/induced.csv
"""
from __future__ import annotations

import argparse
import collections
import csv
import difflib
import json
import os
import sys

import docx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_reference as A
from ganapathy_map import (
    CONSONANTS, COMPOUNDS, DIGITS, INDEPENDENT_VOWELS, MATRAS, MULTI,
    PUNCTUATION, SUBSCRIPTS, SWARAS, decode_units, is_tamil, strip_accents,
)


# --------------------------------------------------------------------------
# 1. Token alignment
# --------------------------------------------------------------------------

_sim = A.similarity
align_tokens = A.align_tokens


# --------------------------------------------------------------------------
# 2. Vote collection
# --------------------------------------------------------------------------

def _spans(units):
    """[(source, output, start, end), ...] over the accent-stripped output."""
    spans, pos = [], 0
    for src, out in units:
        out = strip_accents(out)
        if not out:
            continue
        spans.append((src, out, pos, pos + len(out)))
        pos += len(out)
    return spans, pos


def collect(min_ratio: float = 0.5):
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    grantha = A.segment_grantha(os.path.join(here, "data", "input", "1st Paadam Final-Grantha-Cleaned.docx"))
    ref = A.segment_reference(os.path.join(here, "data", "input", "THAITHIREEYA SAMHITHA 1 (SETHU) प्रथम पादः .docx"))

    votes: collections.defaultdict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    words: collections.defaultdict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    n_pairs = 0

    for key in (k for k in grantha if k in ref):
        toks = [w for w in " ".join(grantha[key]).replace("֍", " ").split()
                if not is_tamil(w)]
        refw = [w for w in A.base_form(A.normalize(ref[key])).split() if w]
        if not toks or not refw:
            continue
        dec = [A.base_form("".join(o for _, o in decode_units(t))) for t in toks]
        for ti, wj in align_tokens(dec, refw):
            tok = "".join(toks[k] for k in ti)
            word = "".join(refw[k] for k in wj)
            spans, _ = _spans(decode_units(tok))
            out = "".join(o for _, o, _, _ in spans)
            ref_chars = strip_accents(word)
            if not out or not ref_chars:
                continue
            ratio = _sim(out, ref_chars)
            if ratio < min_ratio:
                continue
            n_pairs += 1
            sm = difflib.SequenceMatcher(None, out, ref_chars, autojunk=False)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag != "equal":
                    continue
                # only vote for units whose whole output lies inside the match
                for src, unit_out, s, e in spans:
                    if s >= i1 and e <= i2:
                        target = ref_chars[j1 + (s - i1): j1 + (e - i1)]
                        if target:
                            votes[src][target] += 1
            if ratio > 0.75:
                words[tok][word] += 1

    return votes, words, n_pairs


# --------------------------------------------------------------------------
# 3. Report
# --------------------------------------------------------------------------

def base_table() -> dict[str, str]:
    table = {}
    for d in (CONSONANTS, SUBSCRIPTS, INDEPENDENT_VOWELS, MATRAS, DIGITS,
              PUNCTUATION, SWARAS):
        table.update(d)
    for src, tgt in MULTI:
        table[src] = tgt
    table.update(COMPOUNDS)
    return table


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-votes", type=int, default=5)
    ap.add_argument("--min-ratio", type=float, default=0.5)
    ap.add_argument("--csv", default=None)
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    votes, words, n_pairs = collect(args.min_ratio)
    current = base_table()

    rows = []
    for src, counter in votes.items():
        total = sum(counter.values())
        if total < args.min_votes:
            continue
        target, n = counter.most_common(1)[0]
        rows.append({
            "source": src,
            "current": current.get(src, ""),
            "induced": target,
            "votes": n,
            "total": total,
            "confidence": round(n / total, 3),
            "rivals": "; ".join(f"{t}:{c}" for t, c in counter.most_common(4)[1:]),
        })

    rows.sort(key=lambda r: (r["current"] == r["induced"], -r["total"]))

    print(f"{n_pairs} aligned token pairs, {len(votes)} distinct source units\n")
    print(f"{'src':<8} {'cur':<8} {'induced':<8} {'votes':>6} {'conf':>6}  rivals")
    print("-" * 78)
    for r in rows:
        flag = " " if r["current"] == r["induced"] else "!"
        print(f"{flag}{r['source']!r:<7} {r['current']!r:<8} {r['induced']!r:<8} "
              f"{r['votes']:>4}/{r['total']:<4} {r['confidence']:>5}  {r['rivals'][:34]}")

    if args.csv:
        with open(args.csv, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nwrote {args.csv}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"rows": rows,
                       "words": [{"source": k, "target": t, "votes": n}
                                 for k, c in words.items()
                                 for t, n in c.most_common(1)]},
                      fh, ensure_ascii=False, indent=2)
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
