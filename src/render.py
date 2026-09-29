"""
Unified Document Rendering Engine for Jaimineeya Samavedam Pipeline.
-------------------------------------------------------------------
Compiles JSON AST documents into publication-grade PDFs (via LuaLaTeX/XeLaTeX),
interactive standalone HTML readers, and clean Unicode plain-text exports.
"""

import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = Path(__file__).resolve().parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import argparse
import subprocess
import tempfile
import json
import urllib.parse
from requests.models import PreparedRequest
import grapheme
import platform
import jinja2

# --- Re-export all modular filters & environments ---
from src.renderers.filters.latex_filters import *
from src.renderers.filters.html_filters import *
from src.renderers.filters.text_filters import *
from src.renderers.filters.environments import (
    latex_jinja_env, html_jinja_env,
    create_latex_jinja_env, create_html_jinja_env
)

# --- Utility functions ---
from utils import (
    combine_halants, combine_ardhaksharas,
    my_encodeURL, my_format,
    replacecolon, normalize_and_trim,
    parse_mantra_for_latex, 
    sanitize_data_structure,
    get_generated_metadata,
    get_canonical_rik_id
)

# --- Output Filename Normalization ---
def normalize_output_basename(name, doc_family):
    """
    Normalizes the output base name to prevent repeating Devanagari or Malayalam strings.
    E.g.
      Samhita_kpully_Devanagari_Devanagari -> Samhita_kpully_Devanagari
      Samam_Malayalam_Samam_Malayalam      -> Samam_Malayalam_Samam
      Samam_Malayalam_Samam               -> Samam_Malayalam_Samam
      Samhita_kpully_Devanagari           -> Samhita_kpully_Devanagari
      Samhita                             -> Samhita_Devanagari
    """
    if not name:
        return doc_family
    for ext in ['.html', '.pdf', '.tex', '.txt', '.toc', '.log']:
        if name.endswith(ext):
            name = name[:-len(ext)]
            break
    while f"_{doc_family}_{doc_family}" in name:
        name = name.replace(f"_{doc_family}_{doc_family}", f"_{doc_family}")
    if name.endswith(f"_{doc_family}") and (f"_{doc_family}" in name[:-len(doc_family)-1] or name.startswith(f"{doc_family}_")):
        name = name[:-len(doc_family)-1]
    if doc_family not in name:
        name = f"{name}_{doc_family}"
    return name

# --- Core Document Generators ---
def CreatePdf(templateFileName, name, DocfamilyName, data, prayogas=None, current_os="Windows", output_mode="combined", font_family="AdishilaVedic", doc_title_sa="जैमिनीय साम संहिता", pdf_color_mode="bw", closing_mantras=None, summary_table=None, total_riks=None, total_samams=None, summary_title="संहिता सङ्ख्या", toc_level='section', has_riks=True, has_samams=True, output_dir_override=None, name_override=None, jsv_version=None, generated_at=None, kpully=False):
    data=escape_for_latex(data)
    
    outputdir="data/output"
    logdir=f"{outputdir}/logs"
    exit_code=0
    
    # Use overrides if provided
    name = normalize_output_basename(name_override or name, DocfamilyName)
    if output_dir_override:
        norm_override = str(output_dir_override).replace('\\', '/').rstrip('/')
        if norm_override.endswith('/pdf'):
            outputdir = norm_override
        elif norm_override.endswith('05_renders') or (Path(norm_override) / 'pdf').exists():
            outputdir = f"{norm_override}/pdf"
        else:
            outputdir = norm_override
    else:
        outputdir = f"{outputdir}/pdf/{DocfamilyName}"
    
    TexFileName=f"{name}.tex"
    PdfFileName=f"{name}.pdf"
    TocFileName=f"{name}.toc"
    LogFileName=f"{name}.log"
    template = templateFileName
    Path(outputdir).mkdir(parents=True, exist_ok=True)
    Path(logdir).mkdir(parents=True, exist_ok=True)
    
    if not jsv_version or not generated_at:
        from utils import get_generated_metadata, normalize_to_dd_mm_yyyy
        meta = get_generated_metadata()
        jsv_version = jsv_version or meta['version']
        generated_at = normalize_to_dd_mm_yyyy(generated_at or meta['generated_at'])
    else:
        from utils import normalize_to_dd_mm_yyyy
        generated_at = normalize_to_dd_mm_yyyy(generated_at)
    
    document = template.render(
        supersections=data, 
        os=current_os, 
        output_mode=output_mode,
        version=jsv_version,
        generated_at=generated_at,
        font_family=font_family,
        doc_title_sa=doc_title_sa,
        pdf_color_mode=pdf_color_mode,
        closing_mantras=closing_mantras or [],
        font_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts").replace("\\", "/") + "/",
        summary_table=summary_table,
        total_riks=total_riks,
        total_samams=total_samams,
        summary_title=summary_title,
        toc_level=toc_level,
        has_riks=has_riks,
        has_samams=has_samams,
        prayogas=prayogas or [],
        kpully=kpully
    )
    

    tmpdirname="."
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpfilename=f"{tmpdirname}/{TexFileName}"

        with open(tmpfilename,"w",encoding="utf-8") as f:
            f.write(document)
        
        try:
            cmd = ["xelatex", "-interaction=nonstopmode", tmpfilename]
            proc = subprocess.run(cmd, cwd=tmpdirname, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            # Step 2: run makeindex if .idx file exists to generate index (.ind)
            idx_file = Path(tmpdirname) / f"{Path(TexFileName).stem}.idx"
            if idx_file.exists() and idx_file.stat().st_size > 0:
                cmd_idx = ["makeindex", "-c", "-q", str(idx_file.name)]
                subprocess.run(cmd_idx, cwd=tmpdirname, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                
            # Step 3: Pass 2 of xelatex to resolve TOC, index, and page cross-references
            proc = subprocess.run(cmd, cwd=tmpdirname, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            if proc.returncode != 0:
                print(f"[WARNING] xelatex compilation returned non-zero code {proc.returncode}")
                lines = proc.stdout.splitlines()
                for i, line in enumerate(lines):
                    if line.startswith("!"):
                        print("\n".join(lines[i:i+4]))
        except Exception as e:
            print(f"[WARNING] Failed to run xelatex: {e}")
        
        src_pdf_file=Path(f"{tmpdirname}/{PdfFileName}")
        dst_pdf_file=Path(f"{outputdir}/{PdfFileName}")
        src_log_file=Path(f"{tmpdirname}/{LogFileName}")
        dst_log_file=Path(f"{logdir}/{LogFileName}")
        src_tex_file=Path(f"{tmpdirname}/{TexFileName}")
        dst_tex_file=Path(f"{outputdir}/{TexFileName}")
        
        import shutil
        # .tex files are transient and should not be placed into 05_renders/pdf/
        is_pdf_render_dir = "05_renders/pdf" in outputdir.replace('\\', '/') or outputdir.replace('\\', '/').endswith('/pdf')
        if not is_pdf_render_dir:
            path = Path(src_tex_file)
            if path.is_file():
                try:
                    shutil.copyfile(src_tex_file, dst_tex_file)
                except Exception as e:
                    print(f"[WARN] Could not move TeX file: {e}")
        path = Path(src_pdf_file)
        if path.is_file():
            try:
                shutil.copyfile(src_pdf_file, dst_pdf_file)
            except Exception as e:
                print(f"[WARN] Could not overwrite PDF file (may be locked in viewer): {e}")
                for suffix in ["_preview", "_preview2", "_preview3", "_new"]:
                    alt_dst = dst_pdf_file.with_name(f"{dst_pdf_file.stem}{suffix}.pdf")
                    try:
                        shutil.copyfile(src_pdf_file, alt_dst)
                        print(f"[INFO] Saved alternative preview PDF to: {alt_dst}")
                        break
                    except Exception:
                        continue
        path = Path(src_log_file)
        if path.is_file():
            try:
                shutil.copyfile(src_log_file, dst_log_file)
                src_log_file.unlink(missing_ok=True)
            except Exception as e:
                print(f"[WARN] Could not move log file: {e}")

    return exit_code

def CreateTextFile(templateFileName, name, DocfamilyName, data, output_mode="combined", doc_title_sa="जैमिनीय साम संहिता", closing_mantras=None, toc_level='section', output_dir_override=None, name_override=None, jsv_version=None, generated_at=None):
    outputdir="data/output"
    logdir="data/output/logs"
    exit_code=0
    
    # Use overrides if provided
    name = normalize_output_basename(name_override or name, DocfamilyName)
    if output_dir_override:
        norm_override = str(output_dir_override).replace('\\', '/').rstrip('/')
        if norm_override.endswith('/txt'):
            outputdir = norm_override
        elif norm_override.endswith('05_renders') or (Path(norm_override) / 'txt').exists():
            outputdir = f"{norm_override}/txt"
        else:
            outputdir = norm_override
    else:
        outputdir = f"{outputdir}/txt/{DocfamilyName}"

    TexFileName=f"{name}_Unicode.tex"
    PdfFileName=f"{name}_Unicode.pdf"
    TextFileName=f"{name}_Unicode.txt"
    TocFileName=f"{name}_Unicode.toc"
    LogFileName=f"{name}_Unicode.log"
    template = templateFileName
    Path(outputdir).mkdir(parents=True, exist_ok=True)
    Path(logdir).mkdir(parents=True, exist_ok=True)
    
    from utils import get_generated_metadata, normalize_to_dd_mm_yyyy
    meta = get_generated_metadata()
    
    document = template.render(
        supersections=data, 
        output_mode=output_mode,
        doc_title_sa=doc_title_sa,
        version=jsv_version or meta['version'],
        generated_at=normalize_to_dd_mm_yyyy(generated_at or meta['generated_at']),
        closing_mantras=closing_mantras or [],
        toc_level=toc_level
    )
    

    tmpdirname="."
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpfilename=f"{tmpdirname}/{TextFileName}"

        with open(tmpfilename,"w",encoding="utf-8") as f:
            f.write(document)
        
        src_text_file=Path(f"{tmpdirname}/{TextFileName}")
        dst_text_file=Path(f"{outputdir}/{TextFileName}")
        
        path = Path(src_text_file)
        if path.is_file():
            if dst_text_file.exists():
                dst_text_file.unlink()
            src_text_file.rename(dst_text_file)  

    return exit_code

def preprocess_html_data(supersections, output_mode='combined', script='devanagari', with_modifiers=True):
    """
    Pre-processes all subsection content for HTML template rendering.
    """
    index_entries = []
    doc_markers_map = {}
    
    for super_key, supersection in supersections.items():
        for section_key, section in supersection.get('sections', {}).items():
            if section_key == 'count': continue
            
            # --- SECTION STATE ---
            footnote_counter = 0
            footnotes_accumulator = []
            seen_content_map = {}
            
            section['html_subsections'] = [] # List of HTML strings
            
            prev_rik_id = None
            prev_rik_text = None
            
            for subsection_key, subsection in section.get('subsections', {}).items():
                unique_key = f"{super_key}_{section_key}_{subsection_key}"
                is_malayalam = (script == 'malayalam')
                
                # Dispatch based on mode
                html_content = ""
                if output_mode == 'rik':
                    html_content, footnote_counter = format_rik_only_html(
                        subsection, None, None, subsection.get('header', {}).get('header'), {}, 
                        prev_rik_id, unique_key, 
                        footnote_counter, footnotes_accumulator, seen_content_map,
                        doc_markers_map=doc_markers_map,
                        prev_rik_text=prev_rik_text
                    )
                elif output_mode == 'rik_nometa':
                    html_content, footnote_counter = format_rik_nometa_html(
                        subsection, None, None, subsection.get('header', {}).get('header'), {}, 
                        prev_rik_id, unique_key, 
                        footnote_counter, footnotes_accumulator, seen_content_map,
                        doc_markers_map=doc_markers_map,
                        prev_rik_text=prev_rik_text
                    )
                elif output_mode == 'samam':
                    if is_malayalam:
                        html_content, footnote_counter = format_malayalam_samam_html(
                            subsection, subsection.get('header', {}).get('header', ''), include_metadata=True,
                            footnote_counter=footnote_counter, footnotes_accumulator=footnotes_accumulator,
                            seen_content_map=seen_content_map, subsection_key=unique_key,
                            doc_markers_map=doc_markers_map
                        )
                    else:
                        html_content, footnote_counter = format_samam_only_html(
                            subsection, None, None, subsection.get('header', {}).get('header'), {}, 
                            prev_rik_id, unique_key, 
                            footnote_counter, footnotes_accumulator, seen_content_map,
                            with_modifiers=with_modifiers, doc_markers_map=doc_markers_map
                        )
                elif output_mode == 'samam_nometa':
                    if is_malayalam:
                        html_content, footnote_counter = format_malayalam_samam_html(
                            subsection, subsection.get('header', {}).get('header', ''), include_metadata=False,
                            footnote_counter=footnote_counter, footnotes_accumulator=footnotes_accumulator,
                            seen_content_map=seen_content_map, subsection_key=unique_key,
                            doc_markers_map=doc_markers_map
                        )
                    else:
                        html_content, footnote_counter = format_samam_nometa_html(
                            subsection, None, None, subsection.get('header', {}).get('header'), {}, 
                            prev_rik_id, unique_key, 
                            footnote_counter, footnotes_accumulator, seen_content_map,
                            with_modifiers=with_modifiers, doc_markers_map=doc_markers_map
                        )
                else:
                    if is_malayalam:
                        r_html = ""
                        if subsection.get('rik_text') or subsection.get('rik_metadata'):
                            r_html, footnote_counter = format_rik_only_html(
                                subsection, None, None, subsection.get('header', {}).get('header'), {}, 
                                prev_rik_id, unique_key, 
                                footnote_counter, footnotes_accumulator, seen_content_map,
                                doc_markers_map=doc_markers_map
                            )
                        s_html, footnote_counter = format_malayalam_samam_html(
                            subsection, subsection.get('header', {}).get('header', ''), include_metadata=True,
                            footnote_counter=footnote_counter, footnotes_accumulator=footnotes_accumulator,
                            seen_content_map=seen_content_map, subsection_key=unique_key,
                            doc_markers_map=doc_markers_map
                        )
                        html_content = f"{r_html}\n{s_html}" if r_html else s_html
                    else:
                        html_content, footnote_counter = format_mantra_sets_html(
                            subsection, None, None, subsection.get('header', {}).get('header'), {}, 
                            prev_rik_id, unique_key, 
                            footnote_counter, footnotes_accumulator, seen_content_map,
                            with_modifiers=with_modifiers, doc_markers_map=doc_markers_map
                        )
                
                # INDEX COLLECT
                header = subsection.get('header', {}).get('header', '')
                if header and (output_mode not in ('rik', 'rik_nometa') or html_content):
                    # Consistent logic with PDF: strip dandas and spaces
                    index_title = re.sub(r'[|॥]', '', header).strip()
                    if index_title:
                        # Append to list; we'll deduplicate by adding disambiguation if needed
                        index_entries.append({
                            'title': index_title,
                            'anchor': f"{super_key}-{section_key}-{subsection_key}"
                        })

                if output_mode not in ('rik', 'rik_nometa') or html_content:
                    section['html_subsections'].append({
                        'id': f"{super_key}-{section_key}-{subsection_key}",
                        'content': html_content
                    })
                
                prev_rik_id = subsection.get('rik_id')
                if subsection.get('rik_text'):
                    prev_rik_text = subsection.get('rik_text')
                
            # --- GENERATE FOOTNOTE HTML ---
            # Using the logic from render_section_footnotes but locally
            if footnotes_accumulator:
                 output = ['<hr class="footnote-separator"/>']
                 output.append('<div class="footnote-section">')
                 for unique_id, display_num, text in footnotes_accumulator:
                     output.append(f'<div class="footnote-item" id="{unique_id}"><sup class="footnote-ref">{display_num}</sup> {text}</div>')
                 output.append('</div>')
                 section['html_footer'] = '\n'.join(output)
            else:
                 section['html_footer'] = ""

    # Deduplicate and sort index alphabetically
    # To properly sort devanagari we can just use python sorted, it works decently.
    # Group by title to remove duplicates pointing to different anchors (or keep them?)
    # Usually index groups by title and lists pages. For HTML we'll just link to the first occurrence
    unique_index = {}
    title_counts = {}
    
    # Sort by anchor to maintain document order before deduplication/suffixing
    index_entries.sort(key=lambda x: x['anchor'])
    
    for entry in index_entries:
        title = entry['title']
        if title in unique_index:
            # Duplicate title found! Add a numeric suffix to make it unique in the index
            title_counts[title] = title_counts.get(title, 1) + 1
            unique_title = f"{title} ({title_counts[title]})"
            unique_index[unique_title] = entry['anchor']
        else:
            unique_index[title] = entry['anchor']
            title_counts[title] = 1
            
    # Sorted list for template
    sorted_index = []
    for title in sorted(unique_index.keys()):
        sorted_index.append({
            'title': title,
            'anchor': unique_index[title]
        })
    
    return sorted_index

def CreateHtmlFile(templateFileName, name, DocfamilyName, data, html_font="'AdishilaVedic', 'AdishilaSanVedic'", output_mode="combined", doc_title_sa="जैमिनीय साम संहिता", closing_mantras=None, summary_table=None, total_riks=None, total_samams=None, summary_title="संहिता सङ्ख्या", toc_level='section', has_riks=True, has_samams=True, output_dir_override=None, name_override=None, jsv_version=None, generated_at=None, script='devanagari', with_modifiers=True, kpully=False):
    """
    Creates an HTML file from the template and data.
    Similar to CreatePdf but outputs HTML instead.
    
    Args:
        html_font: Font family string for HTML output (e.g., "'AdishilaVedic', 'AdishilaSanVedic'")
        output_mode: 'combined', 'rik', or 'samam' for filtering content
        doc_title_sa: Sanskrit title for the document
        closing_mantras: List of closing mantra lines to render at the end
    """
    outputdir = "data/output"
    exit_code = 0
    
    # Malayalam script mode has no HTML template yet; skip gracefully
    if templateFileName is None:
        return
    
    # Use overrides if provided
    name = normalize_output_basename(name_override or name, DocfamilyName)
    if output_dir_override:
        norm_override = str(output_dir_override).replace('\\', '/').rstrip('/')
        if norm_override.endswith('/html'):
            outputdir = norm_override
        elif norm_override.endswith('05_renders') or (Path(norm_override) / 'html').exists():
            outputdir = f"{norm_override}/html"
        else:
            outputdir = norm_override
    else:
        outputdir = f"{outputdir}/html/{DocfamilyName}"
    
    HtmlFileName = f"{name}.html"
    template = templateFileName
    Path(outputdir).mkdir(parents=True, exist_ok=True)
    
    global HTML_FOOTNOTE_COUNTER
    HTML_FOOTNOTE_COUNTER = 0 # Not used in pre-process mode but kept for safety
    
    # PRE-PROCESS DATA

    html_index = preprocess_html_data(data, output_mode, script=script, with_modifiers=with_modifiers)
    
    if not jsv_version or not generated_at:
        from utils import get_generated_metadata, normalize_to_dd_mm_yyyy
        meta = get_generated_metadata()
        jsv_version = jsv_version or meta['version']
        generated_at = normalize_to_dd_mm_yyyy(generated_at or meta['generated_at'])
    else:
        from utils import normalize_to_dd_mm_yyyy
        generated_at = normalize_to_dd_mm_yyyy(generated_at)
    
    import base64
    jaimineeya_swara_b64 = ""
    font_file = Path("fonts/JaimineeyaSwara.ttf")
    if font_file.exists():
        with open(font_file, "rb") as f_font:
            jaimineeya_swara_b64 = base64.b64encode(f_font.read()).decode("ascii")
    
    adishila_vedic_b64 = ""
    adishila_file = Path("fonts/AdishilaVedic.ttf")
    if adishila_file.exists():
        with open(adishila_file, "rb") as f_font:
            adishila_vedic_b64 = base64.b64encode(f_font.read()).decode("ascii")
    
    adishila_vedic_bold_b64 = ""
    adishila_bold_file = Path("fonts/AdishilaVedicBold.ttf")
    if adishila_bold_file.exists():
        with open(adishila_bold_file, "rb") as f_font:
            adishila_vedic_bold_b64 = base64.b64encode(f_font.read()).decode("ascii")

    rachana_regular_b64 = ""
    rachana_reg_file = Path("fonts/RIT-Rachana-Regular.woff2")
    if rachana_reg_file.exists():
        with open(rachana_reg_file, "rb") as f_font:
            rachana_regular_b64 = base64.b64encode(f_font.read()).decode("ascii")

    rachana_bold_b64 = ""
    rachana_bld_file = Path("fonts/RIT-Rachana-Bold.woff2")
    if rachana_bld_file.exists():
        with open(rachana_bld_file, "rb") as f_font:
            rachana_bold_b64 = base64.b64encode(f_font.read()).decode("ascii")
    
    document = template.render(
        supersections=data, 
        html_font=html_font, 
        output_mode=output_mode,
        doc_title_sa=doc_title_sa,
        version=jsv_version,
        generated_at=generated_at,
        html_index=html_index,
        closing_mantras=closing_mantras or [],
        summary_table=summary_table,
        total_riks=total_riks,
        total_samams=total_samams,
        summary_title=summary_title,
        toc_level=toc_level,
        has_riks=has_riks,
        has_samams=has_samams,
        jaimineeya_swara_b64=jaimineeya_swara_b64,
        adishila_vedic_b64=adishila_vedic_b64,
        adishila_vedic_bold_b64=adishila_vedic_bold_b64,
        rachana_regular_b64=rachana_regular_b64,
        rachana_bold_b64=rachana_bold_b64,
        kpully=kpully
    )
    
    output_path = Path(f"{outputdir}/{HtmlFileName}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(document)
    
    print(f"HTML file created: {output_path}")
    


    return exit_code

# --- Unified Rendering CLI Entrypoint ---
def main():
    # Force UTF-8 encoding for console output
    if sys.stdout.encoding.lower() != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    


    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Generate PDF, HTML, and Text from Vedic text JSON',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Output Modes:
  combined  - Single output with both Rik and Samam content (default)
  separate  - Two separate outputs: Rik-only and Samam-only (with metadata)
  nometa    - Two separate outputs: Rik-only and Samam-only (without metadata)

Examples:
  python renderPDF.py input.json
  python renderPDF.py input.json --output-mode separate
  python renderPDF.py input.json --output-mode nometa
        """
    )
    parser.add_argument('input_file', nargs='?', default=None,
                        help='Input JSON file (auto-selected based on --type if not specified)')
    parser.add_argument('--output-mode', dest='output_mode',
                        choices=['combined', 'separate', 'nometa'], default=None,
                        help='Output mode: combined (default), separate, or nometa')
    parser.add_argument('--pdf-font', dest='pdf_font', default=None,
                        help='Font for PDF output')
    parser.add_argument('--html-font', dest='html_font', default=None,
                        help="Font for HTML output")
    parser.add_argument('--type', choices=['samhita', 'aaranam', 'collection'], default='samhita',
                        help='Type of Samaveda text: samhita, aaranam, or collection')
    
    parser.add_argument('--script', dest='script',
                        choices=['devanagari', 'malayalam'], default='devanagari',
                        help='Rendering script: devanagari (default) or malayalam (Phase 1 Samam-only pilot)')
    
    # CLI OPTION for Swara Modifiers in Devanagari
    parser.add_argument('--swara-modifiers', dest='swara_modifiers', action='store_true', default=True,
                        help='Include swara modifiers in Devanagari (default: True)')
    parser.add_argument('--no-swara-modifiers', dest='swara_modifiers', action='store_false',
                        help='Exclude swara modifiers in Devanagari')
    
    # CLI OPTION for Kodunthirapully variant (swaras above mantra text)
    parser.add_argument('-kpully', '--kpully', dest='kpully', action='store_true', default=False,
                        help='Render Devanagari with swara markings stacked above the mantra text (Kodunthirapully paddhati)')
    

    
    # Color Mode Option (Defaults to color for rich Vedic rendering)
    parser.add_argument('--pdf-color-mode', dest='pdf_color_mode',
                        choices=['bw', 'color'], default='color',
                        help='Color mode for PDF output: color (default) or bw')
                        
    parser.add_argument('--toc-level', dest='toc_level',
                        choices=['section', 'subsection', 'both'], default=None,
                        help='Determines which headers appear in the TOC.')
    
    parser.add_argument('--title', dest='title', default=None,
                        help='Custom Sanskrit title for the document.')
    
    parser.add_argument('--output', '-o', dest='output', default=None,
                        help='Override the default output basename or specify a full output path.')
    
    # Target format filters
    parser.add_argument('--html-only', dest='html_only', action='store_true', default=False,
                        help='Generate only HTML output (skips PDF and text generation)')
    parser.add_argument('--legacy-html', dest='legacy_html', action='store_true', default=False,
                        help='Use legacy single-page HTML layout instead of modern VedaVMS reader layout')
    parser.add_argument('--pdf-only', dest='pdf_only', action='store_true', default=False,
                        help='Generate only PDF output (skips HTML and text generation)')
    parser.add_argument('--txt-only', dest='txt_only', action='store_true', default=False,
                        help='Generate only Text output (skips PDF and HTML generation)')
    parser.add_argument('--samam-only', dest='samam_only', action='store_true', default=False,
                        help='Generate only Samam output (skips Rik output in separate/nometa modes)')
    parser.add_argument('--rik-only', dest='rik_only', action='store_true', default=False,
                        help='Generate only Rik output (skips Samam output in separate/nometa modes)')
    parser.add_argument('--no-pdf', dest='no_pdf', action='store_true', default=False,
                        help='Skip PDF compilation (generates HTML and text outputs)')
    parser.add_argument('--output-dir', dest='output_dir', default=None,
                        help='Base output directory for generated renders (e.g. data/corpora/samhita/05_renders)')
    
    args = parser.parse_args()
    mode_type = args.type

    # Priority Merging: CLI > Hardcoded defaults
    output_mode = args.output_mode or 'combined'
    pdf_font = args.pdf_font or 'AdishilaVedic'
    html_font = args.html_font or "'AdishilaVedic', 'AdishilaSanVedic'"
    pdf_color_mode = args.pdf_color_mode or 'color'
    toc_level = args.toc_level or 'section'
    kpully_mode = args.kpully
    
    global CURRENT_PDF_FONT
    CURRENT_PDF_FONT = pdf_font
    set_current_pdf_font(pdf_font)
    global CURRENT_TOC_LEVEL
    CURRENT_TOC_LEVEL = toc_level
    global CURRENT_WITH_SWARA_MODIFIERS
    CURRENT_WITH_SWARA_MODIFIERS = args.swara_modifiers
    global CURRENT_KPULLY_MODE
    CURRENT_KPULLY_MODE = kpully_mode
    
    # Target format dispatch flags
    gen_pdf = not (args.html_only or args.txt_only or args.no_pdf)
    gen_txt = not (args.html_only or args.pdf_only)
    gen_html = not (args.pdf_only or args.txt_only)
    gen_rik = not args.samam_only
    gen_samam = not args.rik_only
    
    # Handle output path overrides:
    # Priority: explicit --output-dir > stage-numbered corpus renders > legacy data/output
    corpus_map = {'samhita': 'samhita', 'aaranam': 'aaranam', 'collection': 'collections'}
    default_corpus = corpus_map.get(mode_type, 'samhita')
    candidate_corpus_renders = ROOT_DIR / "data" / "corpora" / default_corpus / "05_renders"

    out_dir = args.output_dir or (str(candidate_corpus_renders) if candidate_corpus_renders.exists() else None)
    out_name = None
    html_out_dir = None
    html_out_name = None
    if args.output:
        out_path = Path(args.output)
        if args.output.endswith('/') or args.output.endswith('\\') or out_path.is_dir():
            out_dir = str(out_path)
            out_name = None
        else:
            if out_path.parent != Path('.'):
                out_dir = str(out_path.parent)
            out_name = out_path.name
    
    # Auto-select default input file
    input_file = args.input_file
    if not input_file:
         # Fallback to historical hardcoded defaults
         if mode_type == 'aaranam':
             input_file = 'data/output/Aaranam_latest_out.json'
         elif mode_type == 'collection':
             input_file = 'data/output/Collection_latest_out.json'
         else:
             input_file = 'data/output/Samhita_corrected_out.json'
    
    file_prefix = (
        "Aaranam" if mode_type == 'aaranam' else 
        "Collection" if mode_type == 'collection' else "Samhita"
    )
    if kpully_mode and not args.output and not out_name:
        file_prefix = f"{file_prefix}_kpully"

    # Path configuration
    template_dir = "templates/pdf"
    text_template_dir = "templates/text"
    html_template_dir = "templates/html"
    
    templateFile_Grantha = f"{template_dir}/Grantha_main.template"
    templateFile_Devanagari = f"{template_dir}/Devanagari_main.template"
    templateFile_Tamil = f"{template_dir}/Tamil_main.template"
    templateFile_Malayalam = f"{template_dir}/Malayalam_main.template"
    
    text_templateFile_Devanagari = f"{text_template_dir}/Devanagari_main.template"
    if getattr(args, 'legacy_html', False):
        html_templateFile_Devanagari = f"{html_template_dir}/Devanagari_main_html_legacy.template"
    else:
        html_templateFile_Devanagari = f"{html_template_dir}/Devanagari_main_html.template"

    outputdir = "data/output"
    logdir = "data/output/logs"
    
    # LaTeX/Text Jinja environment (uses LaTeX-style delimiters)
    latex_jinja_env = jinja2.Environment(
    block_start_string = r'\BLOCK{',
    block_end_string = '}',
    variable_start_string = r'\VAR{',
    variable_end_string = '}',
    comment_start_string = r'\#{',
    comment_end_string = '}',
    line_statement_prefix = '%-',
    line_comment_prefix = '%#',
    trim_blocks = True,
    lstrip_blocks=True,
    autoescape = False,
    loader = jinja2.FileSystemLoader(os.path.abspath('.')),
    extensions=['jinja2.ext.loopcontrols']
    )
    latex_jinja_env.filters["my_encodeURL"] = my_encodeURL
    latex_jinja_env.filters["escape_for_latex"] = escape_for_latex
    latex_jinja_env.filters["replace_footnotes"] = replace_footnote_markers_filter
    latex_jinja_env.filters["format_mantra_sets_text"] = format_mantra_sets_text
    latex_jinja_env.filters["format_mantra_sets"] = format_mantra_sets
    latex_jinja_env.filters["format_rik_only"] = format_rik_only
    latex_jinja_env.filters["format_samam_only"] = format_samam_only
    latex_jinja_env.filters["format_rik_only_text"] = format_rik_only_text
    latex_jinja_env.filters["format_samam_only_text"] = format_samam_only_text
    latex_jinja_env.filters["format_rik_nometa"] = format_rik_nometa
    latex_jinja_env.filters["format_samam_nometa"] = format_samam_nometa
    latex_jinja_env.filters["format_rik_nometa_text"] = format_rik_nometa_text
    latex_jinja_env.filters["format_malayalam_rik_only"] = format_malayalam_rik_only
    latex_jinja_env.filters["format_malayalam_rik_nometa"] = format_malayalam_rik_nometa
    latex_jinja_env.filters["format_malayalam_samam_only"] = format_malayalam_samam_only
    latex_jinja_env.filters["format_malayalam_samam_nometa"] = format_malayalam_samam_nometa
    latex_jinja_env.filters["format_malayalam_combined"] = format_malayalam_combined
    latex_jinja_env.filters["format_malayalam_samam"] = format_malayalam_samam
    latex_jinja_env.filters["format_malayalam_samam_text"] = format_malayalam_samam_text
    latex_jinja_env.filters["format_samam_nometa_text"] = format_samam_nometa_text
    latex_jinja_env.filters["split_rik_lines"] = split_rik_lines_text
    latex_jinja_env.filters["replacecolon"] = replacecolon
    latex_jinja_env.filters["clean_toc_title"] = clean_toc_title
    latex_jinja_env.filters["get_canonical_rik_id"] = get_canonical_rik_id
    
    # HTML Jinja environment (uses same LaTeX-style delimiters for consistency)
    html_jinja_env = jinja2.Environment(
    block_start_string = r'\BLOCK{',
    block_end_string = '}',
    variable_start_string = r'\VAR{',
    variable_end_string = '}',
    comment_start_string = r'\#{',
    comment_end_string = '}',
    line_statement_prefix = '%-',
    line_comment_prefix = '%#',
    trim_blocks = True,
    lstrip_blocks=True,
    autoescape = False,
    loader = jinja2.FileSystemLoader(os.path.abspath('.')),
    extensions=['jinja2.ext.loopcontrols']
    )
    html_jinja_env.filters["get_canonical_rik_id"] = get_canonical_rik_id
    html_jinja_env.filters["format_mantra_sets_html"] = format_mantra_sets_html
    html_jinja_env.filters["format_rik_only_html"] = format_rik_only_html
    html_jinja_env.filters["format_samam_only_html"] = format_samam_only_html
    html_jinja_env.filters["format_rik_nometa_html"] = format_rik_nometa_html
    html_jinja_env.filters["format_samam_nometa_html"] = format_samam_nometa_html
    html_jinja_env.filters["escape_for_html"] = escape_for_html
    html_jinja_env.filters["replacecolon"] = replacecolon
    html_jinja_env.filters["reset_html_footnote_counter"] = reset_html_footnote_counter
    html_jinja_env.filters["render_section_footnotes"] = render_section_footnotes
    html_jinja_env.filters["clean_toc_title"] = clean_toc_title

    # Load input data (JSON only)
    ts_string_Devanagari = Path(input_file).read_text(encoding="utf-8")
    data_Devanagari = json.loads(ts_string_Devanagari)
    meta = data_Devanagari.get('meta', {})
    jsv_version = meta.get('version')
    generated_at = get_generated_metadata()['generated_at']
    if jsv_version:
        print(f"[INFO] Using cascading Version {jsv_version} (Final Generation: {generated_at})")
    
    # --- MALAYALAM SCRIPT MODE (Phase 1 Samam-only pilot) ---
    script = args.script
    if script == 'malayalam':
        from malayalam.ml_text import transform_ast
        from malayalam.ml_transliterate import devanagari_to_malayalam
        data_Devanagari, ml_warnings, ml_stats = transform_ast(data_Devanagari)
        print(f"[INFO] Malayalam script mode: Full Samhita "
              f"({ml_stats['marked_words']} marked words, {len(ml_warnings)} warnings)")
        # Transliterate supersection and section titles to Malayalam
        for ss_key, ss_data in data_Devanagari.get('supersection', {}).items():
            if ss_data.get('supersection_title'):
                try:
                    ss_data['supersection_title'] = devanagari_to_malayalam(ss_data['supersection_title'])
                except Exception:
                    pass
            for sec_key, sec_data in ss_data.get('sections', {}).items():
                if sec_key != 'count' and sec_data.get('section_title'):
                    try:
                        sec_data['section_title'] = devanagari_to_malayalam(sec_data['section_title'])
                    except Exception:
                        pass

    supersections = data_Devanagari.get('supersections', data_Devanagari.get('supersection', {}))
    supersections = sanitize_data_structure(supersections)
    closing_mantras = data_Devanagari.get('closing-mantras', data_Devanagari.get('closing_mantras', []))
    
    # Generate Summary Table
    summary_table = []
    total_riks = 0
    total_samams = 0
    
    for ss_key, ss_data in supersections.items():
        if ss_key == 'count': continue
        patha_name = ss_data.get('supersection_title', ss_key).replace('॥', '').strip()
        patha_riks = 0
        patha_samams = 0
        khanda_rows = []
        for sec_key, sec_data in ss_data.get('sections', {}).items():
            if sec_key == 'count': continue
            khanda_name = sec_data.get('section_title', sec_key).replace('॥', '').replace(':', 'ः').strip()
            
            seen_riks = set()
            samam_count = 0
            
            # Smart count: only count if displayable text exists
            baraha_verse_count = 0
            for sub_key, sub_data in sec_data.get('subsections', {}).items():
                if 'content_lines' in sub_data:
                    baraha_verse_count += len(sub_data['content_lines'])
                rik_text = sub_data.get('rik_text', '').strip()
                rik_ids = sub_data.get('rik_ids', [])
                
                # Only count Rik if there is Rik text to display
                if rik_text:
                    if rik_ids:
                        seen_riks.update(rik_ids)
                    else:
                        r_id = sub_data.get('rik_id')
                        if r_id is not None:
                            seen_riks.add(r_id)
                
                # Samam count logic
                sub_samam_count = 0
                has_samam_text = False
                for ms in sub_data.get('corrected-mantra_sets', []):
                    mantra = ms.get('corrected-mantra', '')
                    if mantra.strip():
                        has_samam_text = True
                    # Count all ॥ N ॥ markers
                    m_markers = re.findall(r'॥\s*[०-९\d]+\s*॥', mantra)
                    if m_markers:
                        sub_samam_count += len(m_markers)
                
                # If no markers found but mantra sets exist, count as 1 if there's text
                if sub_samam_count == 0 and has_samam_text:
                    sub_samam_count = 1
                
                samam_count += sub_samam_count
                    
            # Total aggregation format for section headers
            sec_riks = len(seen_riks)
            if baraha_verse_count > 0:
                samam_count = baraha_verse_count
            
            # Summary table row generation
            if sec_riks > 0 or samam_count > 0:
                if khanda_name:
                    khanda_rows.append({
                        'khanda': khanda_name,
                        'id': f"{ss_key}-{sec_key}",
                        'riks': str(sec_riks) if script == 'malayalam' else to_devanagari_numeral(sec_riks),
                        'samams': str(samam_count) if script == 'malayalam' else to_devanagari_numeral(samam_count)
                    })
                patha_riks += sec_riks
                patha_samams += samam_count
                total_riks += sec_riks
                total_samams += samam_count

            count_parts = []
            if script == 'malayalam':
                if sec_riks > 0 and samam_count > 0:
                    count_parts.append(f"ഋ-{sec_riks}")
                    count_parts.append(f"സാ-{samam_count}")
                elif sec_riks > 0:
                    count_parts.append(str(sec_riks))
                elif samam_count > 0:
                    count_parts.append(str(samam_count))
                else:
                    count_parts.append("0")
            else:
                if sec_riks > 0 and samam_count > 0:
                    count_parts.append(f"ऋ-{to_devanagari_numeral(sec_riks)}")
                    count_parts.append(f"सा-{to_devanagari_numeral(samam_count)}")
                elif sec_riks > 0:
                    count_parts.append(to_devanagari_numeral(sec_riks))
                elif samam_count > 0:
                    count_parts.append(to_devanagari_numeral(samam_count))
                else:
                    count_parts.append("०")
            
            sec_data['Count'] = ", ".join(count_parts) if khanda_name else ""
        
        # Add total count for the supersection using similar combined logic
        ss_count_parts = []
        if script == 'malayalam':
            if patha_riks > 0 and patha_samams > 0:
                ss_count_parts.append(f"ഋ-{patha_riks}")
                ss_count_parts.append(f"സാ-{patha_samams}")
            elif patha_riks > 0:
                ss_count_parts.append(str(patha_riks))
            else:
                ss_count_parts.append(str(patha_samams))
        else:
            if patha_riks > 0 and patha_samams > 0:
                ss_count_parts.append(f"ऋ-{to_devanagari_numeral(patha_riks)}")
                ss_count_parts.append(f"सा-{to_devanagari_numeral(patha_samams)}")
            elif patha_riks > 0:
                ss_count_parts.append(to_devanagari_numeral(patha_riks))
            else:
                ss_count_parts.append(to_devanagari_numeral(patha_samams))
            
        ss_data['Count'] = ", ".join(ss_count_parts)
        
        if khanda_rows:
            summary_table.append({
                'patha': patha_name,
                'id': ss_key,
                'patha_riks': str(patha_riks) if script == 'malayalam' else to_devanagari_numeral(patha_riks),
                'patha_samams': str(patha_samams) if script == 'malayalam' else to_devanagari_numeral(patha_samams),
                'khandas': khanda_rows
            })
                
    total_riks_dev = str(total_riks) if script == 'malayalam' else to_devanagari_numeral(total_riks)
    total_samams_dev = str(total_samams) if script == 'malayalam' else to_devanagari_numeral(total_samams)
    
    # Define Sanskrit title based on type (for PDF/html generation)
    # Priority: CLI > JSON Meta title (if Sanskrit/Devanagari) > Config Type default > Hardcoded default
    doc_title_sa = args.title
    if not doc_title_sa:
        meta_title = data_Devanagari.get('meta', {}).get('title', '')
        # Use meta.title only if it contains Devanagari script (i.e., a proper Sanskrit title)
        if meta_title and any('\u0900' <= ch <= '\u097F' for ch in meta_title):
            doc_title_sa = meta_title
    if not doc_title_sa:
        if mode_type == 'aaranam':
            doc_title_sa = "जैमिनीय साम आरण्य गानम्"
            summary_title_sa = "आरण्यम् सङ्ख्या"
        elif mode_type == 'collection':
            doc_title_sa = "जैमिनीय साम सूक्त माला"
            summary_title_sa = "सूक्तम् सङ्ख्या"
        else:
            doc_title_sa = "जैमिनीय साम संहिता"
            summary_title_sa = "संहिता सङ्ख्या"
    else:
        if mode_type == 'aaranam':
            summary_title_sa = "आरण्यम् सङ्ख्या"
        elif mode_type == 'collection':
            summary_title_sa = "सूक्तम् सङ्ख्या"
        else:
            summary_title_sa = "संहिता सङ्ख्या"
    
    current_os = platform.system()

    deva_doc_title_sa = doc_title_sa

    # Malayalam script: transliterate the title on the title page and summary table title
    if script == 'malayalam':
        from malayalam.ml_transliterate import devanagari_to_malayalam
        if doc_title_sa:
            try:
                doc_title_sa = devanagari_to_malayalam(doc_title_sa)
            except Exception:
                pass
        if summary_title_sa:
            try:
                summary_title_sa = devanagari_to_malayalam(summary_title_sa)
            except Exception:
                pass
        else:
            summary_title_sa = "സംഹിതാ സംഖ്യ"
    
    print(f"Processing {input_file} in '{output_mode}' mode...")
    print(f"Document Title: {doc_title_sa}")
    
    # Procedures are loaded from JSON's procedure_ref field (injected by generate_json.py --procedures)
    # No backward compatibility with prayoga_index.yaml
    prayoga_dir = Path("data/input/prayoga")
    procedures = {}
    
    for super_key, supersection in supersections.items():
        for section_key, section in supersection.get('sections', {}).items():
            if section_key == 'count': continue
            for subsection_key, subsection in section.get('subsections', {}).items():
                # Only include procedures that are explicitly referenced in the JSON
                if subsection.get('procedure_ref'):
                    procedure_ref = subsection['procedure_ref']
                    file_path = procedure_ref.get('file', '')
                    if file_path and file_path not in procedures:
                        full_md_path = prayoga_dir / file_path
                        if full_md_path.exists():
                            with open(full_md_path, 'r', encoding='utf-8') as f:
                                md_content = f.read()
                            if md_content.startswith('---'):
                                parts = md_content.split('---', 2)
                                if len(parts) >= 3:
                                    md_content = parts[2].strip()
                            latex_content = md_content.replace('_', '\\_').replace('&', '\\&').replace('%', '\\%').replace('$', '\\$')
                            latex_content = re.sub(r'(?m)^### (.*?)$', r'\\subsubsection*{\1}', latex_content)
                            latex_content = re.sub(r'(?m)^## (.*?)$', r'\\subsection*{\1}', latex_content)
                            latex_content = re.sub(r'(?m)^# (.*?)$', r'\\section*{\1}', latex_content)
                            latex_content = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', latex_content)
                            latex_content = re.sub(r'\*(.*?)\*', r'\\textit{\1}', latex_content)
                            latex_content = re.sub(r'(?m)^- (.*?)$', r'$\\bullet$ \1\n\n', latex_content)
                            
                            procedures[file_path] = {
                                'slug': Path(file_path).stem,
                                'title': procedure_ref.get('title', 'विधिः'),
                                'latex_content': latex_content
                            }
    
    prayogas_list = list(procedures.values())

    doc_family = 'Malayalam' if script == 'malayalam' else 'Devanagari'

    # Template selection (Malayalam script uses its own Samam-only templates)
    if script == 'malayalam':
        template_file_src = templateFile_Malayalam
        text_template_file_src = f"{text_template_dir}/Malayalam_main.template"
        if getattr(args, 'legacy_html', False):
            html_template_file_src = f"{html_template_dir}/Malayalam_main_html_legacy.template"
        else:
            html_template_file_src = f"{html_template_dir}/Malayalam_main_html.template"
        pdf_font = "NotoSerifMalayalam"
        html_font = "Noto Serif Malayalam"
    else:
        template_file_src = templateFile_Devanagari
        text_template_file_src = text_templateFile_Devanagari
        html_template_file_src = html_templateFile_Devanagari

    # Dual text generation helper for Malayalam script mode
    deva_text_template_file = latex_jinja_env.get_template(text_templateFile_Devanagari) if script == 'malayalam' else None
    from malayalam.ml_transliterate import convert_malayalam_data_to_devanagari

    if output_mode == 'combined':
        # Default: Combined output (Rik + Samam together)
        template_file = latex_jinja_env.get_template(template_file_src)
        text_template_file = latex_jinja_env.get_template(text_template_file_src)
        html_template_file = html_jinja_env.get_template(html_template_file_src) if html_template_file_src else None
        
        if gen_pdf:
            CreatePdf(template_file, f"{file_prefix}", doc_family, supersections, prayogas=prayogas_list, current_os=current_os, output_mode='combined', font_family=pdf_font, doc_title_sa=doc_title_sa, pdf_color_mode=pdf_color_mode, closing_mantras=closing_mantras, summary_table=summary_table, total_riks=total_riks_dev, total_samams=total_samams_dev, summary_title=summary_title_sa, toc_level=toc_level, has_riks=total_riks > 0, has_samams=total_samams > 0, output_dir_override=out_dir, name_override=out_name, jsv_version=jsv_version, generated_at=generated_at, kpully=kpully_mode)
        if gen_txt:
            CreateTextFile(text_template_file, f"{file_prefix}", doc_family, supersections, output_mode='combined', doc_title_sa=doc_title_sa, closing_mantras=closing_mantras, toc_level=toc_level, output_dir_override=out_dir, name_override=out_name, jsv_version=jsv_version, generated_at=generated_at)
            if script == 'malayalam':
                deva_supersections = convert_malayalam_data_to_devanagari(supersections)
                CreateTextFile(deva_text_template_file, f"{file_prefix}", 'Devanagari', deva_supersections, output_mode='combined', doc_title_sa=deva_doc_title_sa, closing_mantras=closing_mantras, toc_level=toc_level, output_dir_override=out_dir, name_override=out_name, jsv_version=jsv_version, generated_at=generated_at)
        if gen_html:
            CreateHtmlFile(html_template_file, f"{file_prefix}", doc_family, supersections, html_font=html_font, output_mode='combined', doc_title_sa=doc_title_sa, closing_mantras=closing_mantras, summary_table=summary_table, total_riks=total_riks_dev, total_samams=total_samams_dev, summary_title=summary_title_sa, toc_level=toc_level, has_riks=total_riks > 0, has_samams=total_samams > 0, output_dir_override=html_out_dir or out_dir, name_override=html_out_name or out_name, jsv_version=jsv_version, generated_at=generated_at, script=script, with_modifiers=args.swara_modifiers, kpully=kpully_mode)
        print("Success! Generated combined output files.")
        
    elif output_mode == 'separate':
        # Separate mode: Generate Rik-only and Samam-only files (with metadata, jsv_version=jsv_version, generated_at=generated_at)
        template_file = latex_jinja_env.get_template(template_file_src)
        text_template_file = latex_jinja_env.get_template(text_template_file_src)
        html_template_file = html_jinja_env.get_template(html_template_file_src) if html_template_file_src else None
        
        # Rik-only output: Pass output_mode='rik' to template
        if gen_rik:
            print("Generating Rik-only output (with metadata)...")
            base_pfx = out_name if out_name else file_prefix
            final_out_name = f"{base_pfx}_Rik" if not base_pfx.endswith("_Rik") else base_pfx
            if gen_pdf:
                CreatePdf(template_file, final_out_name, doc_family, supersections, prayogas=prayogas_list, current_os=current_os, output_mode='rik', font_family=pdf_font, doc_title_sa=doc_title_sa, pdf_color_mode=pdf_color_mode, closing_mantras=closing_mantras, summary_table=summary_table, total_riks=total_riks_dev, total_samams=total_samams_dev, summary_title=summary_title_sa, toc_level=toc_level, has_riks=total_riks > 0, has_samams=total_samams > 0, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at, kpully=kpully_mode)
            if gen_txt:
                CreateTextFile(text_template_file, final_out_name, doc_family, supersections, output_mode='rik', doc_title_sa=doc_title_sa, closing_mantras=closing_mantras, toc_level=toc_level, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at)
                if script == 'malayalam':
                    deva_supersections = convert_malayalam_data_to_devanagari(supersections)
                    CreateTextFile(deva_text_template_file, final_out_name, 'Devanagari', deva_supersections, output_mode='rik', doc_title_sa=deva_doc_title_sa, closing_mantras=closing_mantras, toc_level=toc_level, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at)
            if gen_html:
                CreateHtmlFile(html_template_file, final_out_name, doc_family, supersections, html_font=html_font, output_mode='rik', doc_title_sa=doc_title_sa, closing_mantras=closing_mantras, summary_table=summary_table, total_riks=total_riks_dev, total_samams=total_samams_dev, summary_title=summary_title_sa, toc_level=toc_level, has_riks=total_riks > 0, has_samams=total_samams > 0, output_dir_override=html_out_dir or out_dir, name_override=html_out_name or final_out_name, jsv_version=jsv_version, generated_at=generated_at, script=script, with_modifiers=args.swara_modifiers, kpully=kpully_mode)
        
        # Samam-only output: Pass output_mode='samam' to template
        if gen_samam:
            print("Generating Samam-only output (with metadata)...")
            base_pfx = out_name if out_name else file_prefix
            final_out_name = f"{base_pfx}_Samam" if not base_pfx.endswith("_Samam") else base_pfx
            if gen_pdf:
                CreatePdf(template_file, final_out_name, doc_family, supersections, prayogas=prayogas_list, current_os=current_os, output_mode='samam', font_family=pdf_font, doc_title_sa=doc_title_sa, pdf_color_mode=pdf_color_mode, closing_mantras=closing_mantras, summary_table=summary_table, total_riks=total_riks_dev, total_samams=total_samams_dev, summary_title=summary_title_sa, toc_level=toc_level, has_riks=total_riks > 0, has_samams=total_samams > 0, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at, kpully=kpully_mode)
            if gen_txt:
                CreateTextFile(text_template_file, final_out_name, doc_family, supersections, output_mode='samam', doc_title_sa=doc_title_sa, closing_mantras=closing_mantras, toc_level=toc_level, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at)
                if script == 'malayalam':
                    deva_supersections = convert_malayalam_data_to_devanagari(supersections)
                    CreateTextFile(deva_text_template_file, final_out_name, 'Devanagari', deva_supersections, output_mode='samam', doc_title_sa=deva_doc_title_sa, closing_mantras=closing_mantras, toc_level=toc_level, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at)
            if gen_html:
                CreateHtmlFile(html_template_file, final_out_name, doc_family, supersections, html_font=html_font, output_mode='samam', doc_title_sa=doc_title_sa, closing_mantras=closing_mantras, summary_table=summary_table, total_riks=total_riks_dev, total_samams=total_samams_dev, summary_title=summary_title_sa, toc_level=toc_level, has_riks=total_riks > 0, has_samams=total_samams > 0, output_dir_override=html_out_dir or out_dir, name_override=html_out_name or final_out_name, jsv_version=jsv_version, generated_at=generated_at, script=script, with_modifiers=args.swara_modifiers, kpully=kpully_mode)
        
        print("Success! Generated separate Rik and Samam output files.")
        
    else:
        # Nometa mode: Generate Rik-only and Samam-only files (without metadata, jsv_version=jsv_version, generated_at=generated_at)
        template_file = latex_jinja_env.get_template(template_file_src)
        text_template_file = latex_jinja_env.get_template(text_template_file_src)
        html_template_file = html_jinja_env.get_template(html_template_file_src) if html_template_file_src else None
        
        # Rik-only output (no metadata): Pass output_mode='rik_nometa' to template
        if gen_rik:
            print("Generating Rik-only output (without metadata)...")
            base_pfx = out_name if out_name else file_prefix
            final_out_name = f"{base_pfx}_Rik_NoMeta" if not base_pfx.endswith("_Rik_NoMeta") else base_pfx
            if gen_pdf:
                CreatePdf(template_file, final_out_name, doc_family, supersections, current_os=current_os, output_mode='rik_nometa', font_family=pdf_font, doc_title_sa=doc_title_sa, pdf_color_mode=pdf_color_mode, closing_mantras=closing_mantras, summary_table=summary_table, total_riks=total_riks_dev, total_samams=total_samams_dev, summary_title=summary_title_sa, toc_level=toc_level, has_riks=total_riks > 0, has_samams=total_samams > 0, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at, kpully=kpully_mode)
            if gen_txt:
                CreateTextFile(text_template_file, final_out_name, doc_family, supersections, output_mode='rik_nometa', doc_title_sa=doc_title_sa, closing_mantras=closing_mantras, toc_level=toc_level, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at)
                if script == 'malayalam':
                    deva_supersections = convert_malayalam_data_to_devanagari(supersections)
                    CreateTextFile(deva_text_template_file, final_out_name, 'Devanagari', deva_supersections, output_mode='rik_nometa', doc_title_sa=deva_doc_title_sa, closing_mantras=closing_mantras, toc_level=toc_level, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at)
            if gen_html:
                CreateHtmlFile(html_template_file, final_out_name, doc_family, supersections, html_font=html_font, output_mode='rik_nometa', doc_title_sa=doc_title_sa, closing_mantras=closing_mantras, summary_table=summary_table, total_riks=total_riks_dev, total_samams=total_samams_dev, summary_title=summary_title_sa, toc_level=toc_level, has_riks=total_riks > 0, has_samams=total_samams > 0, output_dir_override=html_out_dir or out_dir, name_override=html_out_name or final_out_name, jsv_version=jsv_version, generated_at=generated_at, script=script, with_modifiers=args.swara_modifiers, kpully=kpully_mode)
        
        # Samam-only output (no metadata): Pass output_mode='samam_nometa' to template
        if gen_samam:
            print("Generating Samam-only output (without metadata)...")
            base_pfx = out_name if out_name else file_prefix
            final_out_name = f"{base_pfx}_Samam_NoMeta" if not base_pfx.endswith("_Samam_NoMeta") else base_pfx
            if gen_pdf:
                CreatePdf(template_file, final_out_name, doc_family, supersections, current_os=current_os, output_mode='samam_nometa', font_family=pdf_font, doc_title_sa=doc_title_sa, pdf_color_mode=pdf_color_mode, closing_mantras=closing_mantras, summary_table=summary_table, total_riks=total_riks_dev, total_samams=total_samams_dev, summary_title=summary_title_sa, toc_level=toc_level, has_riks=total_riks > 0, has_samams=total_samams > 0, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at, kpully=kpully_mode)
            if gen_txt:
                CreateTextFile(text_template_file, final_out_name, doc_family, supersections, output_mode='samam_nometa', doc_title_sa=doc_title_sa, closing_mantras=closing_mantras, toc_level=toc_level, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at)
                if script == 'malayalam':
                    deva_supersections = convert_malayalam_data_to_devanagari(supersections)
                    CreateTextFile(deva_text_template_file, final_out_name, 'Devanagari', deva_supersections, output_mode='samam_nometa', doc_title_sa=deva_doc_title_sa, closing_mantras=closing_mantras, toc_level=toc_level, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at)
            if gen_html:
                CreateHtmlFile(html_template_file, final_out_name, doc_family, supersections, html_font=html_font, output_mode='samam_nometa', doc_title_sa=doc_title_sa, closing_mantras=closing_mantras, summary_table=summary_table, total_riks=total_riks_dev, total_samams=total_samams_dev, summary_title=summary_title_sa, toc_level=toc_level, has_riks=total_riks > 0, has_samams=total_samams > 0, output_dir_override=html_out_dir or out_dir, name_override=html_out_name or final_out_name, jsv_version=jsv_version, generated_at=generated_at, script=script, with_modifiers=args.swara_modifiers, kpully=kpully_mode)
        
        print("Success! Generated separate Rik and Samam output files without metadata.")



if __name__ == "__main__":
    main()
