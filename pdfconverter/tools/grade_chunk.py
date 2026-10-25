"""
Grade one converted chunk against the SETHU oracle.

The converter never reads the reference; this script is the *examiner*.  It
segments the already-converted Devanagari chunk on its anuvaka markers
(`{१}`, `{१२}`, ...), drops editorial furniture (running heads, Tamil
commentary, rules, page refs `[२१]`, ornaments), and scores each anuvaka with
the same metrics as `align_reference.py`:

  * base CER / word recall      — is the letter mapping right?
  * aligned CER / exact words   — restricted to 1:1 word pairs
  * full CER / accent agreement — are the swaras right?

    python pdfconverter/tools/grade_chunk.py --chunk K1P1
    python pdfconverter/tools/grade_chunk.py --chunk K1P1 --json reports/K1P1.grade.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata

import docx
from docx.oxml.ns import qn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ganapathy_map as M
from align_reference import (  # noqa: E402
    accent_stats, aligned_stats, base_form, full_form, is_tamil, levenshtein,
    normalize, word_diff_stats,
)
from build_chunks import CHUNK_DIR

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORACLE = os.path.join(HERE, "data", "reference", "sethu_anuvakas.json")
MANIFEST_PATH = os.path.join(CHUNK_DIR, "manifest.json")

MARKER_RE = re.compile(r"\{\s*([०-९]+)\s*\}\s*$")
HEADING_KEYS = ("प्रश्नः", "काण्डे", "प्रातिशाख्य", "स्वरविधि")
RULE_RE = re.compile(r"^[\s\u2013\u2014\-_=~*·•֎]+$")


def deva_int(digits: str) -> int:
    return int("".join(str("०१२३४५६७८९".index(c)) for c in digits))


def iter_body_paragraphs(doc):
    """Body paragraphs in document order, skipping tables.

    The oracle covers the mantra text only; the tables are the anukramani
    indices and have no counterpart, so including them would only add noise.
    """
    body = doc.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            from docx.text.paragraph import Paragraph
            yield Paragraph(child, doc)


def strip_furniture(text: str) -> str:
    """Remove what the oracle does not contain, keeping the mantra text."""
    if not text.strip():
        return ""
    if RULE_RE.match(text.strip()):
        return ""
    if any(key in text for key in HEADING_KEYS):
        return ""
    if is_tamil(text):  # Pure commentary paragraph.
        return ""
    words = text.split()
    words = [w for w in words if not is_tamil(w)]
    text = " ".join(words)
    return normalize(text)


def segment(doc, prasna_hint: int) -> dict[tuple[int, int], list[str]]:
    """Return {(prasna, anuvaka): [text, ...]} for the chunk's mantras."""
    segments: dict[tuple[int, int], list[str]] = {}
    pending: list[str] = []
    nxt = 1
    prasna = prasna_hint
    for p in iter_body_paragraphs(doc):
        raw = p.text
        text = raw.strip()
        if not text:
            continue
        for num, word in ((1, "प्रथमः प्रश्नः"), (2, "द्वितीयः प्रश्नः"),
                          (3, "तृतीयः प्रश्नः"), (4, "चतुर्थः प्रश्नः"),
                          (5, "पञ्चमः प्रश्नः"), (6, "षष्ठः प्रश्नः"),
                          (7, "सप्तमः प्रश्नः"), (8, "अष्टमः प्रश्नः")):
            if word in text:
                prasna, nxt, pending = num, 1, []
                break
        else:
            m = MARKER_RE.search(text)
            if m:
                num = deva_int(m.group(1))
                if num == nxt:
                    body = strip_furniture(text[: m.start()])
                    if body:
                        pending.append(body)
                    segments[(prasna, num)] = pending
                    pending = []
                    nxt += 1
                    continue
            body = strip_furniture(raw)
            if body:
                pending.append(body)
    return segments


def load_oracle() -> dict[tuple[int, int, int], str]:
    with open(ORACLE, encoding="utf-8") as fh:
        data = json.load(fh)
    return {(a["kandam"], a["prasna"], a["anuvaka"]): a["text"]
            for a in data["anuvakas"]}


def score(ref_text: str, dec_text: str) -> tuple[dict, dict]:
    """Return (reported metrics, raw counters).

    The counters are summed across anuvakas to get chunk totals without
    re-running the O(n²) word alignment on the whole chunk.
    """
    ref_base, dec_base = base_form(ref_text), base_form(dec_text)
    ref_chars = re.sub(r"\s+", "", ref_base)
    dec_chars = re.sub(r"\s+", "", dec_base)
    edit = levenshtein(ref_chars, dec_chars)

    rw, dw, matched, _subs, ins, dele = word_diff_stats(ref_base, dec_base)
    st = aligned_stats(ref_base, dec_base)
    ref_full, dec_full = full_form(ref_text), full_form(dec_text)
    full_edit = levenshtein(re.sub(r"\s+", "", ref_full),
                            re.sub(r"\s+", "", dec_full))
    full_chars = len(re.sub(r"\s+", "", ref_full))
    a_total, a_same = accent_stats(ref_full, dec_full)
    counters = {
        "ref_words": rw, "dec_words": dw, "matched_words": matched,
        "inserted_words": ins, "deleted_words": dele,
        "ref_chars": len(ref_chars), "edit": edit,
        "aligned_words": st["words"], "aligned_chars": st["chars"],
        "aligned_edit": st["edit"], "aligned_exact": st["exact"],
        "full_chars": full_chars, "full_edit": full_edit,
        "accent_words": a_total, "accent_same": a_same,
    }
    return metrics_from(counters), counters


def metrics_from(c: dict) -> dict:
    def ratio(a: int, b: int) -> float:
        return round(a / b, 4) if b else 0.0

    return {
        "ref_words": c["ref_words"],
        "dec_words": c["dec_words"],
        "matched_words": c["matched_words"],
        "word_recall": ratio(c["matched_words"], c["ref_words"]),
        "base_cer": ratio(c["edit"], c["ref_chars"]),
        "aligned_words": c["aligned_words"],
        "aligned_cer": ratio(c["aligned_edit"], c["aligned_chars"]),
        "aligned_exact": ratio(c["aligned_exact"], c["aligned_words"]),
        "full_cer": ratio(c["full_edit"], c["full_chars"]),
        "accent_words": c["accent_words"],
        "accent_agreement": ratio(c["accent_same"], c["accent_words"]),
        "inserted_words": c["inserted_words"],
        "deleted_words": c["deleted_words"],
    }


def chunk_meta(name: str) -> dict:
    with open(MANIFEST_PATH, encoding="utf-8") as fh:
        manifest = json.load(fh)
    for chunk in manifest["chunks"]:
        if chunk["name"] == name:
            return chunk
    raise SystemExit(f"unknown chunk {name!r}")


def run(chunk: str, path: str | None = None) -> dict:
    meta = chunk_meta(chunk)
    path = path or os.path.join(CHUNK_DIR, f"{chunk}.devanagari.docx")
    if not os.path.exists(path):
        raise SystemExit(f"missing {path}; run convert_chunk.py first")
    doc = docx.Document(path)
    segments = segment(doc, meta["prasna"])
    oracle = load_oracle()

    rows = []
    totals: dict[str, int] = {}
    matched_anuvakas = 0
    for (prasna, anuvaka), parts in sorted(segments.items()):
        key = (meta["kandam"], prasna, anuvaka)
        if key not in oracle:
            continue
        matched_anuvakas += 1
        dec_text = normalize(" ".join(parts))
        ref_text = normalize(oracle[key])
        metrics, counters = score(ref_text, dec_text)
        rows.append({"anuvaka": anuvaka, **metrics})
        for name, value in counters.items():
            totals[name] = totals.get(name, 0) + value

    aggregate = metrics_from(totals) if totals else metrics_from({k: 0 for k in (
        "ref_words", "dec_words", "matched_words", "inserted_words",
        "deleted_words", "ref_chars", "edit", "aligned_words", "aligned_chars",
        "aligned_edit", "aligned_exact", "full_chars", "full_edit",
        "accent_words", "accent_same")})
    missing = [a for a in sorted({k[2] for k in oracle if k[0] == meta["kandam"]
                                  and k[1] == meta["prasna"]})
               if (meta["prasna"], a) not in segments]

    report = {
        "chunk": chunk,
        "decoder_version": M.DECODER_VERSION,
        "document": os.path.basename(path),
        "kandam": meta["kandam"],
        "prasna": meta["prasna"],
        "segments_found": len(segments),
        "anuvakas_graded": matched_anuvakas,
        "missing_anuvakas": missing,
        "summary": aggregate,
        "anuvakas": rows,
    }
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chunk", required=True)
    ap.add_argument("--json", default=None)
    ap.add_argument("--path", help="explicit .docx (default: data/chunks/<chunk>.devanagari.docx)")
    args = ap.parse_args()

    report = run(args.chunk, args.path)
    s = report["summary"]
    if not report["anuvakas_graded"]:
        print(f"{report['chunk']}: no SETHU text for this chunk "
              f"(oracle covers Kandam 1 Prasnas 1-4); nothing to grade")
        return
    print(f"{report['chunk']}: {report['anuvakas_graded']} anuvakas graded "
          f"of {report['anuvakas_graded'] + len(report['missing_anuvakas'])}")
    if report["missing_anuvakas"]:
        print(f"  missing anuvakas: {report['missing_anuvakas']}")
    print(f"  word recall     : {s['matched_words']}/{s['ref_words']} = {s['word_recall']:.2%}")
    print(f"  base-text CER   : {s['base_cer']:.2%}")
    print(f"  aligned CER     : {s['aligned_cer']:.2%}  ({s['aligned_words']} words 1:1)")
    print(f"  exact words     : {s['aligned_exact']:.2%}")
    print(f"  full-text CER   : {s['full_cer']:.2%}")
    print(f"  accent agreement: {s['accent_agreement']:.2%}")
    print("\nworst anuvakas (base CER):")
    for row in sorted(report["anuvakas"], key=lambda r: -r["base_cer"])[:8]:
        print(f"  A{row['anuvaka']:>2}  CER={row['base_cer']:.1%}  "
              f"recall={row['word_recall']:.0%}  exact={row['aligned_exact']:.0%}")

    out = args.json or os.path.join(HERE, "reports", f"{args.chunk}.grade.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
