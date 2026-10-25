"""
Inventory every Grantha code point in the source document.

Answers "what is left to map, and how much does it matter?" — for each code
point it reports frequency, cumulative coverage, the current target (if any),
and the surrounding context so an unknown byte can be identified from a few
examples instead of a full document pass.

    python pdfconverter/tools/codepoint_inventory.py
    python pdfconverter/tools/codepoint_inventory.py --csv reports/codepoints.csv
"""
from __future__ import annotations

import argparse
import collections
import csv
import os
import sys
import unicodedata

import docx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ganapathy_map import (  # noqa: E402
    COMPOUNDS, CONSONANTS, DIGITS, INDEPENDENT_VOWELS, MATRAS, MULTI,
    PUNCTUATION, SUBSCRIPTS, SWARAS, is_tamil,
)


def mapping_table() -> dict[str, str]:
    table: dict[str, str] = {}
    for d in (CONSONANTS, SUBSCRIPTS, INDEPENDENT_VOWELS, MATRAS, DIGITS,
              PUNCTUATION, SWARAS):
        table.update(d)
    for src, tgt in MULTI:
        table[src] = tgt
    return table


def iter_texts(path: str):
    doc = docx.Document(path)
    for p in doc.paragraphs:
        yield p.text
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    yield p.text


def inventory(path: str):
    counts: collections.Counter[str] = collections.Counter()
    contexts: dict[str, list[str]] = collections.defaultdict(list)
    for text in iter_texts(path):
        if not text or is_tamil(text):
            continue
        for i, ch in enumerate(text):
            if ch.isspace():
                continue
            counts[ch] += 1
            if len(contexts[ch]) < 3:
                lo, hi = max(0, i - 3), min(len(text), i + 4)
                contexts[ch].append(text[lo:hi].replace(ch, f"[{ch}]"))
    return counts, contexts


def main() -> None:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default=os.path.join(
        here, "data", "input", "1st Paadam Final-Grantha-Cleaned.docx"))
    ap.add_argument("--csv", default=None)
    ap.add_argument("--all", action="store_true", help="include mapped code points")
    args = ap.parse_args()

    table = mapping_table()
    compound_heads = {k[0] for k in COMPOUNDS}
    counts, contexts = inventory(args.input)
    total = sum(counts.values())

    rows = []
    cumulative = 0
    for ch, n in counts.most_common():
        cumulative += n
        target = table.get(ch)
        rows.append({
            "codepoint": f"U+{ord(ch):04X}",
            "char": ch,
            "name": unicodedata.name(ch, "?"),
            "count": n,
            "share": round(n / total, 5),
            "cumulative": round(cumulative / total, 5),
            "mapped": bool(target),
            "target": target or "",
            "compound_head": ch in compound_heads,
            "contexts": " | ".join(contexts[ch]),
        })

    shown = [r for r in rows if args.all or not r["mapped"]]
    print(f"{len(rows)} distinct code points, {total} occurrences")
    unmapped = [r for r in rows if not r["mapped"]]
    print(f"{len(unmapped)} unmapped ({sum(r['count'] for r in unmapped)} occurrences, "
          f"{sum(r['count'] for r in unmapped) / total:.2%} of corpus)\n")
    print(f"{'cp':<8} {'char':<6} {'count':>7} {'cum':>7}  target  contexts")
    print("-" * 96)
    for r in shown[:60]:
        print(f"{r['codepoint']:<8} {r['char']!r:<6} {r['count']:>7} "
              f"{r['cumulative']:>6.1%}  {r['target']!r:<8} {r['contexts'][:52]}")

    if args.csv:
        with open(args.csv, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nwrote {args.csv}")


if __name__ == "__main__":
    main()
