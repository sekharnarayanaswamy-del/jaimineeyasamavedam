"""
Golden-score gate for the Grantha decoder.

Runs the reference alignment on Kandam 1 Prasnas 1-4 and compares the
headline numbers against `pdfconverter/tests/golden_scores.json`.  Any
regression beyond the tolerance fails, so a map edit can never quietly make
the output worse.

    python pdfconverter/tools/check_scores.py --update   # re-baseline
    python pdfconverter/tools/check_scores.py            # gate (exit 1 on regression)
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_reference as A
import ganapathy_map as M

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = os.path.join(HERE, "tests", "golden_scores.json")

# higher is better / lower is better
METRICS = {
    "word_recall": "higher",
    "base_cer": "lower",
    "aligned_cer": "lower",
    "aligned_exact": "higher",
    "full_cer": "lower",
    "accent_agreement": "higher",
}
TOLERANCE = 0.002


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--update", action="store_true", help="write the current scores as the new baseline")
    ap.add_argument("--tolerance", type=float, default=TOLERANCE)
    ap.add_argument("--note", default=None,
                    help="reason for an intentional divergence, stored with the baseline")
    args = ap.parse_args()

    report = A.run(
        os.path.join(HERE, "data", "input", "1st Paadam Final-Grantha-Cleaned.docx"),
        os.path.join(HERE, "data", "input", "THAITHIREEYA SAMHITHA 1 (SETHU) प्रथम पादः .docx"),
    )
    current = {k: report["summary"][k] for k in METRICS}
    payload = {"decoder_version": M.DECODER_VERSION, "scores": current}
    if args.note:
        payload["note"] = args.note

    if args.update:
        if not args.note and os.path.exists(GOLDEN):
            with open(GOLDEN, encoding="utf-8") as fh:
                old_note = json.load(fh).get("note")
            if old_note:
                payload["note"] = old_note
        os.makedirs(os.path.dirname(GOLDEN), exist_ok=True)
        with open(GOLDEN, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print(f"wrote {GOLDEN}")
        for k, v in current.items():
            print(f"  {k:<18} {v:.4f}")
        return

    if not os.path.exists(GOLDEN):
        raise SystemExit(f"missing {GOLDEN}; run with --update first")
    with open(GOLDEN, encoding="utf-8") as fh:
        payload = json.load(fh)
    golden = payload["scores"]

    failed = []
    print(f"decoder {M.DECODER_VERSION}")
    if payload.get("note"):
        print(f"note: {payload['note']}")
    for key, direction in METRICS.items():
        want, got = golden[key], current[key]
        delta = got - want
        worse = (delta < -args.tolerance) if direction == "higher" else (delta > args.tolerance)
        flag = "FAIL" if worse else ("ok  " if abs(delta) <= args.tolerance else "BETTER")
        print(f"  {key:<18} {got:.4f}  (baseline {want:.4f}, {delta:+.4f})  {flag}")
        if worse:
            failed.append(key)

    if failed:
        raise SystemExit(f"regression: {', '.join(failed)}")
    print("no regression")


if __name__ == "__main__":
    main()
