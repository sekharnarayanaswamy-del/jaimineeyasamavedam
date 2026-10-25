"""
Alignment + accuracy harness: decoded Grantha vs the SETHU reference text.

The reference docx (`THAITHIREEYA SAMHITHA 1 (SETHU) ... .docx`) contains one
paragraph per anuvaka for Kandam 1 Prasnas 1-4, each ending with a Devanagari
`{N}` marker.  The Grantha source contains many paragraphs per anuvaka (one per
typeset line / page fragment), each ending with a Ganapathy `{N}` marker.

This module segments both documents on those markers, decodes the Grantha text,
and reports:

  * base-text character error rate (swaras stripped) - "is the letter mapping right?"
  * base-text word error rate                          - "are the words right?"
  * recall of reference words                          - robust to inline Tamil/Grantha footnotes
  * the most frequent character confusions              - "what should I fix in the map?"

Usage
-----
    python pdfconverter/tools/align_reference.py
    python pdfconverter/tools/align_reference.py --input <grantha.docx> --json report.json
"""
from __future__ import annotations

import argparse
import collections
import difflib
import importlib
import json
import os
import re
import sys

import docx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ganapathy_map import GRANTHA_DIGITS, decode_text, is_tamil, strip_accents  # noqa: E402


def load_decoder(spec: str):
    """Load a decoder callable from 'module:function' (module on sys.path)."""
    if ":" not in spec:
        raise SystemExit(f"--decoder must be 'module:function', got {spec!r}")
    mod_name, func_name = spec.split(":", 1)
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    mod = importlib.import_module(mod_name)
    return getattr(mod, func_name)

DEVANAGARI_DIGITS = {c: str(i) for i, c in enumerate("०१२३४५६७८९")}

PRASNA_PATTERNS = [
    (r"h\fk,", 1),      # प्रथम
    (r"~]D[K,", 2),     # द्वितीय
    (r"D4D[K,", 3),     # तृतीय
    (r"ID6f9,", 4),     # चतुर्थ
    (r"hVk,", 5),       # पञ्चम
    (r"cc¢,", 6),       # षष्ठ
    (r"vh¦k,", 7),      # सप्तम
    (r"q%k,", 8),       # अष्टम
]
KANDAM_PATTERNS = [
    (r"h\fky31d", 1),   # प्रथमकाण्ड
    (r"~]D[Ky31d", 2),  # द्वितीयकाण्ड
]

ORNAMENT = "֎"
GRANTHA_MARKER = re.compile(r"\{\s*([æçèéêëìíîï]+)\s*\}\s*$")


def _num(chars: str, table: dict[str, str]) -> int:
    return int("".join(table.get(c, "") for c in chars))


def segment_grantha(path: str) -> dict[tuple[int, int, int], list[str]]:
    """Return {(kandam, prasna, anuvaka): [paragraph texts]} for mantras."""
    doc = docx.Document(path)
    kandam, prasna, nxt = 1, 1, 1
    pending: list[str] = []
    segments: dict[tuple[int, int, int], list[str]] = collections.OrderedDict()
    for p in doc.paragraphs:
        raw = p.text
        text = raw.strip()
        if not text:
            continue
        for pat, k in KANDAM_PATTERNS:
            if pat in text:
                kandam = k
        hit = next((k for pat, k in PRASNA_PATTERNS if pat in text), None)
        if hit is not None:
            prasna, nxt, pending = hit, 1, []
            continue

        m = GRANTHA_MARKER.search(text)
        if m:
            try:
                num = _num(m.group(1), GRANTHA_DIGITS)
            except ValueError:
                num = -1
            if num == nxt:  # ignores footnote/page numbers
                pending.append(raw[: m.start()])
                segments[(kandam, prasna, num)] = pending
                pending = []
                nxt += 1
                continue
        pending.append(raw)
    return segments


def segment_reference(path: str) -> dict[tuple[int, int, int], str]:
    doc = docx.Document(path)
    prasna = 1
    ref: dict[tuple[int, int, int], str] = {}
    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        if "प्रथमः प्रश्नः" in text:
            prasna = 1
            continue
        if "द्वितीयः प्रश्नः" in text:
            prasna = 2
            continue
        if "तृतीयः प्रश्नः" in text:
            prasna = 3
            continue
        if "चतुर्थः प्रश्नः" in text:
            prasna = 4
            continue
        m = re.search(r"\{\s*([०-९]+)\s*\}\s*$", text)
        if m:
            ref[(1, prasna, _num(m.group(1), DEVANAGARI_DIGITS))] = text[: m.start()].strip()
    return ref


def normalize(text: str) -> str:
    text = text.replace(ORNAMENT, " ")
    text = re.sub(r"\[[०-९0-9æçèéêëìíîï]+\]", " ", text)  # footnote refs
    text = re.sub(r"[ \t\u00a0]+", " ", text)
    return text.strip()


# Punctuation is graded separately from the letter mapping: the source uses
# `.`/`-` as layout separators as well as dandas, so counting them here would
# drown the signal we care about.
_PUNCT_RE = re.compile(r"[।॥.,;:!?'\"()\[\]{}<>–—\u200c\u200d\u00ad]")


def base_form(text: str) -> str:
    """Letters only: no swaras, no punctuation, single spaces."""
    text = strip_accents(text)
    text = _PUNCT_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def levenshtein_dp(a: str, b: str) -> int:
    """Classic O(len(a)*len(b)) edit distance (reference implementation)."""
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def levenshtein(a: str, b: str) -> int:
    """Bit-parallel (Myers) edit distance — ~100x faster than the DP version.

    The grader calls this on every aligned word and on whole anuvakas, so the
    constant matters: map tuning evaluates ~100 candidates per round.
    """
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if len(a) > len(b):
        a, b = b, a
    m = len(a)
    mask = (1 << m) - 1
    last = 1 << (m - 1)
    peq: dict[str, int] = {}
    for i, ch in enumerate(a):
        peq[ch] = peq.get(ch, 0) | (1 << i)
    pv, mv, score = mask, 0, m
    for ch in b:
        eq = peq.get(ch, 0)
        xv = eq | mv
        xh = (((eq & pv) + pv) ^ pv) | eq
        ph = mv | ~(xh | pv)
        mh = pv & xh
        if ph & last:
            score += 1
        elif mh & last:
            score -= 1
        ph = ((ph << 1) | 1) & mask
        mh = (mh << 1) & mask
        pv = (mh | ~(xv | ph)) & mask
        mv = ph & xv
    return score


def word_diff_stats(ref: str, dec: str):
    rw, dw = ref.split(), dec.split()
    sm = difflib.SequenceMatcher(None, rw, dw, autojunk=False)
    matched = sum(b.size for b in sm.get_matching_blocks())
    subs, ins, dele = [], 0, 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "replace":
            a, b = rw[i1:i2], dw[j1:j2]
            for k in range(min(len(a), len(b))):
                subs.append((b[k], a[k]))  # (decoded, reference)
            ins += max(0, len(b) - len(a))
            dele += max(0, len(a) - len(b))
        elif tag == "insert":
            ins += j2 - j1
        elif tag == "delete":
            dele += i2 - i1
    return len(rw), len(dw), matched, subs, ins, dele


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def align_tokens(tokens: list[str], words: list[str], gap: float = -0.45):
    """DP align grantha tokens to reference words.

    Allows 1:1, 2:1 and 1:2 blocks because the source sometimes splits a word
    across a line break and sometimes merges two words.  Returns
    ``[(token_indices, word_indices), ...]``.
    """
    nt, nw = len(tokens), len(words)
    NEG = float("-inf")
    score = [[NEG] * (nw + 1) for _ in range(nt + 1)]
    back = [[None] * (nw + 1) for _ in range(nt + 1)]
    score[0][0] = 0.0
    cache: dict[tuple[int, int, int, int], float] = {}

    def sim(i1, i2, j1, j2):
        key = (i1, i2, j1, j2)
        if key not in cache:
            cache[key] = similarity("".join(tokens[i1:i2]), "".join(words[j1:j2]))
        return cache[key]

    for i in range(nt + 1):
        for j in range(nw + 1):
            cur = score[i][j]
            if cur == NEG:
                continue
            moves = []
            if i < nt and j < nw:
                moves.append((cur + 2 * sim(i, i + 1, j, j + 1), ("m", i, j), (i + 1, j + 1)))
            if i < nt:
                moves.append((cur + gap, ("t", i, j), (i + 1, j)))
            if j < nw:
                moves.append((cur + gap, ("w", i, j), (i, j + 1)))
            if i + 1 < nt and j < nw:
                moves.append((cur + 1.6 * sim(i, i + 2, j, j + 1), ("mm", i, j), (i + 2, j + 1)))
            if i < nt and j + 1 < nw:
                moves.append((cur + 1.6 * sim(i, i + 1, j, j + 2), ("ww", i, j), (i + 1, j + 2)))
            for value, mark, (ni, nj) in moves:
                if value > score[ni][nj]:
                    score[ni][nj] = value
                    back[ni][nj] = mark

    pairs, i, j = [], nt, nw
    while i > 0 or j > 0:
        step = back[i][j]
        if step is None:
            break
        kind, pi, pj = step
        if kind == "m":
            pairs.append(([pi], [pj]))
        elif kind == "mm":
            pairs.append(([pi, pi + 1], [pj]))
        elif kind == "ww":
            pairs.append(([pi], [pj, pj + 1]))
        i, j = pi, pj
    pairs.reverse()
    return pairs


def aligned_stats(ref_base: str, dec_base: str):
    """Word-aligned comparison statistics.

    Returns a dict with:
      * ``words`` / ``chars`` / ``edit`` — base-text (accent-free) accuracy
        measured only where a decoded word matches a reference word.  Footnotes
        and page numbers in the source have no counterpart in the oracle, so
        counting them would hide real mapping mistakes; `word_recall` still
        penalises dropping them.
      * ``exact`` — aligned pairs that match exactly (no letter error),
      * ``accent_same`` — aligned pairs whose swara sequence agrees, which is
        the only signal we have for accent placement (the letters may differ).
    """
    rw, dw = ref_base.split(), dec_base.split()
    ref_chars = edit = words = exact = 0
    for ti, wj in align_tokens(dw, rw):
        if len(ti) != 1 or len(wj) != 1:
            continue
        a, b = rw[wj[0]], dw[ti[0]]
        ref_chars += len(a)
        d = levenshtein(a, b)
        edit += d
        words += 1
        if d == 0:
            exact += 1
    return {"words": words, "chars": ref_chars, "edit": edit, "exact": exact}


_ACCENT_SET = set("\u0951\u0952\u1CDA")


def _accents(word: str) -> str:
    return "".join(ch for ch in word if ch in _ACCENT_SET)


def full_form(text: str) -> str:
    """Letters and swaras, punctuation and PUA glyph differences removed."""
    text = text.replace("\uE004", "\uA8E3").replace("\uE003", "\uA8E3")
    text = text.replace("\uE005", "\uA8E3").replace("\uE006", "\uA8E3")
    text = _PUNCT_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def accent_stats(ref_full: str, dec_full: str):
    """(aligned pairs, pairs whose swara sequence matches)."""
    rw, dw = ref_full.split(), dec_full.split()
    total = same = 0
    for ti, wj in align_tokens(dw, rw):
        if len(ti) != 1 or len(wj) != 1:
            continue
        total += 1
        if _accents(rw[wj[0]]) == _accents(dw[ti[0]]):
            same += 1
    return total, same


def char_confusions(subs, limit=40):
    counter: collections.Counter[tuple[str, str]] = collections.Counter()
    for dec_word, ref_word in subs:
        sm = difflib.SequenceMatcher(None, ref_word, dec_word, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "replace":
                counter[(ref_word[i1:i2], dec_word[j1:j2])] += 1
    return counter.most_common(limit)


def run(input_path: str, ref_path: str, decoder=decode_text) -> dict:
    grantha = segment_grantha(input_path)
    ref = segment_reference(ref_path)

    keys = [k for k in grantha if k in ref]
    report = {
        "input": input_path,
        "reference": ref_path,
        "grantha_segments": len(grantha),
        "reference_segments": len(ref),
        "compared_segments": len(keys),
        "missing_reference": [list(k) for k in grantha if k not in ref][:20],
        "missing_grantha": [list(k) for k in ref if k not in grantha][:20],
        "anuvakas": [],
    }

    ref_word_total = dec_word_total = matched_total = 0
    ref_char_total = char_edit_total = 0
    aligned_words = aligned_chars = aligned_edit = aligned_exact = 0
    full_edit = full_chars = accent_words = accent_same = 0
    all_subs = []
    for key in keys:
        ref_text = normalize(ref[key])
        dec_raw = " ".join(grantha[key])
        dec_text = normalize(decoder(dec_raw))
        if is_tamil(dec_text):
            dec_text = " ".join(w for w in dec_text.split() if not is_tamil(w))

        ref_base, dec_base = base_form(ref_text), base_form(dec_text)
        ref_chars = re.sub(r"\s+", "", ref_base)
        dec_chars = re.sub(r"\s+", "", dec_base)
        edit = levenshtein(ref_chars, dec_chars)

        rw, dw, matched, subs, ins, dele = word_diff_stats(ref_base, dec_base)
        st = aligned_stats(ref_base, dec_base)
        aligned_words += st["words"]
        aligned_chars += st["chars"]
        aligned_edit += st["edit"]
        aligned_exact += st["exact"]
        ref_full, dec_full = full_form(ref_text), full_form(dec_text)
        full_edit += levenshtein(re.sub(r"\s+", "", ref_full), re.sub(r"\s+", "", dec_full))
        full_chars += len(re.sub(r"\s+", "", ref_full))
        t, s = accent_stats(ref_full, dec_full)
        accent_words += t
        accent_same += s
        ref_word_total += rw
        dec_word_total += dw
        matched_total += matched
        ref_char_total += len(ref_chars)
        char_edit_total += edit
        all_subs.extend(subs)

        report["anuvakas"].append(
            {
                "kandam": key[0],
                "prasna": key[1],
                "anuvaka": key[2],
                "ref_words": rw,
                "dec_words": dw,
                "matched_words": matched,
                "word_recall": round(matched / rw, 4) if rw else 0.0,
                "base_cer": round(edit / len(ref_chars), 4) if ref_chars else 0.0,
                "inserted_words": ins,
                "deleted_words": dele,
            }
        )

    report["summary"] = {
        "word_recall": round(matched_total / ref_word_total, 4) if ref_word_total else 0.0,
        "word_precision": round(matched_total / dec_word_total, 4) if dec_word_total else 0.0,
        "base_cer": round(char_edit_total / ref_char_total, 4) if ref_char_total else 0.0,
        "aligned_words": aligned_words,
        "aligned_cer": round(aligned_edit / aligned_chars, 4) if aligned_chars else 0.0,
        "aligned_exact": round(aligned_exact / aligned_words, 4) if aligned_words else 0.0,
        "full_cer": round(full_edit / full_chars, 4) if full_chars else 0.0,
        "accent_agreement": round(accent_same / accent_words, 4) if accent_words else 0.0,
        "ref_words": ref_word_total,
        "dec_words": dec_word_total,
        "matched_words": matched_total,
    }
    report["top_confusions"] = [
        {"reference": r, "decoded": d, "count": c} for (r, d), c in char_confusions(all_subs)
    ]
    return report


def main() -> None:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default=os.path.join(here, "data", "input", "1st Paadam Final-Grantha-Cleaned.docx"))
    ap.add_argument("--ref", default=os.path.join(here, "data", "input", "THAITHIREEYA SAMHITHA 1 (SETHU) प्रथम पादः .docx"))
    ap.add_argument("--json", default=None)
    ap.add_argument("--decoder", default="ganapathy_map:decode_text",
                    help="module:function used to decode Grantha (default: ganapathy_map:decode_text)")
    args = ap.parse_args()

    report = run(args.input, args.ref, load_decoder(args.decoder))
    s = report["summary"]
    print(f"segments: grantha={report['grantha_segments']} reference={report['reference_segments']} compared={report['compared_segments']}")
    if report["missing_reference"]:
        print(f"  grantha segments with no reference: {report['missing_reference'][:10]}")
    if report["missing_grantha"]:
        print(f"  reference segments with no grantha: {report['missing_grantha'][:10]}")
    print(f"word recall     : {s['matched_words']}/{s['ref_words']} = {s['word_recall']:.2%}")
    print(f"word precision  : {s['matched_words']}/{s['dec_words']} = {s['word_precision']:.2%}")
    print(f"base-text CER   : {s['base_cer']:.2%}")
    print(f"aligned CER     : {s['aligned_cer']:.2%}  ({s['aligned_words']} words matched 1:1)")
    print(f"exact words     : {s['aligned_exact']:.2%}  of {s['aligned_words']} aligned pairs")
    print(f"full-text CER   : {s['full_cer']:.2%}  (swaras included)")
    print(f"accent agreement: {s['accent_agreement']:.2%}")
    print("\nworst anuvakas (base CER):")
    for row in sorted(report["anuvakas"], key=lambda r: -r["base_cer"])[:8]:
        print(f"  K{row['kandam']}P{row['prasna']}A{row['anuvaka']:>2}  CER={row['base_cer']:.1%}  recall={row['word_recall']:.0%}")
    print("\ntop confusions (reference -> decoded):")
    for c in report["top_confusions"][:25]:
        print(f"  {c['count']:>4}x  {c['reference']!r} -> {c['decoded']!r}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
