import fitz  # PyMuPDF
import sys
import re

def verify_flow_pdf(pdf_path, max_bottom_y=565.0):
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"=== Verifying {pdf_path} ===")
    print(f"Total Pages: {total_pages}")
    
    # Text bottom safety check (safe bottom is max_bottom_y, footer rule at 569.6 pt)
    overflows = []
    top_rules = []
    orphan_headers = []
    whitespace_stats = {
        "< 20 pt (96-100% full)": 0,
        "20-50 pt (90-95% full)": 0,
        "50-100 pt (80-89% full)": 0,
        "100-150 pt (70-79% full)": 0,
        "> 150 pt (< 70% full)": 0
    }
    
    content_pages = 0
    
    for page_idx in range(total_pages):
        page_num = page_idx + 1
        page = doc[page_idx]
        
        # Check text words with exact bounding boxes
        words = page.get_text("words")
        text_bottoms = []
        has_content = False
        
        for w in words:
            # w: (x0, y0, x1, y1, word, block_no, line_no, word_no)
            text = w[4].strip()
            if not text:
                continue
            # Exclude daisy floral border ([ characters from bbding)
            if text == '[':
                continue
            # Exclude running footers (y > 565)
            if 'jaimineeyasamavedam' in text or '(v' in text:
                continue
            # Exclude running headers (y < 80)
            if w[3] < 80:
                continue
            # Exclude page numbers at bottom footer if any
            if w[1] > 568 and text.isdigit():
                continue
                
            has_content = True
            text_bottoms.append(w[3])
            
            if w[3] > max_bottom_y:
                overflows.append((page_num, w[3], text))
                    
        # Check drawings (like divider rules)
        drawings = page.get_drawings()
        for d in drawings:
            # Check horizontal lines
            if d.get("rect"):
                r = d["rect"]
                # A divider rule has small height (< 2pt) and width around 3cm (~85pt)
                if r.height < 1.5 and 70 < r.width < 100:
                    # If this rule appears at top of page before any body content (y < 120 and before text)
                    if r.y0 < 110:
                        top_rules.append((page_num, r.y0))
                        
        if has_content and page_num > 4 and page_num < total_pages - 1:
            content_pages += 1
            max_y = max(text_bottoms) if text_bottoms else 0
            free_space = max(0, 563.9 - max_y)
            if free_space < 20:
                whitespace_stats["< 20 pt (96-100% full)"] += 1
            elif free_space < 50:
                whitespace_stats["20-50 pt (90-95% full)"] += 1
            elif free_space < 100:
                whitespace_stats["50-100 pt (80-89% full)"] += 1
            elif free_space < 150:
                whitespace_stats["100-150 pt (70-79% full)"] += 1
            else:
                whitespace_stats["> 150 pt (< 70% full)"] += 1
                
    print(f"\nSafety Checks:")
    print(f"- Overflows past {max_bottom_y} pt: {len(overflows)}")
    if overflows:
        for p, y, txt in overflows[:5]:
            print(f"  Page {p}: bottom y = {y:.1f} pt: {txt}")
    print(f"- Divider rules at top of page: {len(top_rules)}")
    if top_rules:
        for p, y in top_rules:
            print(f"  Page {p}: rule at y = {y:.1f} pt")
            
    print(f"\nWhitespace Distribution across {content_pages} content pages:")
    for k, v in whitespace_stats.items():
        pct = (v / content_pages * 100) if content_pages else 0
        print(f"  {k}: {v} pages ({pct:.1f}%)")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        verify_flow_pdf(sys.argv[1], float(sys.argv[2]))
    elif len(sys.argv) > 1:
        verify_flow_pdf(sys.argv[1])
    else:
        print("Usage: python verify_flow_metrics.py <pdf_path> [max_bottom_y]")
