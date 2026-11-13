#!/usr/bin/env python3
"""
Batch Continuous Flow PDF Generator (Section continuous flow, Supersection new page):
1. Book Color Flow -> Samhita_book_flow_Devanagari.pdf & Samhita_book_Devanagari.pdf
2. Book BW Flow    -> Samhita_book_flow_bw_Devanagari.pdf & Samhita_book_bw_Devanagari.pdf
3. A4 Color Flow   -> Samhita_flow_Devanagari.pdf & Samhita_Devanagari.pdf
4. A4 BW Flow      -> Samhita_flow_bw_Devanagari.pdf & Samhita_bw_Devanagari.pdf
"""

import sys
import shutil
import subprocess
import time
from pathlib import Path
from datetime import datetime

RUNS = [
    {
        "title": "Book Color (Continuous Flow)",
        "target": "data/corpora/samhita/05_renders/pdf/Samhita_book_flow_Devanagari.pdf",
        "alias": "data/corpora/samhita/05_renders/pdf/Samhita_book_Devanagari.pdf",
        "cmd": [sys.executable, "-X", "utf8", "src/render.py", "--type", "samhita", "--book-print", "--pdf-color-mode", "color", "--flow"]
    },
    {
        "title": "Book Black & White (Continuous Flow)",
        "target": "data/corpora/samhita/05_renders/pdf/Samhita_book_flow_bw_Devanagari.pdf",
        "alias": "data/corpora/samhita/05_renders/pdf/Samhita_book_bw_Devanagari.pdf",
        "cmd": [sys.executable, "-X", "utf8", "src/render.py", "--type", "samhita", "--book-print", "--pdf-color-mode", "bw", "--flow"]
    },
    {
        "title": "A4 Color (Continuous Flow, Symmetric 18mm)",
        "target": "data/corpora/samhita/05_renders/pdf/Samhita_flow_Devanagari.pdf",
        "alias": "data/corpora/samhita/05_renders/pdf/Samhita_Devanagari.pdf",
        "cmd": [sys.executable, "-X", "utf8", "src/render.py", "--type", "samhita", "--pdf-color-mode", "color", "--flow"]
    },
    {
        "title": "A4 Black & White (Continuous Flow, Symmetric 18mm)",
        "target": "data/corpora/samhita/05_renders/pdf/Samhita_flow_bw_Devanagari.pdf",
        "alias": "data/corpora/samhita/05_renders/pdf/Samhita_bw_Devanagari.pdf",
        "cmd": [sys.executable, "-X", "utf8", "src/render.py", "--type", "samhita", "--pdf-color-mode", "bw", "--flow"]
    },
]

def format_size(bytes_val):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"

def get_page_count(path):
    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        return len(reader.pages)
    except Exception:
        try:
            with open(path, 'rb') as f:
                d = f.read()
                return d.count(b'/Type /Page') - d.count(b'/Type /Pages')
        except Exception:
            return "N/A"

def main():
    print("=" * 75)
    print("॥ अविच्छिन्न प्रवाह (Section Flow, Supersection New Page) PDF उत्पादनम् ॥")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)

    results = []

    for idx, run in enumerate(RUNS, 1):
        print(f"\n[{idx}/4] Compiling: {run['title']}...")
        t0 = time.time()
        proc = subprocess.run(run['cmd'], capture_output=True, text=True, encoding='utf-8')
        elapsed = time.time() - t0

        tpath = Path(run['target'])
        if proc.returncode == 0 and tpath.exists():
            sz = tpath.stat().st_size
            pages = get_page_count(tpath)
            print(f"       [SUCCESS] Generated in {elapsed:.1f}s ({pages} pages, {format_size(sz)})")
            
            # Sync to alias
            apath = Path(run['alias'])
            try:
                shutil.copy2(tpath, apath)
                print(f"       [SYNC] Synced alias: {apath.name}")
            except Exception as e:
                print(f"       [WARN] Sync failed: {e}")
                
            results.append({
                "title": run['title'],
                "pages": pages,
                "size": format_size(sz),
                "elapsed": f"{elapsed:.1f}s",
                "path": str(tpath).replace('\\', '/'),
                "status": "SUCCESS"
            })
        else:
            print(f"       [FAILED] Return code: {proc.returncode}")
            if proc.stderr:
                print("--- STDERR ---", proc.stderr[-500:])
            if proc.stdout:
                print("--- STDOUT ---", proc.stdout[-500:])
            results.append({
                "title": run['title'],
                "pages": "N/A",
                "size": "N/A",
                "elapsed": f"{elapsed:.1f}s",
                "path": str(tpath).replace('\\', '/'),
                "status": "FAILED"
            })

    print("\n" + "=" * 75)
    print("॥ SUMMARY OF COMPILED CONTINUOUS FLOW PDFs ॥")
    print("=" * 75)
    for r in results:
        status_icon = "✅" if r['status'] == 'SUCCESS' else "❌"
        print(f"{status_icon} {r['title']:<40} | {r['pages']} pgs | {r['size']:<9} | {r['elapsed']:<7}")
        print(f"   Link: {r['path']}")
    print("=" * 75)

if __name__ == "__main__":
    main()
