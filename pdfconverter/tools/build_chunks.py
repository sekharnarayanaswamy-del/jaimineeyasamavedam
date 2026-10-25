"""
Split the cleaned Grantha source into one docx per Prasna, plus an appendix chunk.

Chunk boundaries are the encoded "हरिः परमात्मने" invocations that open every
Prasna; the padānukrama / varṇa / śākhā block that follows the last Prasna
becomes its own `APPENDIX` chunk (it is a word index, not prose, and needs
different formatting rules).

The split is done by deleting out-of-range body elements from a fresh copy of
the source, so every chunk keeps the original tables, section properties,
numbering and styles.  `manifest.json` records the source hash and the exact
block range of every chunk, so a chunk is reproducible byte-for-byte.

    python pdfconverter/tools/build_chunks.py            # build all chunks
    python pdfconverter/tools/build_chunks.py --list     # print the ranges only
    python pdfconverter/tools/build_chunks.py --chunk K1P1
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

import docx
from docx.oxml.ns import qn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from align_reference import (  # noqa: E402
    KANDAM_PATTERNS, PRASNA_PATTERNS, _num, DEVANAGARI_DIGITS,
)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(HERE, "data", "input", "1st Paadam Final-Grantha-Cleaned.docx")
CHUNK_DIR = os.path.join(HERE, "data", "chunks")

INVOCATION = "TCk,"          # हरिः — every Prasna opens with it
PADANUKRAMA = "vLY´dx6Xzd9h3A,"  # title of the appendix block
SAMAPTI = "vk3h¦"            # समाप्तिः — closes a Prasna


def sha256(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def blocks(path: str) -> list:
    """Body elements in document order: ('p', Paragraph) / ('t', Table)."""
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    doc = docx.Document(path)
    out = []
    for child in doc.element.body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            out.append(("p", Paragraph(child, doc)))
        elif tag == "tbl":
            out.append(("t", Table(child, doc)))
    return out


def find_ranges(path: str) -> list[dict]:
    """[{name, kandam, prasna, start, end}] covering the whole body in order."""
    items = blocks(path)
    texts = [b.text if t == "p" else "" for t, b in items]

    starts = [i for i, text in enumerate(texts) if INVOCATION in text]
    if not starts:
        raise SystemExit("no Prasna invocations found — source changed?")

    ranges: list[dict] = []
    for n, begin in enumerate(starts):
        end = starts[n + 1] - 1 if n + 1 < len(starts) else len(items) - 1
        head = "\n".join(texts[begin:begin + 4])
        prasna = next((p for pat, p in PRASNA_PATTERNS if pat in head), None)
        kandam = next((k for pat, k in KANDAM_PATTERNS if pat in head), 1)
        if prasna is None:
            raise SystemExit(f"cannot read Prasna number from {texts[begin]!r}")
        ranges.append({"name": f"K{kandam}P{prasna}", "kandam": kandam,
                       "prasna": prasna, "start": begin, "end": end})

    # the appendix starts after the last Prasna's closing blessing
    last = ranges[-1]
    appendix = None
    for i in range(last["start"], last["end"] + 1):
        if PADANUKRAMA in texts[i]:
            appendix = i
            break
    if appendix is None:
        raise SystemExit("appendix title not found")
    last["end"] = appendix - 1

    tail_end = len(items) - 1
    while tail_end > appendix and not texts[tail_end].strip():
        tail_end -= 1
    ranges.append({"name": "APPENDIX", "kandam": 0, "prasna": 0,
                   "start": appendix, "end": tail_end})
    return ranges


def kind_counts(items, start: int, end: int) -> dict:
    paras = tables = chars = tamil = 0
    for t, b in items[start:end + 1]:
        if t == "t":
            tables += 1
            for row in b.rows:
                for cell in row.cells:
                    chars += len(cell.text)
            continue
        paras += 1
        text = b.text
        chars += len(text)
        if any(0x0B80 <= ord(ch) <= 0x0BFF for ch in text):
            tamil += 1
    return {"paragraphs": paras, "tables": tables, "characters": chars,
            "tamil_paragraphs": tamil}


def write_chunk(ranges_entry: dict, items_meta: list, path: str) -> dict:
    start, end = ranges_entry["start"], ranges_entry["end"]
    doc = docx.Document(SOURCE)
    body = doc.element.body
    children = [c for c in body.iterchildren() if c.tag != qn("w:sectPr")]
    for i, child in enumerate(children):
        if i < start or i > end:
            body.remove(child)

    os.makedirs(CHUNK_DIR, exist_ok=True)
    out = os.path.join(CHUNK_DIR, f"{ranges_entry['name']}.grantha.docx")
    doc.save(out)

    first = last = ""
    for t, b in items_meta[start:end + 1]:
        text = (b.text if t == "p" else "").strip()
        if text:
            if not first:
                first = text
            last = text
    info = dict(ranges_entry)
    info.update(kind_counts(items_meta, start, end))
    info["file"] = os.path.basename(out)
    info["sha256"] = sha256(out)
    info["first_text"] = first[:120]
    info["last_text"] = last[:120]
    return info


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chunk", default=None, help="build only this chunk")
    ap.add_argument("--list", action="store_true", help="print ranges, build nothing")
    ap.add_argument("--source", default=SOURCE)
    args = ap.parse_args()

    ranges = find_ranges(args.source)
    items = blocks(args.source)
    if args.list:
        for r in ranges:
            info = kind_counts(items, r["start"], r["end"])
            print(f"{r['name']:<9} blocks {r['start']:>5}..{r['end']:<5} "
                  f"paras {info['paragraphs']:>4}  tables {info['tables']:>3}  "
                  f"chars {info['characters']:>7}")
        return

    selected = [r for r in ranges if args.chunk is None or r["name"] == args.chunk]
    if not selected:
        raise SystemExit(f"unknown chunk {args.chunk!r}; have {[r['name'] for r in ranges]}")

    manifest_path = os.path.join(CHUNK_DIR, "manifest.json")
    manifest = {"source": os.path.basename(args.source),
                "source_sha256": sha256(args.source),
                "block_count": len(items),
                "chunks": []}
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as fh:
            old = json.load(fh)
        if old.get("source_sha256") == manifest["source_sha256"]:
            manifest["chunks"] = old.get("chunks", [])

    for r in selected:
        info = write_chunk(r, items, args.source)
        manifest["chunks"] = [c for c in manifest["chunks"] if c["name"] != info["name"]]
        manifest["chunks"].append(info)
        print(f"{info['name']:<9} {info['file']}  {info['paragraphs']} paras, "
              f"{info['tables']} tables, {info['characters']} chars")

    order = {r["name"]: i for i, r in enumerate(ranges)}
    manifest["chunks"].sort(key=lambda c: order.get(c["name"], 999))
    os.makedirs(CHUNK_DIR, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(f"wrote {manifest_path} ({len(manifest['chunks'])} chunks)")


if __name__ == "__main__":
    main()
