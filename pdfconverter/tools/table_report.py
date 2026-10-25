"""
Side-by-side review of every table: Grantha original (as printed) / generated
Devanagari.

`diff_report.py` covers running text, anuvaka by anuvaka, against SETHU.  SETHU
has no tables, so tables get their own report: for each cell the top line is the
source bytes rendered in the embedded Ganapathy face (exactly what the printed
page shows), the bottom line is what the converter produced.  Cells that still
contain foreign characters are outlined in red so they can be fixed from the
Grantha.

    python pdfconverter/tools/table_report.py                # all chunks
    python pdfconverter/tools/table_report.py --chunk K1P1

Writes `reports/tables.html` (self-contained, no network).
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
import ganapathy_map as M  # noqa: E402
from convert_chunk import unknown_chars  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_DIR = os.path.join(HERE, "reports")
CHUNK_DIR = os.path.join(HERE, "data", "chunks")
MANIFEST = os.path.join(CHUNK_DIR, "manifest.json")
FONT_PATH = os.path.join(os.path.dirname(HERE), "fonts", "GANAPATHY - GRANTHA FONT.ttf")

CSS = """
body{font-family:"Sanskrit 2020","Vijaya","Nirmala UI",system-ui,sans-serif;
     max-width:1500px;margin:2rem auto;padding:0 1rem;line-height:1.6;color:#1a1a1a}
h1{font-size:1.5rem} h2{font-size:1.1rem;margin:2rem 0 .3rem}
h3{font-size:.95rem;margin:1.4rem 0 .3rem;color:#333}
.meta{color:#666;font-size:.85rem;margin:.2rem 0 1rem}
.toc a{margin-right:1rem;font-size:.9rem}
table{border-collapse:collapse;width:100%;margin:.3rem 0 1rem;table-layout:fixed}
td{border:1px solid #d8d8d8;padding:.35rem .45rem;vertical-align:top;overflow-wrap:anywhere}
td.num{width:7rem}
.grantha{font-family:"Ganapathy Grantha",Consolas,"Courier New",monospace;
         font-size:1.15rem;line-height:1.9;color:#111;background:#fafafa;
         border-radius:3px;padding:.1rem .25rem;margin-bottom:.2rem}
.deva{font-size:.95rem;color:#0a3d62}
.bytes{font-family:Consolas,monospace;font-size:.68rem;color:#999;line-height:1.4}
.bad{outline:2px solid #c62828;outline-offset:-2px;background:#fff5f5}
.bad .deva{color:#b00020}
.flag{font-size:.68rem;color:#b00020;font-weight:600}
.legend span{margin-right:1.2rem;font-size:.9rem}
.empty{color:#bbb}
summary{cursor:pointer;color:#666;font-size:.8rem}
"""


def font_face() -> str:
    if not os.path.exists(FONT_PATH):
        return ""
    with open(FONT_PATH, "rb") as fh:
        payload = base64.b64encode(fh.read()).decode("ascii")
    return ("@font-face{font-family:'Ganapathy Grantha';"
            "src:url(data:font/ttf;base64," + payload + ") format('truetype')}")


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def tc_text(tc) -> str:
    return "".join(node.text or "" for node in tc.iter(qn("w:t")))


def table_rows(table) -> list[list[tuple[str, int]]]:
    """[(text, colspan), ...] per row, straight from the XML.

    python-docx's ``row.cells`` repeats a horizontally merged cell once per grid
    column, which makes the printed structure impossible to see; the XML keeps
    ``gridSpan`` so the review shows the same layout as the page.
    """
    rows = []
    for tr in table._tbl.findall(qn("w:tr")):
        cells = []
        for tc in tr.findall(qn("w:tc")):
            span = 1
            pr = tc.find(qn("w:tcPr"))
            if pr is not None:
                gs = pr.find(qn("w:gridSpan"))
                if gs is not None:
                    span = int(gs.get(qn("w:val")) or 1)
            cells.append((tc_text(tc), span))
        rows.append(cells)
    return rows


def render_cell(raw: str, deva: str) -> str:
    junk = unknown_chars(deva)
    classes = "bad" if junk else ""
    flag = ""
    if junk:
        sample = "".join(sorted(junk))
        flag = (f'<div class="flag">{sum(junk.values())} foreign: '
                f'{esc(" ".join(f"U+{ord(c):04X}" for c in sample))}</div>')
    grantha = (f'<div class="grantha">{esc(raw)}</div>' if raw.strip()
               else '<div class="grantha empty">—</div>')
    deva_html = (f'<div class="deva">{esc(deva)}</div>' if deva.strip()
                 else '<div class="deva empty">—</div>')
    return (f'<td class="{classes}">{grantha}{deva_html}{flag}'
            f'<div class="bytes">{esc(raw)}</div></td>')


def build(chunks: list[str]) -> tuple[str, dict]:
    blocks: list[str] = []
    toc: list[str] = []
    stats = {"tables": 0, "cells": 0, "bad_cells": 0, "chunks": []}

    for chunk in chunks:
        grantha_path = os.path.join(CHUNK_DIR, f"{chunk}.grantha.docx")
        deva_path = os.path.join(CHUNK_DIR, f"{chunk}.devanagari.docx")
        if not (os.path.exists(grantha_path) and os.path.exists(deva_path)):
            continue
        src = docx.Document(grantha_path)
        gen = docx.Document(deva_path)
        toc.append(f'<a href="#{chunk}">{chunk}</a>')
        blocks.append(f'<h2 id="{chunk}">{chunk}</h2>')
        chunk_bad = 0

        for ti, stable in enumerate(src.tables):
            if ti >= len(gen.tables):
                blocks.append(f'<p class="flag">table {ti}: missing in generated file</p>')
                continue
            gtable = gen.tables[ti]
            grows = table_rows(stable)
            drows = table_rows(gtable)
            ncols = max((sum(s for _, s in r) for r in grows), default=0)
            stats["tables"] += 1
            blocks.append(f'<h3>table {ti} — {len(grows)} rows × {ncols} cols</h3>')
            blocks.append('<table>')
            for ri, row in enumerate(grows):
                out = ['<tr>']
                drow = drows[ri] if ri < len(drows) else []
                for ci, (raw, span) in enumerate(row):
                    deva = drow[ci][0] if ci < len(drow) else ""
                    cell = render_cell(raw, deva)
                    if span > 1:
                        cell = cell.replace("<td ", f'<td colspan="{span}" ', 1)
                    if "bad" in cell:
                        stats["bad_cells"] += 1
                        chunk_bad += 1
                    stats["cells"] += 1
                    out.append(cell)
                out.append("</tr>")
                blocks.append("".join(out))
            blocks.append("</table>")
        stats["chunks"].append((chunk, chunk_bad))

    summary = "".join(
        f'<tr><td>{esc(c)}</td><td class="{"bad" if n else ""}">{n}</td></tr>'
        for c, n in stats["chunks"])
    page = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Tables — Grantha original / generated</title>"
        f"<style>{font_face()}{CSS}</style></head><body>"
        "<h1>Tables — Grantha original / generated</h1>"
        f"<div class='meta'>decoder {esc(M.DECODER_VERSION)} · "
        f"{stats['tables']} tables · {stats['cells']} cells · "
        f"{stats['bad_cells']} cells with foreign characters</div>"
        "<p class='legend'><span><b>top</b> = source bytes in the Ganapathy face "
        "(the printed page)</span><span><b>bottom</b> = generated Devanagari</span>"
        "<span>red outline = foreign character left in the output</span></p>"
        "<p class='toc'>" + "".join(toc) + "</p>"
        "<h2>Foreign characters per chunk</h2>"
        "<table style='width:auto'><tr><th>chunk</th><th>cells</th></tr>"
        + summary + "</table>"
        + "".join(blocks) + "</body></html>")
    return page, stats


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chunk", default=None)
    ap.add_argument("--out", default=os.path.join(REPORT_DIR, "tables.html"))
    args = ap.parse_args()

    if args.chunk:
        chunks = [args.chunk]
    else:
        with open(MANIFEST, encoding="utf-8") as fh:
            chunks = [c["name"] for c in json.load(fh)["chunks"]]

    page, stats = build(chunks)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page)
    print(f"{stats['tables']} tables, {stats['cells']} cells, "
          f"{stats['bad_cells']} cells with foreign characters")
    for chunk, bad in stats["chunks"]:
        print(f"  {chunk:<9} {bad}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
