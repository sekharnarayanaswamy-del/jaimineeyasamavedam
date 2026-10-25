"""
Convert one Grantha chunk to Unicode Devanagari, in place, without the reference.

The source chunk (`<name>.grantha.docx`) is copied, and every paragraph run is
rewritten through `ganapathy_map.decode_text`.  Formatting that Word 2013 needs
is applied at the same time:

  * Vedic text      Sanskrit 2020, 16 pt (12 pt in tables), justified, line=360
  * Tamil commentary Vijaya, 14 pt (12 pt in tables), justified, line=360
  * headings        bold, centred, 16 pt
  * tables          cell paragraphs left aligned, line=280, space after 40

The converter never reads the SETHU reference: the reference is an oracle for
`align_reference.py`, never a source of output text.

    python pdfconverter/tools/convert_chunk.py --chunk K1P1
    python pdfconverter/tools/convert_chunk.py --chunk K1P1 --no-fail
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.text.paragraph import Paragraph

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ganapathy_map as M
from build_chunks import CHUNK_DIR
from align_reference import KANDAM_PATTERNS, PRASNA_PATTERNS

DEVA_FONT = "Sanskrit 2020"
TAMIL_FONT = "Vijaya"
BODY_PT, TABLE_PT = 16.0, 12.0
TAMIL_PT, TAMIL_TABLE_PT = 14.0, 12.0
# Running heads sit above the text; 12 pt keeps them subordinate to the
# mantras while staying legible in print.
HEADER_PT, HEADER_TAMIL_PT = 12.0, 12.0

HEADING_KEYS = [pat for pat, _ in PRASNA_PATTERNS] + [pat for pat, _ in KANDAM_PATTERNS]
RULE_RE = re.compile(r"^[\s\u2013\u2014\-_=~*·•]+$")
NUMBER_RE = re.compile(r"^[\s0-9०-९.,;:()\[\]{}\-–—]+$")

# The opening salutation block of every Prasna.  The printed page centres the
# whole block; only `ॐ नमः परमात्मने` and the Prasna line are matched by the
# heading rules, so `श्रीगुरुभ्यो नमः` and `हरिः ओ (४) म्` used to fall through
# to justified and sit hard against the left margin.  `तैत्तिरीयसंहितायाम्`
# (first Prasna of each Kanda only) belongs to the same block.  These are the
# raw Grantha bytes of those three lines.
INVOCATION_PREFIXES = (">[(u(6l(61J(83", "bl], T ", "11DD\u00a6]l[Kv;b]D3K3")


# ---------------------------------------------------------------------------
# text helpers
# ---------------------------------------------------------------------------

def is_tamil_char(ch: str) -> bool:
    return 0x0B80 <= ord(ch) <= 0x0BFF


def _is_grantha(ch: str) -> bool:
    return ch in M.GRANTHA_TRIGGERS


def split_scripts(text: str) -> list[tuple[str, bool]]:
    """Split into (segment, is_tamil) runs, keeping whitespace with its side.

    Curly quotes are attached to the Tamil run they hug, because the Tamil
    commentary uses them as ordinary quotation marks while the Grantha
    encoding uses the same bytes for swara accents.
    """
    out: list[tuple[str, bool]] = []
    buf, current = "", None
    for i, ch in enumerate(text):
        if ch.isspace():
            buf += ch
            continue
        tamil = M.hugs_tamil(text, i) if ch in M.TAMIL_QUOTES else is_tamil_char(ch)
        if current is None:
            current = tamil
        elif tamil != current:
            out.append((buf, current))
            buf, current = "", tamil
        buf += ch
    if buf:
        out.append((buf, bool(current)))
    return out


NUMERIC_CELL_RE = re.compile(r"^[\s0-9\u0966-\u096F.,;:/()\[\]{}\-\u2013\u2014]+$")


def classify(text: str, in_table: bool = False) -> str:
    stripped = text.strip()
    if not stripped:
        return "blank"
    if in_table:
        # number/range columns (`2-50`, `103`, `4.47`) stay exactly as printed
        if NUMERIC_CELL_RE.match(stripped) and (
                any(ch.isdigit() for ch in stripped)
                or stripped in {"-", "\u2013", "\u2014", "/", "."}):
            return "cell_number"
        return "cell_text"
    if RULE_RE.match(stripped):
        return "rule"
    if any(key in text for key in HEADING_KEYS) or "hlk3D°1G" in text:
        return "heading"
    if not in_table and stripped.startswith(INVOCATION_PREFIXES):
        return "invocation"
    if NUMBER_RE.match(stripped) and len(stripped) <= 6:
        return "number"
    has_grantha = any(_is_grantha(ch) for ch in text)
    has_tamil = any(is_tamil_char(ch) for ch in text)
    if has_tamil and not has_grantha:
        return "tamil"
    if has_tamil:
        return "mixed"
    return "mantra"


def decode(text: str) -> str:
    """Decode Grantha runs; leave already-Unicode (Tamil or plain) text alone.

    The Tamil commentary in the source is already Unicode Tamil, so only runs
    that actually contain Grantha letters are translated.  Punctuation that is
    not part of a Grantha run (a comma inside a Tamil sentence, the digits of
    a table range) survives verbatim.  A run of bare swara bytes (a line with
    only `” ” ”`) is decoded too, so the orphan accents are dropped instead of
    surviving as junk.
    """
    if not text:
        return ""
    parts = []
    for segment, tamil in split_scripts(text):
        decode_it = (not tamil) and (
            any(_is_grantha(ch) for ch in segment)
            or any(ch in "\u201C\u201D" for ch in segment))
        if decode_it:
            parts.append(M.decode_text(segment))
        else:
            parts.append(segment)
    out = M.canonicalize("".join(parts))
    # Collapse only *text* whitespace.  Inside a run of flower motifs the
    # multiple spaces are deliberate: they are what separates the ornaments on
    # the printed page, so they must survive verbatim.
    out = "".join(chunk if ornament else re.sub(r"[ \t]{2,}", " ", chunk)
                  for chunk, ornament in split_ornaments(out))
    return out.strip()


# Runs typeset in one of these faces carry legacy Grantha bytes; any other
# explicit font means the characters are literal (see `run_is_literal`).
GRANTHA_FONT_HINTS = ("ganapathy", "grantha")
_PLACEHOLDER_BASE = 0xE100


def run_is_literal(run) -> bool:
    """True when a run's text is literal, not Grantha-encoded.

    The editors wrapped a few visargas in Latin-font parentheses -- `(`, `:`,
    `)` typed in Calibri, printed as `(ः)`.  Those bytes must survive as
    punctuation: read as Grantha they would become anudatta + gum, which both
    corrupts the word and leaves an orphan combining mark, i.e. the dotted
    circle Word draws.  A run is only treated as literal when it is explicitly
    in a non-Grantha font *and* contains no Grantha letters.
    """
    font = (run.font.name or "").lower()
    if not font or any(hint in font for hint in GRANTHA_FONT_HINTS):
        return False
    # Only *non-ASCII* Grantha glyphs prove that a run is encoded text.  `{`
    # and `}` are also Grantha letters (क्त), but in a Latin-font run they are
    # literal braces — the `{५}` anuvaka markers are exactly that.
    return not any(ch in M.GRANTHA_TRIGGERS and not ch.isascii()
                   for ch in run.text)


def decode_paragraph(paragraph) -> str:
    """Decode a paragraph, preserving runs that hold literal (non-Grantha) text."""
    literal: list[str] = []
    pieces: list[str] = []
    for run in paragraph.runs:
        text = run.text
        if text and run_is_literal(run):
            pieces.append(chr(_PLACEHOLDER_BASE + len(literal)))
            literal.append(text)
        else:
            pieces.append(text)
    if not literal:
        return decode(paragraph.text)
    out = decode("".join(pieces))
    for i, original in enumerate(literal):
        out = out.replace(chr(_PLACEHOLDER_BASE + i), original)
    # The literal Calibri pair `(` ... `)` wraps a decoded visarga: splice the
    # printed colon in afterwards, once the placeholders are gone.
    return out.replace("(\u0903)", "(:)")


# ---------------------------------------------------------------------------
# docx helpers
# ---------------------------------------------------------------------------

def set_para_layout(paragraph, alignment="both", line="360", after="120"):
    pPr = paragraph._p.get_or_add_pPr()
    jc = pPr.find(qn("w:jc"))
    if jc is None:
        jc = OxmlElement("w:jc")
        pPr.append(jc)
    jc.set(qn("w:val"), alignment)
    sp = pPr.find(qn("w:spacing"))
    if sp is None:
        sp = OxmlElement("w:spacing")
        pPr.append(sp)
    sp.set(qn("w:line"), line)
    sp.set(qn("w:lineRule"), "auto")
    sp.set(qn("w:after"), after)


def style_run(run, font: str, size: float, bold: bool = False):
    run.font.name = font
    run.font.size = Pt(size)
    run.bold = bold
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rFonts.set(qn(attr), font)
    if rPr.find(qn("w:noProof")) is None:
        rPr.append(OxmlElement("w:noProof"))
    if rPr.find(qn("w:lang")) is None:
        lang = OxmlElement("w:lang")
        lang.set(qn("w:val"), "en-US")
        lang.set(qn("w:bidi"), "hi-IN")
        rPr.append(lang)


# The flower motif (U+058D/U+058E) is decoration: the source sets it in
# Calibri, where Word substitutes a symbol font that draws the wide, clearly
# spaced flower of the printed book.  Re-setting it in Sanskrit 2020 picks a
# different glyph (a tighter, circled flower), so ornament runs keep the
# source face and the spaces that separate the motifs.
ORNAMENT_CHARS = "\u058D\u058E"
ORNAMENT_FONT = "Calibri"


def split_ornaments(text: str) -> list[tuple[str, bool]]:
    """Split a segment into ``(chunk, is_ornament)`` chunks.

    A chunk of ornaments *and the spaces between them* stays together, so the
    motif keeps the spacing of the printed page instead of collapsing into a
    solid row.
    """
    out: list[tuple[str, bool]] = []
    i, n = 0, len(text)
    while i < n:
        if text[i] in ORNAMENT_CHARS:
            j = i
            while j < n and (text[j] in ORNAMENT_CHARS or text[j].isspace()):
                j += 1
            out.append((text[i:j], True))
            i = j
        else:
            j = i
            while j < n and text[j] not in ORNAMENT_CHARS:
                j += 1
            out.append((text[i:j], False))
            i = j
    return out


def rewrite(paragraph, segments: list[tuple[str, bool]], deva_pt: float,
            tamil_pt: float, bold: bool = False):
    """Replace the paragraph's runs with one run per script segment."""
    base = paragraph.runs[0]._r if paragraph.runs else None
    for run in list(paragraph.runs):
        run._r.getparent().remove(run._r)
    for text, tamil in segments:
        for chunk, ornament in split_ornaments(text):
            if not chunk:
                continue
            run = paragraph.add_run(chunk)
            if base is not None:
                rPr = run._r.get_or_add_rPr()
                old = base.find(qn("w:rPr"))
                if old is not None:
                    for child in old:
                        if child.tag not in (qn("w:rFonts"), qn("w:sz"), qn("w:szCs")):
                            rPr.append(child)
            if ornament:
                style_run(run, ORNAMENT_FONT, deva_pt, bold)
            else:
                style_run(run, TAMIL_FONT if tamil else DEVA_FONT,
                          tamil_pt if tamil else deva_pt, bold)


def process_paragraph(paragraph, stats: dict, in_table: bool = False):
    text = paragraph.text
    kind = classify(text, in_table)
    stats[kind] = stats.get(kind, 0) + 1
    if kind in ("blank", "rule", "number", "cell_number"):
        if kind == "cell_number":
            set_para_layout(paragraph, "left", "280", "40")
            return
        if kind in ("blank", "number"):
            for run in list(paragraph.runs):
                run.text = ""
            return
        return

    decoded = decode_paragraph(paragraph)
    stats["chars_in"] = stats.get("chars_in", 0) + len(text)
    stats["chars_out"] = stats.get("chars_out", 0) + len(decoded)

    segments = split_scripts(decoded)
    if in_table:
        rewrite(paragraph, segments, TABLE_PT, TAMIL_TABLE_PT)
        set_para_layout(paragraph, "left", "280", "40")
        return

    heading = kind == "heading"
    rewrite(paragraph, segments, BODY_PT, TAMIL_PT, bold=heading)
    set_para_layout(paragraph, "center" if heading or kind == "invocation" else "both",
                    "360", "120")


def iter_table_paragraphs(table):
    """Every paragraph of a table exactly once, nested tables included.

    `row.cells` is deliberately avoided: it repeats merged cells, and the old
    `id(cell._tc)` de-duplication was unsafe because lxml proxies are garbage
    collected and their addresses reused, silently skipping paragraphs.
    Walking the raw XML visits each `w:tc` once, in document order.
    """
    for tc in table._tbl.iter(qn("w:tc")):
        for p in tc.findall(qn("w:p")):
            yield Paragraph(p, table)


# ---------------------------------------------------------------------------
# running heads / footers
# ---------------------------------------------------------------------------

HEADER_FOOTER_PARTS = ("header", "footer", "first_page_header",
                       "first_page_footer", "even_page_header",
                       "even_page_footer")


def has_grantha(text: str) -> bool:
    return (any(ch in M.GRANTHA_TRIGGERS for ch in text)
            or bool(M.leftover_bytes(text)))


def iter_header_footer_parts(doc):
    """Each distinct header/footer part of the document exactly once.

    Sections share parts (all even-page headers are usually one part), and
    decoding a shared part twice would double-apply the decoder, so dedupe on
    the part name.  `is_linked_to_previous` must be checked *before* touching
    `.part`: that property would otherwise create an empty definition.
    """
    seen: set[str] = set()
    for section in doc.sections:
        for name in HEADER_FOOTER_PARTS:
            hf = getattr(section, name)
            if hf.is_linked_to_previous:
                continue
            key = str(hf.part.partname)
            if key in seen:
                continue
            seen.add(key)
            yield name, hf


def process_header_footer(doc, stats: dict) -> None:
    """Decode the Grantha running heads, leaving plain footers untouched.

    Page numbers live in field results, whose cached text looks like an
    ordinary number; decoding such a paragraph would drop the field.  Only
    paragraphs that still contain Grantha bytes are touched, so the footers
    and any Tamil-only text keep their original formatting.
    """
    for _name, part in iter_header_footer_parts(doc):
        for paragraph in part.paragraphs:
            if not has_grantha(paragraph.text):
                continue
            decoded = decode_paragraph(paragraph)
            rewrite(paragraph, split_scripts(decoded), HEADER_PT,
                    HEADER_TAMIL_PT)
            stats["running_head"] = stats.get("running_head", 0) + 1
        for table in part.tables:
            for paragraph in iter_table_paragraphs(table):
                if not has_grantha(paragraph.text):
                    continue
                decoded = decode_paragraph(paragraph)
                rewrite(paragraph, split_scripts(decoded), TABLE_PT,
                        TAMIL_TABLE_PT)
                stats["running_head_table"] = stats.get("running_head_table", 0) + 1


# ---------------------------------------------------------------------------
# audit
# ---------------------------------------------------------------------------

LATIN_RE = re.compile(r"[A-Za-z]")
ACCENT_BEFORE_VIRAMA = re.compile(r"[\u0951\u0952\u1CDA]+\u094D")
DOUBLE_NASAL = re.compile(r"[\u0901\u0902][\u0901\u0902]")
# A Vedic accent written before a syllable-closing mark makes the shaper draw a
# dotted circle (both are marks, so the second has no base).
ACCENT_BEFORE_MARK = re.compile(r"[\u0951\u0952\u1CDA][\u0901-\u0903]")
# A combining mark with nothing to attach to: it follows whitespace, a danda or
# an opening bracket, or starts the text -- the same dotted circle in print.
ORPHAN_MARK = re.compile(
    r"(?:^|[\s\u0964\u0965(\[])[\u0900-\u0903\u093A-\u093C\u093E-\u094D"
    r"\u0951\u0952\u1CDA]")

# Characters the finished document may contain.  Anything else is either an
# unmapped Grantha glyph or a leftover typesetting artefact, and the gate has
# to see it: `Ë`/`˜`/`^` are not ASCII letters, so `latin_letters` misses them.
ALLOWED_PUNCT = set("\u0964\u0965\u058E\u2018\u2019\u201C\u201D\u2013\u2014")
ALLOWED_PUA = {"\uE003", "\uE004", "\uE006", "\uF205", "\uF206"}


def unknown_chars(text: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for ch in text:
        if ch.isspace() or ch in ALLOWED_PUNCT or ch in ALLOWED_PUA:
            continue
        cp = ord(ch)
        if 0x0900 <= cp <= 0x097F:      # Devanagari
            continue
        if 0xA8E0 <= cp <= 0xA8FF:      # Devanagari Extended (Vedic)
            continue
        if 0x1CD0 <= cp <= 0x1CFF:      # Vedic Extensions
            continue
        if 0x0B80 <= cp <= 0x0BFF:      # Tamil
            continue
        if ch.isascii():                # digits / punctuation kept verbatim
            continue
        out[ch] = out.get(ch, 0) + 1
    return out


def audit(doc) -> dict:
    texts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for p in iter_table_paragraphs(table):
            texts.append(p.text)
    for _name, part in iter_header_footer_parts(doc):
        texts.extend(p.text for p in part.paragraphs)
        for table in part.tables:
            texts.extend(p.text for p in iter_table_paragraphs(table))
    joined = "\n".join(texts)
    unknown = unknown_chars(joined)
    return {
        "legacy_bytes": len(M.leftover_bytes(joined)),
        "dotted_circle": joined.count("\u25CC"),
        "double_nasal": len(DOUBLE_NASAL.findall(joined)),
        "accent_before_virama": len(ACCENT_BEFORE_VIRAMA.findall(joined)),
        "accent_before_mark": len(ACCENT_BEFORE_MARK.findall(joined)),
        "orphan_mark": len(ORPHAN_MARK.findall(joined)),
        "latin_letters": len(LATIN_RE.findall(joined)),
        "unknown_chars": sum(unknown.values()),
        "unknown_sample": "".join(sorted(unknown)[:12]),
        "has_tamil": any(is_tamil_char(ch) for ch in joined),
    }


def save_docx(doc, path: str) -> str:
    """Save, tolerating a file that is open in Word / being synced.

    Writing straight to `path` fails with `PermissionError` when the previous
    output is still open in Word.  Save to `<path>.new.docx` and swap it in;
    if the target stays locked, keep the new file and say so, so the run still
    produces a checkable artefact.
    """
    tmp = path + ".new.docx"
    doc.save(tmp)
    for _ in range(3):
        try:
            os.replace(tmp, path)
            return path
        except PermissionError:
            time.sleep(0.5)
    print(f"  WARNING: {os.path.basename(path)} is locked (open in Word?); "
          f"wrote {os.path.basename(tmp)} instead")
    return tmp


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chunk", required=True)
    ap.add_argument("--no-fail", action="store_true")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    src = os.path.join(CHUNK_DIR, f"{args.chunk}.grantha.docx")
    if not os.path.exists(src):
        raise SystemExit(f"missing {src}; run build_chunks.py first")
    doc = docx.Document(src)

    stats: dict = {}
    for p in doc.paragraphs:
        process_paragraph(p, stats)
    for table in doc.tables:
        for p in iter_table_paragraphs(table):
            process_paragraph(p, stats, in_table=True)
    process_header_footer(doc, stats)

    checks = audit(doc)
    out = os.path.join(CHUNK_DIR, f"{args.chunk}.devanagari.docx")
    out = save_docx(doc, out)

    report = {"chunk": args.chunk, "decoder_version": M.DECODER_VERSION,
              "source": os.path.basename(src), "output": os.path.basename(out),
              "classes": stats, "audit": checks,
              "output_bytes": os.path.getsize(out)}
    print(f"{args.chunk}: {out}")
    print("  classes:", ", ".join(f"{k}={v}" for k, v in sorted(stats.items())))
    print("  audit  :", ", ".join(f"{k}={v}" for k, v in checks.items()))

    if args.json:
        os.makedirs(os.path.dirname(args.json) or ".", exist_ok=True)
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print(f"  report : {args.json}")

    hard = {k: v for k, v in checks.items()
            if k in ("legacy_bytes", "dotted_circle", "double_nasal",
                     "accent_before_virama", "accent_before_mark",
                     "orphan_mark", "latin_letters", "unknown_chars") and v}
    if hard and not args.no_fail:
        raise SystemExit(f"{args.chunk}: audit failed {hard}")


if __name__ == "__main__":
    main()
