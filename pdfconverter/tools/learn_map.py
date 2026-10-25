"""
Backwards-compatible entry point for map learning.

The real work now lives in `induce_map.py`: it aligns tokens with a DP (so
footnotes and split words do not poison the votes), attributes every output
character to its exact source byte, and reports per-byte confidence.

    python pdfconverter/tools/learn_map.py
    python pdfconverter/tools/learn_map.py --json reports/map_proposals.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import induce_map


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default=None)
    ap.add_argument("--ref", default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--min-votes", type=int, default=2)
    args = ap.parse_args()

    votes, words, n_pairs = induce_map.collect()
    rows = []
    for src, counter in votes.items():
        total = sum(counter.values())
        if total < args.min_votes:
            continue
        target, n = counter.most_common(1)[0]
        rows.append({"source": src, "target": target, "votes": n,
                     "total": total, "confidence": round(n / total, 3)})
    rows.sort(key=lambda r: -r["total"])

    print(f"{n_pairs} aligned pairs, {len(rows)} source units\n")
    for r in rows[:40]:
        print(f"  {r['votes']:>4}/{r['total']:<4} {r['source']!r:<8} -> {r['target']!r}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"units": rows,
                       "words": [{"source": k, "target": t, "votes": n}
                                 for k, c in words.items()
                                 for t, n in c.most_common(1)]},
                      fh, ensure_ascii=False, indent=2)
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
