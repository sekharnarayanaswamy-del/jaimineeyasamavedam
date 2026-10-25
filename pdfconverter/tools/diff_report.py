"""
Three-way review of a converted chunk: Grantha original, generated Devanagari,
SETHU ground truth.

The oracle is only ~85 % faithful (it prints every क्ष as ख्ष, joins or splits
words differently, and has its own typos), so a single CER number is not
actionable.  This report puts the three texts side by side, anuvaka by
anuvaka, with character-level detail inside changed words, so each difference
can be settled by eye and either fixed in the decoder or accepted as an oracle
artifact.

    python pdfconverter/tools/diff_report.py --chunk K1P1
    python pdfconverter/tools/diff_report.py --chunk K1P5   # no oracle yet

Writes `reports/<chunk>.diff.html` (self-contained, no network) and prints a
short summary plus the most frequent changed word pairs.
"""
from __future__ import annotations

import argparse
import base64
import collections
import difflib
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx  # noqa: E402
import grade_chunk as G  # noqa: E402
import ganapathy_map as M  # noqa: E402
from align_reference import normalize, segment_grantha  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_DIR = os.path.join(HERE, "reports")
FONT_PATH = os.path.join(os.path.dirname(HERE), "fonts", "GANAPATHY - GRANTHA FONT.ttf")

CSS = """
body{font-family:"Sanskrit 2020","Vijaya","Nirmala UI",system-ui,sans-serif;
     max-width:1100px;margin:2rem auto;padding:0 1rem;line-height:1.7;color:#1a1a1a}
h1{font-size:1.5rem} h2{font-size:1.05rem;margin:0 0 .4rem}
.meta{color:#666;font-size:.85rem;margin:.2rem 0 1rem}
.audit{font-family:ui-monospace,monospace;font-size:.85rem;background:#f5f5f5;padding:.7rem 1rem;border-radius:6px}
.audit .bad{color:#b00020;font-weight:600} .audit .good{color:#0a7a2f}
.anu{background:#fff;border:1px solid #e6e6e6;border-radius:6px;padding:.7rem 1rem;margin:.9rem 0}
.label{font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;color:#888;margin:.6rem 0 .1rem}
.grantha{font-family:"Ganapathy Grantha",Consolas,"Courier New",monospace;font-size:1.05rem;
         line-height:2;color:#111;background:#fafafa;border-radius:4px;padding:.35rem .5rem;
         word-break:break-word}
.grantha.bytes{font-family:Consolas,"Courier New",monospace;font-size:.72rem;line-height:1.5;color:#777}
.sethu{color:#333;background:#fcfcf5;border-radius:4px;padding:.35rem .5rem}
details{margin-top:.4rem} summary{cursor:pointer;color:#666;font-size:.8rem}
del{background:#ffe3e3;color:#8a1010;text-decoration:none;border-radius:3px;padding:0 .1em}
ins{background:#e2f7e5;color:#0a5c22;text-decoration:none;border-radius:3px;padding:0 .1em}
.legend span{margin-right:1.2rem;font-size:.9rem}
table{border-collapse:collapse;font-size:.9rem;margin-top:.4rem}
td,th{border:1px solid #ddd;padding:.25rem .6rem;text-align:left} th{background:#fafafa}
.junk{background:#fff7e6;border:1px solid #f0d9a8;border-radius:6px;padding:.7rem 1rem;margin:1rem 0}
.junk code{background:#fff;border:1px solid #eee;padding:0 .2em;border-radius:3px}
"""


def font_face() -> str:
    """Embed the legacy Grantha font so the original is readable, as printed.

    The source ``.docx`` only *looks* like Grantha because its runs use this
    font; the underlying text is 8-bit legacy bytes.  Embedding the same face
    in the report reproduces the printed page without the font being installed.
    """
    if not os.path.exists(FONT_PATH):
        return ""
    with open(FONT_PATH, "rb") as fh:
        payload = base64.b64encode(fh.read()).decode("ascii")
    return ("@font-face{font-family:'Ganapathy Grantha';"
            "src:url(data:font/ttf;base64," + payload + ") format('truetype')}")

ALLOWED_PUA = set("\uE003\uE004\uE005\uE006\uF205\uF206")


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def char_diff(ref: str, gen: str) -> str:
    """Character-level markup for one changed word pair."""
    out = []
    sm = difflib.SequenceMatcher(None, ref, gen, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            out.append(esc(ref[i1:i2]))
        elif tag == "delete":
            out.append(f"<del>{esc(ref[i1:i2])}</del>")
        elif tag == "insert":
            out.append(f"<ins>{esc(gen[j1:j2])}</ins>")
        else:
            out.append(f"<del>{esc(ref[i1:i2])}</del><ins>{esc(gen[j1:j2])}</ins>")
    return "".join(out)


def word_diff(ref_words: list[str], gen_words: list[str]) -> tuple[str, list[tuple[str, str]]]:
    """Inline word diff; returns (html, changed pairs ``(ref, gen)``)."""
    out: list[str] = []
    changed: list[tuple[str, str]] = []
    sm = difflib.SequenceMatcher(None, ref_words, gen_words, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            out.append(" ".join(esc(w) for w in ref_words[i1:i2]))
        elif tag == "replace":
            a, b = ref_words[i1:i2], gen_words[j1:j2]
            if len(a) == 1 and len(b) == 1:
                out.append(char_diff(a[0], b[0]))
                changed.append((a[0], b[0]))
            else:
                out.append(" ".join(f"<del>{esc(w)}</del>" for w in a)
                           + " "
                           + " ".join(f"<ins>{esc(w)}</ins>" for w in b))
                changed.extend(zip(a, b))
        elif tag == "delete":
            out.append(" ".join(f"<del>{esc(w)}</del>" for w in ref_words[i1:i2]))
            changed.extend((w, "") for w in ref_words[i1:i2])
        else:  # insert: generated text with no reference counterpart
            out.append(" ".join(f"<ins>{esc(w)}</ins>" for w in gen_words[j1:j2]))
            changed.extend(("", w) for w in gen_words[j1:j2])
    return " ".join(out), changed


def load_json(path: str) -> dict | None:
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def is_foreign(ch: str) -> bool:
    cp = ord(ch)
    from convert_chunk import ALLOWED_PUNCT, ALLOWED_PUA
    if ch.isspace() or ch in ALLOWED_PUNCT or ch in ALLOWED_PUA or ch.isascii():
        return False
    if 0x0900 <= cp <= 0x097F or 0xA8E0 <= cp <= 0xA8FF:
        return False
    if 0x1CD0 <= cp <= 0x1CFF or 0x0B80 <= cp <= 0x0BFF:
        return False
    return True


def foreign_report(doc) -> list[tuple[str, str]]:
    """Unmapped characters still in the output, with context.

    These are source typos (Latin-1 letters typed outside the Grantha font,
    stray Kannada signs, ...), not decoder output; they are listed so they can
    be reviewed instead of silently shipping as junk.
    """
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    texts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        from convert_chunk import iter_table_paragraphs
        texts.extend(p.text for p in iter_table_paragraphs(table))
    for text in texts:
        for i, ch in enumerate(text):
            if is_foreign(ch) and ch not in seen:
                seen.add(ch)
                found.append((ch, text[max(0, i - 20):i + 20]))
    return found


def build(chunk: str, deva_path: str | None = None) -> tuple[str, dict]:
    meta = G.chunk_meta(chunk)
    deva_path = deva_path or os.path.join(G.CHUNK_DIR, f"{chunk}.devanagari.docx")
    grantha_path = os.path.join(G.CHUNK_DIR, meta["file"])
    if not os.path.exists(deva_path):
        raise SystemExit(f"missing {deva_path}; run convert_chunk.py first")
    doc = docx.Document(deva_path)
    segments = G.segment(doc, meta["prasna"])
    grantha = segment_grantha(grantha_path) if os.path.exists(grantha_path) else {}
    oracle = G.load_oracle()
    convert = load_json(os.path.join(REPORT_DIR, f"{chunk}.convert.json"))

    changed_counter: collections.Counter[tuple[str, str]] = collections.Counter()
    blocks: list[str] = []
    stats = {"anuvakas": 0, "with_oracle": 0, "changed_pairs": 0,
             "inserted": 0, "deleted": 0}
    keys = sorted({(meta["kandam"], prasna, anu) for prasna, anu in segments})
    for key in keys:
        kandam, prasna, anuvaka = key
        stats["anuvakas"] += 1
        parts = segments.get((prasna, anuvaka), [])
        gen_words = normalize(" ".join(parts)).split()
        raw = " ".join(grantha.get(key, [])).strip()

        body = [f'<div class="anu" id="K{kandam}-P{prasna}-A{anuvaka}">'
                f'<h2>K{kandam} P{prasna} A{anuvaka}</h2>']
        body.append('<div class="label">Grantha original (as printed)</div>'
                    f'<div class="grantha">{esc(raw)}</div>'
                    '<details class="raw"><summary>raw source bytes</summary>'
                    f'<div class="grantha bytes">{esc(raw)}</div></details>')
        if key in oracle:
            stats["with_oracle"] += 1
            ref_words = normalize(oracle[key]).split()
            markup, changed = word_diff(ref_words, gen_words)
            changed_counter.update(changed)
            stats["changed_pairs"] += len(changed)
            stats["inserted"] += sum(1 for r, _ in changed if not r)
            stats["deleted"] += sum(1 for _, g in changed if not g)
            body.append(f'<div class="label">Generated — differences against SETHU '
                        f'({len(ref_words)} vs {len(gen_words)} words)</div>'
                        f'<div>{markup}</div>')
            body.append('<details><summary>SETHU ground truth</summary>'
                        f'<div class="sethu">{esc(normalize(oracle[key]))}</div></details>')
        else:
            body.append('<div class="label">Generated (no SETHU text for this anuvaka)</div>'
                        f'<div>{esc(" ".join(gen_words))}</div>')
        body.append("</div>")
        blocks.append("".join(body))

    audit_html = ""
    if convert:
        a = convert["audit"]
        gates = ["legacy_bytes", "dotted_circle", "double_nasal",
                 "accent_before_virama", "latin_letters", "unknown_chars"]
        cells = " &middot; ".join(
            f'<span class="{"bad" if a.get(k) else "good"}">{k}={a.get(k, 0)}</span>'
            for k in gates)
        audit_html = (f'<div class="audit">quality gates: {cells}<br>'
                      f'classes: {esc(", ".join(f"{k}={v}" for k, v in sorted(convert["classes"].items())))}'
                      f'</div>')

    junk_html = ""
    foreign = foreign_report(doc)
    if foreign:
        rows = "".join(
            f"<tr><td><code>U+{ord(ch):04X}</code> {esc(ch)}</td>"
            f"<td>{esc(ctx)}</td></tr>" for ch, ctx in foreign)
        junk_html = (f'<div class="junk"><strong>{len(foreign)} foreign characters</strong> '
                     f'from the source (not decoder output). Review or replace them before '
                     f'publishing:<table><tr><th>char</th><th>context</th></tr>{rows}</table></div>')

    top = "".join(
        f"<tr><td>{esc(r) or '<em>—</em>'}</td><td>{esc(g) or '<em>—</em>'}</td><td>{n}</td></tr>"
        for (r, g), n in changed_counter.most_common(30))
    summary = (f'<p>{stats["anuvakas"]} anuvakas &middot; {stats["with_oracle"]} with SETHU text '
               f'&middot; {stats["changed_pairs"]} changed word pairs '
               f'&middot; {stats["inserted"]} generated-only &middot; {stats["deleted"]} reference-only</p>'
               f'<table><tr><th>reference (SETHU)</th><th>generated</th><th>count</th></tr>{top}</table>')

    title = f"{chunk} — Grantha / generated / SETHU"
    page = (f"<!doctype html><html><head><meta charset='utf-8'><title>{esc(title)}</title>"
            f"<style>{font_face()}{CSS}</style></head><body><h1>{esc(title)}</h1>"
            f"<div class='meta'>decoder {esc(M.DECODER_VERSION)} &middot; "
            f"source {esc(meta['file'])}</div>{audit_html}{junk_html}"
            f"<p class='legend'><span><del>reference</del> only</span>"
            f"<span><ins>generated</ins> only</span>"
            f"<span>plain = identical</span></p>"
            f"<h2>Most frequent differences</h2>{summary}"
            + "".join(blocks) + "</body></html>")
    return page, stats | {"top": changed_counter.most_common(10),
                          "foreign": len(foreign)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chunk", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--open", action="store_true", help="open the report in the browser")
    ap.add_argument("--path", help="explicit .docx (default: data/chunks/<chunk>.devanagari.docx)")
    args = ap.parse_args()

    page, stats = build(args.chunk, args.path)
    out = args.out or os.path.join(REPORT_DIR, f"{args.chunk}.diff.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page)
    print(f"{args.chunk}: {stats['anuvakas']} anuvakas ({stats['with_oracle']} with SETHU), "
          f"{stats['changed_pairs']} changed word pairs "
          f"({stats['inserted']} generated-only, {stats['deleted']} reference-only), "
          f"{stats['foreign']} foreign chars")
    if stats["top"]:
        print("most frequent differences (reference -> generated):")
        for (ref, gen), count in stats["top"]:
            print(f"  {count:>3}x  {ref or '—':<20} -> {gen or '—'}")
    print(f"wrote {out}")
    if args.open:
        os.startfile(out)  # noqa: S606 - user asked for it


if __name__ == "__main__":
    main()
