"""Generate Malayalam_JSV/samhita_marker_review.csv for user approval.

Frozen per-letter lookup (Locked Decision #1): every distinct swara marker
found in the Jaimineeya Samaveda Samhita text is decomposed per Devanagari
character, each character resolved to a Grantha glyph from swara_mapping.json
(Ayugma-only table + fixed matra table), and any character with no entry is
flagged for review (fallback codepoint shown). The output CSV is the artifact
the user reviews and approves once; the accompanying swara_lookup_frozen.json
is the machine-readable frozen table that drives the pipeline
(src/malayalam reads the frozen JSON, never the live sheet).

2026-08-14 revision (Ayugma-only, manuscript truth):
  - The sheet now curates the 'Grantha Glyph' column as authoritative:
    codepoints are derived from the glyph characters, so the review derives
    its letter table from swara_mapping.json instead of hardcoding entries.
  - Only the Ayugma table is used; Yugma swaras are not used by the Samhita.
    Letters outside the Ayugma table (ga/cha/ja/jha/TTha/Dda/Ddha/da/na/ba/
    la/LLa/va/ha/ma and friends) do not occur as swara markers in the corpus;
    if one ever does it resolves via fallback with a LETTER_NOT_IN_SHEET flag.
  - Sheet anomalies are FIXED in the sheet (2026-08-14): A04 glyph is now the
    canonical TTA (U+1131F), A15/A17/A19 now include the virama
    (pl/tr/kra), so no per-letter overrides are needed and no marker is
    'decided'.
  - A13 (Saa) resolves to the MALAYALAM character ശ (U+0D36) per the
    reference manuscript, and its dependent signs resolve to MALAYALAM
    matras (ശാ/ശി/ശു/...); Grantha matras cannot shape onto a Malayalam
    base and would render as dotted circles in the PDF.
  - Corrupted markers are resolved best-effort and flagged; QA report lists
    their occurrences. No source data edits.

2026-08-14 review overrides (source-annotation errors, input to be corrected):
  - 'मा' (नार्क्ता(मा)): the marker does not match the word (नार्क्ता ends in
    -क्ता, not मा); the same mantra later renders the word मा with marker
    (कि). Classified source=corrupt.
  - 'वृ' (वृ(वृ)): flagged corrupt per review. Classified source=corrupt.
  Both overrides become inert automatically once the markers are removed
  from data/input/Samhita_corrected.txt.

Usage:
    .venv\\Scripts\\python.exe -X utf8 Malayalam_JSV\\generate_marker_review.py
"""

import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "input" / "Samhita_corrected.txt"
MAPPING = Path(__file__).parent / "swara_mapping.json"
OUT = Path(__file__).parent / "samhita_marker_review.csv"
OUT_DATA_CSV = ROOT / "data" / "output" / "malayalam" / "samhita_marker_review.csv"
FROZEN = Path(__file__).parent / "swara_lookup_frozen.json"

MARKER_RE = re.compile(r"\(([^)]+)\)")

# Independent vowels -> Grantha (only reachable via corrupted markers).
VOWEL_TABLE = {
    "अ": "11305", "आ": "11306", "इ": "11307", "ई": "11308",
    "उ": "11309", "ऊ": "1130A", "ऋ": "1130D", "ए": "1130E",
    "ऐ": "1130F", "ओ": "11313", "औ": "11314",
}

SPECIAL = {"\u094D": "1134D", "\u0902": "11302", "\u0903": "11303"}  # virama, anusvara, visarga

# A13 (Saa) resolves to the MALAYALAM character ശ (U+0D36) per the reference
# manuscript, so its dependent signs MUST be Malayalam matras (U+0D3E..):
# a Grantha matra cannot shape onto a Malayalam base and renders as a dotted
# circle in the PDF. Applies while the last emitted base letter is A13.
MALAYALAM_MATRA = {
    "\u093E": "0D3E", "\u093F": "0D3F", "\u0940": "0D40", "\u0941": "0D41",
    "\u0942": "0D42", "\u0943": "0D43", "\u0944": "0D44", "\u0947": "0D46",
    "\u0948": "0D47", "\u094B": "0D4A", "\u094C": "0D4B",
    "\u0902": "0D02", "\u0903": "0D03", "\u094D": "0D4D",
}

# Markers that are source-annotation errors (reviewed 2026-08-14): the
# marker does not belong with its word. Resolved best-effort and classified
# source=corrupt; overrides become inert once the input file is corrected.
CORRUPT_OVERRIDES = {"\u092E\u093E", "\u0935\u0943"}  # मा, वृ

# Devanagari letters outside the Ayugma table (Yugma-only letters and others):
# emitted with their canonical Grantha codepoint and a LETTER_NOT_IN_SHEET
# flag (source=fallback). None of these occur as swara markers in the corpus;
# the table guards against corrupt markers only.
FALLBACK_LETTERS = {
    "ग": "11317", "घ": "11318", "छ": "1131B", "ज": "1131C", "झ": "1131D",
    "ञ": "1131E", "ठ": "11320", "ड": "11321", "ढ": "11322", "द": "11326",
    "ध": "11327", "न": "11328", "ब": "1132C", "म": "1132E", "ल": "11332",
    "ळ": "11333", "व": "11335", "ह": "11339",
}


CUSTOM_SWARA_OVERRIDES = [
    # Pla family (longest prefixes first)
    ("प्ला", ["E021"]),
    ("प्लि", ["E022"]),
    ("प्ली", ["E023"]),
    ("प्लु", ["E024"]),
    ("प्लू", ["E025"]),
    ("प्ल्", ["E026"]),
    ("प्ल", ["E020"]),
    # Sha family (longest prefixes first)
    ("शा", ["E010"]),
    ("शि", ["E011"]),
    ("शी", ["E012"]),
    ("शु", ["E015"]),
    ("शू", ["E016"]),
    ("शृ", ["E017"]),
    ("शॄ", ["E018"]),
    ("शे", ["E019"]),
    ("शै", ["E01A"]),
    ("शो", ["E01B"]),
    ("शौ", ["E01C"]),
    ("श्रू", ["E027"]),
    ("श्रृ", ["E028"]),
    ("श्", ["E013"]),
    # Kra & Tra family
    ("क्र्", ["E01F"]),
    ("क्र", ["11315", "1134D", "11330"]),
    ("त्र्", ["11324", "1134D", "11330", "1134D"]),
    ("त्र", ["11324", "1134D", "11330"]),
    # Clean Nna composites
    ("णु", ["E029"]),
    ("श", ["0D36"]),
]


def load_mapping() -> tuple[dict, dict, list, dict]:
    """Return (letters, multi, matra) derived from swara_mapping.json.

    letters: single Devanagari char -> entry dict (grantha_text/codepoints).
    multi:   multi-char entries (pl/tr/kra), longest first, for prefix match.
    matra:   Devanagari codepoint -> Grantha codepoint.
    """
    with open(MAPPING, encoding="utf-8") as fh:
        data = json.load(fh)
    letters: dict[str, dict] = {}
    multi: list[dict] = []
    for e in data["ayugma"]:
        if len(e["devanagari_char"]) > 1:
            multi.append(e)
        else:
            letters[e["devanagari_char"]] = e
    multi.sort(key=lambda e: -len(e["devanagari_char"]))
    matra = {int(cp[2:], 16): int(gcp[2:], 16) for cp, gcp in data["matra_table"].items()}
    return letters, multi, matra


def resolve(marker: str, letters: dict, multi: list, matra: dict) -> tuple[list[str], list[str]]:
    """Return (grantha_codepoints, flags) for a marker string."""
    cps: list[str] = []
    flags: list[str] = []
    i = 0
    while i < len(marker):
        matched_override = False
        for prefix, override_cps in CUSTOM_SWARA_OVERRIDES:
            if marker.startswith(prefix, i):
                cps.extend(override_cps)
                i += len(prefix)
                matched_override = True
                break
        if matched_override:
            continue

        ch = marker[i]
        matched = False
        for entry in multi:
            if marker.startswith(entry["devanagari_char"], i):
                cps.extend(entry["grantha_codepoints"])
                i += len(entry["devanagari_char"])
                matched = True
                break
        if matched:
            continue
        if ch in letters:
            cps.extend(letters[ch]["grantha_codepoints"])
        elif ch in VOWEL_TABLE:
            cps.append(VOWEL_TABLE[ch])
            flags.append(f"INDEPENDENT_VOWEL:{ch}")
        elif ch in SPECIAL:
            cps.append(SPECIAL[ch])
        elif ch in FALLBACK_LETTERS:
            cps.append(FALLBACK_LETTERS[ch])
            flags.append(f"LETTER_NOT_IN_SHEET:{ch}")
        elif ch == "।":
            flags.append("CORRUPTED_DANDA_IN_MARKER")
        elif ch.isspace():
            flags.append("CORRUPTED_SPACE_IN_MARKER")
        elif ch.isascii():
            flags.append(f"CORRUPTED_ASCII:{ch!r}")
        elif 0x0900 <= ord(ch) <= 0x097F:
            m = matra.get(ord(ch))
            if m:
                cps.append(f"{m:04X}")
            else:
                flags.append(f"UNMAPPED_DEVANAGARI:U+{ord(ch):04X}")
        else:
            flags.append(f"UNMAPPED:U+{ord(ch):04X}")
        i += 1
    return cps, flags


def main() -> None:
    letters, multi, matra = load_mapping()
    entry_hex_to_ids: dict[str, list[str]] = {}
    entries = list(letters.values()) + multi
    for e in entries:
        key = "".join(e["grantha_codepoints"])
        entry_hex_to_ids.setdefault(key, []).append(e["id"])

    text = SOURCE.read_text(encoding="utf-8")
    counts = Counter(MARKER_RE.findall(text))

    rows = []
    sheet_hex_used: set[str] = set()
    for marker, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        cps, flags = resolve(marker, letters, multi, matra)
        hex_str = " ".join(cps)
        if hex_str:
            sheet_hex_used.add("".join(cps))
        matches = entry_hex_to_ids.get("".join(cps), [])
        sheet_match = " ".join(matches) if matches else ""
        all_flags = sorted(set(flags))
        if marker in CORRUPT_OVERRIDES:
            source = "corrupt"
            all_flags.append("CORRUPTED_SOURCE_ANNOTATION")
        elif any(f.startswith(("CORRUPTED", "INDEPENDENT_VOWEL", "UNMAPPED", "CORRUPTED_ASCII")) for f in all_flags):
            source = "corrupt"
        elif any(f.startswith("LETTER_NOT_IN_SHEET") for f in all_flags):
            source = "fallback"
        elif all_flags:
            source = "decided"   # deliberate overrides (currently none)
        else:
            source = "sheet"
        rows.append(
            {
                "marker": marker,
                "count": count,
                "dev_char_count": len(marker),
                "grantha_hex": hex_str,
                "grantha_text": "".join(chr(int(cp, 16)) for cp in cps) if cps else "",
                "sheet_entry_match": sheet_match,
                "source": source,
                "flags": "; ".join(all_flags),
            }
        )

    OUT_DATA_CSV.parent.mkdir(parents=True, exist_ok=True)
    for out_path in (OUT, OUT_DATA_CSV):
        try:
            with open(out_path, "w", encoding="utf-8-sig", newline="") as fh:
                writer = csv.DictWriter(
                    fh,
                    fieldnames=["marker", "count", "dev_char_count", "grantha_hex",
                                "grantha_text", "sheet_entry_match", "source", "flags"],
                )
                writer.writeheader()
                writer.writerows(rows)
            print(f"Wrote {out_path}")
        except PermissionError:
            print(f"Warning: Could not overwrite {out_path} (file may be open in viewer).")

    # Build modifiers dictionary for swara_lookup_frozen.json
    canonical_modifiers = [
        {"id": "MOD-01", "shortcut": "(A)", "name": "Syllable Arc (Tie)", "glyph": "\uE004", "hex": "U+256D + U+256E / E004", "stack_pos": "Above", "inputs": ["(A)", "(a)", "(╭╮)", "(⁀)", "╭╮", "⁀"]},
        {"id": "MOD-02", "shortcut": "(B)", "name": "Underbar", "glyph": "\uE007", "hex": "E007", "stack_pos": "Below", "inputs": ["(B)", "(b)", "(_)", "_"]},
        {"id": "MOD-03", "shortcut": "(C)", "name": "Full Stop / Dot", "glyph": ".", "hex": "002E", "stack_pos": "Inline", "inputs": ["(C)", "(c)", "(.)", "."]},
        {"id": "MOD-04", "shortcut": "(D)", "name": "Single Danda", "glyph": "।", "hex": "0964", "stack_pos": "Inline", "inputs": ["(D)", "(d)", "(|)", "(।)", "|", "।"]},
        {"id": "MOD-05", "shortcut": "(E)", "name": "Double Danda", "glyph": "॥", "hex": "0965", "stack_pos": "Inline", "inputs": ["(E)", "(e)", "(||)", "(॥)", "||", "॥"]},
        {"id": "MOD-06", "shortcut": "(F)", "name": "Caret / Peak", "glyph": "\uE005", "hex": "E005", "stack_pos": "Above", "inputs": ["(F)", "(f)", "(^)", "(/\\)", "^", "/\\", "˄"]},
        {"id": "MOD-07", "shortcut": "(G)", "name": "High/Mid-Dot", "glyph": "\uE001", "hex": "E001", "stack_pos": "Above", "inputs": ["(G)", "(g)", "(ॱ)", "(·)", "ॱ", "·"]},
        {"id": "MOD-08", "shortcut": "(H)", "name": "Low Comma", "glyph": "\uE00A", "hex": "E00A", "stack_pos": "Below", "inputs": ["(H)", "(h)", "(,)", "(ˏ)", ",", "ˏ"]},
        {"id": "MOD-09", "shortcut": "(I)", "name": "Chevron Roof", "glyph": "\uE006", "hex": "E006", "stack_pos": "Above", "inputs": ["(I)", "(i)", "(Ʌ)", "Ʌ", "∧"]},
        {"id": "MOD-10", "shortcut": "(J)", "name": "Heavy Vertical / Down Line", "glyph": "\uE002", "hex": "E002", "stack_pos": "Below", "inputs": ["(J)", "(j)", "(J_1)", "(┃)", "(╷)", "┃", "╷"]},
        {"id": "MOD-11", "shortcut": "(K)", "name": "Descending Tone", "glyph": "\uE003", "hex": "E003", "stack_pos": "Below", "inputs": ["(K)", "(k)", "(\\)", "(╲)", "\\", "╲"]},
        {"id": "MOD-12", "shortcut": "(L)", "name": "Swarita Accent", "glyph": "\u0951", "hex": "0951", "stack_pos": "Above", "inputs": ["(L)", "(l)", "(॑)", "॑"]},
    ]

    modifier_input_map = {}
    for mod in canonical_modifiers:
        for inp in mod["inputs"]:
            clean_inp = inp.strip("()")
            modifier_input_map[inp] = mod["glyph"]
            modifier_input_map[clean_inp] = mod["glyph"]

    frozen = {
        "_meta": {
            "description": "Authoritative per-marker and per-modifier swara lookup for the Jaimineeya Samaveda Malayalam pipeline.",
            "generated_by": "Malayalam_JSV/generate_marker_review.py",
            "source_mapping": "Malayalam_JSV/swara_mapping.json",
            "grantha_text_note": (
                "grantha_text carries the actual Unicode glyph characters "
                "(derived from the sheet 'Grantha Glyph' column); "
                "grantha_codepoints are the matching codepoints."
            ),
            "decisions": [
                "Ayugma-only mapping; Yugma swaras not used by the Samhita",
                "A13 Saa -> Malayalam ശ (U+0D36) per reference manuscript",
                "A04 TTA -> U+1131F (sheet glyph corrected)",
                "A15/A17/A19 virama clusters (pl/tr/kra) resolve to sheet entries",
                "12 Canonical Vedic Modifiers (A-L) with separate stacking handling",
            ],
            "occurrence_check": f"total marker occurrences: {sum(counts.values())}",
        },
        "matra_table": {f"U+{k:04X}": f"U+{v:04X}" for k, v in sorted(matra.items())},
        "modifiers": {m["shortcut"]: m for m in canonical_modifiers},
        "modifier_input_map": modifier_input_map,
        "lookup": {
            r["marker"]: {
                "grantha_text": r["grantha_text"],
                "grantha_codepoints": r["grantha_hex"].split() if r["grantha_hex"] else [],
                "count": r["count"],
                "source": r["source"],
            }
            for r in rows
        },
    }
    with open(FROZEN, "w", encoding="utf-8") as fh:
        json.dump(frozen, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    unused = [
        (e["id"], e["grantha_text"], e["malayalam_name"])
        for e in entries
        if "".join(e["grantha_codepoints"]) not in sheet_hex_used
    ]
    flagged = [r for r in rows if r["flags"]]
    print(f"Distinct markers: {len(rows)}  (total occurrences: {sum(counts.values())})")
    print(f"Flagged rows:     {len(flagged)}")
    print(f"By source:        {dict(Counter(r['source'] for r in rows))}")
    print(f"Ayugma entries never produced by any marker: {len(unused)}")
    for eid, text, name in unused:
        print(f"  UNUSED {eid}  {text!r}  ({name})")
    print()
    print("Flagged rows (top by count):")
    for r in sorted(flagged, key=lambda r: -r["count"])[:40]:
        print(f"  {r['marker']!r:16s} x{r['count']:<5d} -> {r['grantha_hex'] or 'NONE':28s} {r['flags']}")
    print()
    print(f"Wrote {OUT}")
    print(f"Wrote {FROZEN}")


if __name__ == "__main__":
    main()