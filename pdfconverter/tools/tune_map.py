"""
Greedy map tuner: measure base CER / word recall for candidate byte mappings.

The corpus and reference are decoded once into plain strings; each candidate
is then applied to the in-memory tables in `ganapathy_map`, scored, and
reverted.  The best improvement is kept and the loop repeats, so the map
converges without a human having to re-run the full docx pipeline for every
idea.

    python pdfconverter/tools/tune_map.py                  # baseline only
    python pdfconverter/tools/tune_map.py --auto --rounds 5
    python pdfconverter/tools/tune_map.py --set ';=म्'
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_reference as A
import ganapathy_map as M

TABLE_NAMES = ("CONSONANTS", "SUBSCRIPTS", "INDEPENDENT_VOWELS", "MATRAS",
               "DIGITS", "PUNCTUATION", "SWARAS")

_CORPUS: list[tuple[str, list[str]]] | None = None
_PAIRS: list[tuple[int, int, str]] | None = None


def corpus() -> list[tuple[str, list[str]]]:
    """[(reference base text, grantha tokens)] for compared anuvakas."""
    global _CORPUS
    if _CORPUS is None:
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        grantha = A.segment_grantha(os.path.join(here, "data", "input", "1st Paadam Final-Grantha-Cleaned.docx"))
        ref = A.segment_reference(os.path.join(here, "data", "input", "THAITHIREEYA SAMHITHA 1 (SETHU) प्रथम पादः .docx"))
        out = []
        for k in grantha:
            if k not in ref:
                continue
            toks = [w for w in " ".join(grantha[k]).replace("֍", " ").split()
                    if not A.is_tamil(w)]
            out.append((A.base_form(A.normalize(ref[k])), toks))
        _CORPUS = out
    return _CORPUS


def pairs() -> list[tuple[int, int, str]]:
    """[(segment, token, reference word)] as matched by the base map.

    The DP word alignment is computed once; scoring a candidate only needs
    to re-decode the tokens.  A candidate that changes the word boundaries
    is caught by the final `align_reference.py` run, not here.
    """
    global _PAIRS
    if _PAIRS is None:
        found = []
        for si, (ref_base, toks) in enumerate(corpus()):
            refw = ref_base.split()
            dec = [A.base_form(A.normalize(M.decode_text(t))) for t in toks]
            for ti, wj in A.align_tokens(dec, refw):
                if len(ti) == 1 and len(wj) == 1:
                    found.append((si, ti[0], refw[wj[0]]))
        _PAIRS = found
    return _PAIRS


_DECODE_CACHE: dict[str, str] = {}


def decode_cached(token: str) -> str:
    out = _DECODE_CACHE.get(token)
    if out is None:
        out = A.base_form(A.normalize(M.decode_text(token)))
        _DECODE_CACHE[token] = out
    return out


def invalidate() -> None:
    _DECODE_CACHE.clear()


def invalidate_containing(src: str) -> None:
    for key in [k for k in _DECODE_CACHE if src in k]:
        del _DECODE_CACHE[key]


def score() -> tuple[float, float, float]:
    """(aligned CER, base CER, word recall) over the cached corpus."""
    decoded = []
    ref_word_total = matched_total = 0
    ref_char_total = edit_total = 0
    for ref_base, toks in corpus():
        dec_toks = [decode_cached(t) for t in toks]
        decoded.append(dec_toks)
        dec = " ".join(dec_toks)
        ref_chars = re.sub(r"\s+", "", ref_base)
        dec_chars = re.sub(r"\s+", "", dec)
        edit_total += A.levenshtein(ref_chars, dec_chars)
        ref_char_total += len(ref_chars)
        rw, dw, matched, _, _, _ = A.word_diff_stats(ref_base, dec)
        ref_word_total += rw
        matched_total += matched

    aligned_chars = aligned_edit = 0
    for si, ti, ref_word in pairs():
        dec_word = decoded[si][ti]
        aligned_chars += len(ref_word)
        aligned_edit += A.levenshtein(ref_word, dec_word)

    cer = edit_total / ref_char_total if ref_char_total else 1.0
    aligned = aligned_edit / aligned_chars if aligned_chars else 1.0
    recall = matched_total / ref_word_total if ref_word_total else 0.0
    return aligned, cer, recall


def table_of(byte: str) -> str:
    for name in TABLE_NAMES:
        if byte in getattr(M, name):
            return name
    return "CONSONANTS"


def apply_override(byte: str, value: str) -> tuple[str, str | None]:
    name = table_of(byte)
    table = getattr(M, name)
    old = table.get(byte)
    table[byte] = value
    invalidate_containing(byte)
    return name, old


def revert_override(byte: str, name: str, old: str | None) -> None:
    table = getattr(M, name)
    if old is None:
        table.pop(byte, None)
    else:
        table[byte] = old
    invalidate_containing(byte)


def apply_multi(src: str, value: str) -> None:
    M.MULTI.insert(0, (src, value))
    invalidate_containing(src)


def revert_multi(src: str, value: str) -> None:
    M.MULTI.remove((src, value))
    invalidate_containing(src)


CANDIDATES: list[tuple[str, str]] = [
    (")", "ꣳ"), (")", "꣣"), (")", ""),
    ("™", "ꣴ"), ("™", ""), ("™", "\ue004"),
    ("?", "ङ्"), ("?", "ङ"), ("?", "ङ्ग"),
    ("X", "ध"), ("X", "द्ध"),
    ("º", "्द्व"), ("º", "द्व"),
    ("…", "्ग"), ("…", "ग"),
    ("8", "्य"), ("8", "्"), ("8", "ँ"),
    ("!", "ँ"), ("!", "\u1CDA"),
    ("1", "े"), ("1", "ो"), ("11", "ै"), ("11", "ौ"),
    ("r", "ृ"), ("r", "ऋ"), ("r", "र"),
    ("~", "द्व"), ("~", "्ह"), ("~", "्व"),
    ("µ", "्स"), ("µ", "्य"),
    ("´", "्ष"), ("´", "्र"),
    ("ˆ", "्च"), ("ˆ", "्क"),
    ("N", "ञ्ज"), ("N", "ञ्"), ("N", "ण्"),
    ("V", "ञ्च"), ("V", "ञ्"), ("&", "ञ्च"),
    ("©", "्ध"), ("©", "्ज"),
    ("†", "्घ"), ("†", "्थ"),
    ("H", "्फ"), ("H", "घ्"),
    ("Ú", "्स्"), ("Ú", "्थ"),
    ("±", "ल्ँ"), ("±", "्ल"),
    ("¯", "्भ्"), ("¯", "्र"),
    ("Ý", "्र"), ("Ý", "र"),
    ("³", "्श"), ("³", "श"),
    ("ƒ", "्क"), ("ƒ", "्श"),
    ("M", "त्"), ("M", "म्"), ("M", "्त"),
    ("T", "ओ"), ("T", "ह"), ("T", "ओम्"),
    ("t", "ए"), ("t", "ट"),
    ("o", "छ"), ("o", "च"),
    ("C", "न्न"), ("C", "छ"),
    ("Š", "ज्"), ("Š", "ज"),
    ("<", "न्"), ("<", "न"),
    ("Ö", "व"), ("Ö", "द्व"),
    ("a", "ट"), ("a", "त"),
    ("m", "न"), ("n", "म"),
    ("w", "इ"), ("W", "ई"), ("e", "उ"), ("E", "ऊ"),
    ("q", "अ"), ("Q", "आ"),
]

MULTI_CANDIDATES: list[tuple[str, str]] = [
    ("X²", "ध्व"), ("X]", "द्धि"), ("X3", "द्धा"), ("X(", "द्ध"),
    ("™v²3", "ꣴस्वाहा"), ("™v²g", "ꣴस्वधि"),
]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--set", action="append", default=[], metavar="BYTE=VALUE")
    ap.add_argument("--multi", action="append", default=[], metavar="SRC=VALUE")
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--rounds", type=int, default=1)
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    if args.set or args.multi:
        for spec in args.set:
            byte, _, value = spec.partition("=")
            name, old = apply_override(byte, value)
            print(f"{byte!r} ({name}): {old!r} -> {value!r}")
        for spec in args.multi:
            src, _, value = spec.partition("=")
            apply_multi(src, value)
            print(f"MULTI {src!r} -> {value!r}")
        aligned, cer, recall = score()
        print(f"aligned CER = {aligned:.2%}   base CER = {cer:.2%}   word recall = {recall:.2%}")
        return

    aligned0, cer0, recall0 = score()
    print(f"baseline: aligned CER = {aligned0:.2%}   base CER = {cer0:.2%}   "
          f"word recall = {recall0:.2%}")
    if not args.auto:
        return

    accepted = []
    for rnd in range(args.rounds):
        best = None
        for byte, value in CANDIDATES:
            name, old = apply_override(byte, value)
            aligned, cer, recall = score()
            revert_override(byte, name, old)
            if aligned < aligned0 - 1e-4 and (best is None or aligned < best[0]):
                best = (aligned, cer, recall, "byte", byte, value)
        for src, value in MULTI_CANDIDATES:
            apply_multi(src, value)
            aligned, cer, recall = score()
            revert_multi(src, value)
            if aligned < aligned0 - 1e-4 and (best is None or aligned < best[0]):
                best = (aligned, cer, recall, "multi", src, value)
        if not best:
            print(f"round {rnd + 1}: no improvement")
            break
        aligned, cer, recall, kind, key, value = best
        if kind == "byte":
            name, old = apply_override(key, value)
        else:
            name, old = "MULTI", None
            apply_multi(key, value)
        aligned0, cer0, recall0 = aligned, cer, recall
        accepted.append({"kind": kind, "key": key, "from": old, "to": value,
                         "table": name, "aligned_cer": round(aligned, 5),
                         "cer": round(cer, 5), "recall": round(recall, 5)})
        print(f"round {rnd + 1}: [{kind}] {key!r} {old!r} -> {value!r}   "
              f"aligned CER {aligned:.2%}  base CER {cer:.2%}  recall {recall:.2%}")

    print(f"\nfinal: aligned CER = {aligned0:.2%}   base CER = {cer0:.2%}   "
          f"word recall = {recall0:.2%}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"final": {"aligned_cer": round(aligned0, 5),
                                 "base_cer": round(cer0, 5),
                                 "recall": round(recall0, 5)},
                       "accepted": accepted}, fh, ensure_ascii=False, indent=2)
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
