"""
Render a converted chunk to PNG pages for visual inspection.

LibreOffice converts the .docx to PDF, then pypdfium2 rasterises the pages.
This is the only check that exercises real font shaping and line breaking --
the HTML review report cannot show whether Sanskrit 2020 stacks a cluster
correctly or whether a Vijaya paragraph overflows its cell.

    python pdfconverter/tools/render_pages.py --chunk K1P1
    python pdfconverter/tools/render_pages.py --chunk K1P1 --pages 1-2 --dpi 200

Writes `reports/preview/<chunk>-p<N>.png` and prints their paths.
Requires LibreOffice (`soffice` on PATH or in Program Files) and pypdfium2.
"""
from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHUNK_DIR = os.path.join(HERE, "data", "chunks")
OUT_DIR = os.path.join(HERE, "reports", "preview")

SOFFICE_CANDIDATES = [
    "soffice",
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
]


def find_soffice() -> str:
    for cand in SOFFICE_CANDIDATES:
        path = shutil.which(cand) if os.sep not in cand else cand
        if path and os.path.exists(path):
            return path
    raise SystemExit("LibreOffice not found; install it or add soffice to PATH")


def parse_pages(spec: str | None, total: int) -> list[int]:
    """``None``/``all`` -> every page, ``2`` -> [2], ``1-3`` -> [1, 2, 3]."""
    if not spec or spec == "all":
        return list(range(1, total + 1))
    pages: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = (int(x) for x in part.split("-", 1))
            pages.extend(range(lo, hi + 1))
        elif part:
            pages.append(int(part))
    return [p for p in pages if 1 <= p <= total]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chunk", required=True)
    ap.add_argument("--pages", default="all", help="'all', '3', or '1-3'")
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--out", default=OUT_DIR)
    ap.add_argument("--path", help="explicit .docx (default: data/chunks/<chunk>.devanagari.docx)")
    args = ap.parse_args()

    docx_path = args.path or os.path.join(CHUNK_DIR, f"{args.chunk}.devanagari.docx")
    if not os.path.exists(docx_path):
        raise SystemExit(f"missing {docx_path}; run convert_chunk.py first")

    import pypdfium2 as pdfium

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        proc = subprocess.run(
            [find_soffice(), "--headless", "--norestore",
             "--convert-to", "pdf", "--outdir", tmp, docx_path],
            capture_output=True, text=True)
        pdfs = glob.glob(os.path.join(tmp, "*.pdf"))
        if not pdfs:
            raise SystemExit(f"conversion to PDF failed:\n{proc.stdout}\n{proc.stderr}")
        pdf = pdfium.PdfDocument(pdfs[0])
        pages = parse_pages(args.pages, len(pdf))
        os.makedirs(args.out, exist_ok=True)
        written = []
        for number in pages:
            bitmap = pdf[number - 1].render(scale=args.dpi / 72)
            path = os.path.join(args.out, f"{args.chunk}-p{number}.png")
            bitmap.to_pil().save(path)
            written.append(path)
            print(path)
        total = len(pdf)
        pdf.close()
        print(f"{len(written)} of {total} pages from {os.path.basename(docx_path)}")


if __name__ == "__main__":
    main()
