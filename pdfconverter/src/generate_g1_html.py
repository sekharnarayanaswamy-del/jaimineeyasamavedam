"""
Generate a standalone HTML viewer from g1_extr.json using src/render.py and Devanagari_main_html.template.
----------------------------------------------------------------------------------------------------------
- Leverages the existing HTML renderer in `src/render.py` (`CreateHtmlFile`, `html_jinja_env`,
  `toc_header`, `to_devanagari_numeral`) without modifying any source files in the main project.
- Maps the `Parva -> Prapataka -> Kandah -> Samam` hierarchy into `supersections -> sections -> subsections`,
  grouping all Samam variants corresponding to the same Rik (e.g., 1.1 to 1.3) into a single `.subsection` card.
- Renders Vedic Tone Prenkha (U+1CD2 '᳒') with a single continuous horizontal line spanning over BOTH
  the preceding avagraha ('ऽ') and the syllable/numeral over which the horizontal bar appears in Unicode.
- Enlarges and boldens the superscript Vedic swara numerals/marks (U+A8E0..U+A8F1, U+1CD0, U+1CDA)
  in the embedded base64 font so they are clearly legible while preserving 100% pure Unicode text in the DOM.
- Renders each Samam's Checksum in the rounded pill box matching the source PDF.
"""

import argparse
import base64
import copy
import datetime
import html
import io
import json
import re
import sys
from pathlib import Path
from fontTools.ttLib import TTFont

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Import the existing HTML rendering engine from src/render.py
import src.render as render_engine
from src.renderers.filters.html_filters import format_dandas_html

DEFAULT_TEMPLATE = "templates/html/Devanagari_main_html.template"
FONTS_DIR = REPO_ROOT / "fonts"

# Matches a preceding avagraha ('ऽ') + the syllable/numeral carrying Vedic Tone Prenkha (U+1CD2 '᳒')
# (or any standalone syllable/numeral carrying U+1CD2 if no avagraha precedes it).
PRENKHA_RE = re.compile(
    r"(ऽ?\u1CD2?[०-९\u0900-\u093C\u093E-\u0963\uA8E0-\uA8FF\u1CD0-\u1CD1\u1CD3-\u1CFF]+)\u1CD2"
)


def build_scaled_swara_font_b64(
    font_path: Path,
    bold_font_path: Path = None,
    scale: float = 1.40,
    caret_scale: float = 1.00,
    swara_x_shift: int = 100,
    caret_x_shift: int = 180,
    deergha_gap: int = 380,
) -> str:
    """
    Loads `AdishilaVedic.ttf` (or `AdishilaVedicBold.ttf`) in memory, replaces the superscript
    Vedic swara numeral/mark glyphs (U+A8E0..U+A8F1, U+1CD0, U+1CDA) with bolder outlines:
    - Scales swara numerals by `scale` (default 1.40x) for clear legibility.
    - Scales caret accent symbol (U+1CD0) to a more compact `caret_scale` (default 1.00x)
      so it avoids colliding with previous or succeeding swara markers.
    - Positions swara markers left-justified over the base mantra syllable (`swara_x_shift` = 100)
      to avoid overhang into preceding syllables.
    - Centers caret over the avagraha (`caret_x_shift` = 180) in line with the swara markers.
    - In GPOS, spaces deergha marks (like '१र', '२र') with `deergha_gap` (default 380 font units
      via Value1.XPlacement = -380) to guarantee clean daylight separation between the digit
      and the deergha 'र', completely eliminating collisions across all deergha swaras.
    Does not modify any font files on disk.
    """
    if not font_path.exists():
        return ""

    tt = TTFont(str(font_path))
    bold_tt = TTFont(str(bold_font_path)) if (bold_font_path and bold_font_path.exists()) else None

    cmap = tt.getBestCmap()
    glyf = tt["glyf"]
    bold_cmap = bold_tt.getBestCmap() if bold_tt else {}
    bold_glyf = bold_tt["glyf"] if bold_tt else None

    swara_codepoints = list(range(0xA8E0, 0xA8F2)) + [0x1CD0, 0x1CDA]
    swara_glyph_names = set()

    for cp in swara_codepoints:
        gname = cmap.get(cp)
        if not gname or gname not in glyf:
            continue
        swara_glyph_names.add(gname)

        # Copy bolder glyph contour from AdishilaVedicBold if available
        if bold_glyf is not None and cp in bold_cmap and bold_cmap[cp] in bold_glyf:
            glyf[gname] = copy.deepcopy(bold_glyf[bold_cmap[cp]])

        g = glyf[gname]
        if g.isComposite() or not hasattr(g, "coordinates") or len(g.coordinates) == 0:
            continue

        g.recalcBounds(glyf)
        cx = (g.xMin + g.xMax) / 2.0
        base_y = g.yMin

        # Individual scale: caret is smaller to avoid collisions
        current_scale = caret_scale if cp in [0x1CD0, 0x1CDA] else scale

        # Align lower caret / svarita marks (U+1CD0, U+1CDA) up to the level of other swara markers (yMin ≈ 1690)
        y_shift = max(0, 1690 - base_y) if cp in [0x1CD0, 0x1CDA] else 0

        # Left-justified horizontal placement over consonant syllable
        x_shift = caret_x_shift if cp in [0x1CD0, 0x1CDA] else (swara_x_shift if cp in range(0xA8E0, 0xA8F2) else 0)

        new_coords = []
        for x, y in g.coordinates:
            nx = int(round(cx + (x - cx) * current_scale)) - x_shift
            ny = int(round(base_y + (y - base_y) * current_scale)) + y_shift
            new_coords.append((nx, ny))

        g.coordinates[:] = new_coords
        g.recalcBounds(glyf)
        if "hmtx" in tt and gname in tt["hmtx"].metrics:
            adv, _ = tt["hmtx"].metrics[gname]
            tt["hmtx"].metrics[gname] = (adv, g.xMin)

    # Configure horizontal pair spacing between consecutive combining swara marks (e.g. '꣡꣯' = '१र', '२र') in GPOS.
    # OpenType PairPos in AdishilaVedic uses ValueFormat1=1, ValueFormat2=0 (only Value1.XPlacement affects relative position).
    # Value1.XPlacement = -deergha_gap shifts the digit to the left of deergha 'र' by deergha_gap font units,
    # ensuring clean daylight spacing and zero collision between the digit and deergha 'र'.
    if "GPOS" in tt:
        for lookup in tt["GPOS"].table.LookupList.Lookup:
            if lookup.LookupType == 2:  # PairPos
                for st in lookup.SubTable:
                    cov_glyphs = getattr(st, "Coverage", None)
                    if not cov_glyphs:
                        continue
                    if any(gn in swara_glyph_names for gn in cov_glyphs.glyphs):
                        for pair_set in getattr(st, "PairSet", []):
                            for pvr in getattr(pair_set, "PairValueRecord", []):
                                if getattr(pvr, "SecondGlyph", "") == "uniA8EF":  # deergha 'र'
                                    if getattr(pvr, "Value1", None):
                                        pvr.Value1.XPlacement = -deergha_gap
                                elif getattr(pvr, "Value1", None) and getattr(pvr.Value1, "XPlacement", None):
                                    pvr.Value1.XPlacement = int(round(pvr.Value1.XPlacement * scale))

    # Ensure vertical ascender metrics accommodate the taller swara numerals without clipping
    new_ascent = 2500
    if "hhea" in tt:
        tt["hhea"].ascent = max(tt["hhea"].ascent, new_ascent)
    if "OS/2" in tt:
        tt["OS/2"].sTypoAscender = max(tt["OS/2"].sTypoAscender, new_ascent)
        tt["OS/2"].usWinAscent = max(tt["OS/2"].usWinAscent, new_ascent)
    if "head" in tt:
        tt["head"].yMax = max(tt["head"].yMax, new_ascent)

    buf = io.BytesIO()
    tt.save(buf)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def render_prenkha_html(escaped_text: str) -> str:
    """
    Replaces any sequence of `<avagraha><syllable/numeral>\\u1CD2` (e.g. `ऽ२᳒`) with a span that draws
    a continuous horizontal bar over BOTH the preceding avagraha ('ऽ') and the syllable/numeral ('२')
    over which the Prenkha bar is shown in the Unicode file.
    """
    def _wrap_prenkha(match: re.Match) -> str:
        base_seq = match.group(1).replace("\u1CD2", "")  # e.g. 'ऽ२' (preceding avagraha + syllable/numeral)
        return (
            '<span class="prenkha-overline" '
            'style="position:relative; display:inline; white-space:nowrap;" '
            'title="Vedic Tone Prenkha (U+1CD2)">'
            f'{base_seq}'
            '<span class="prenkha-bar" '
            'style="position:absolute; left:0.02em; right:0.02em; top:0.50em; '
            'height:2px; background:currentColor; pointer-events:none;"></span>'
            '</span>'
        )

    return PRENKHA_RE.sub(_wrap_prenkha, escaped_text)


def format_mantra_line_html(line: str) -> str:
    """
    Formats a Unicode Devanagari Samam line for HTML display:
    - Normalizes Caret (U+1CD0 '᳐') order: ensures caret is placed over the avagraha ('ऽ᳐')
      before following syllables and swara markers.
    - Delivers Caret (U+1CD0) inline on the same horizontal level when following a swara numeral,
      preventing vertical stacking.
    - Escapes HTML special characters.
    - Renders Vedic Tone Prenkha (U+1CD2 '᳒') with a continuous horizontal line over the
      preceding avagraha ('ऽ') and the syllable/numeral carrying U+1CD2.
    - Formats dandas ('।', '॥') using `src/renderers/filters/html_filters.py`.
    """
    # 1. Normalize caret over avagraha
    line = re.sub(r'\u1cd0[ \t]*ऽ', 'ऽ\u1cd0', line)

    # 2. When caret follows a swara numeral, insert thin space so browser shaper keeps it inline
    line = re.sub(r'([\ua8e0-\ua8f1])\u1cd0', lambda m: m.group(1) + '\u2009\u1cd0', line)

    escaped = html.escape(line)
    escaped = render_prenkha_html(escaped)
    escaped = format_dandas_html(escaped, preserve_spaces=True)
    return escaped


def format_checksum_html(ck: dict) -> str:
    """
    Renders the Samam checksum pill box matching the PDF screenshot:
    (दी॰ ७। प॰ ९। मा॰ ९)   (१)   ॥ झो ॥ १ ॥
    """
    if not ck:
        return ""

    raw = ck.get("raw", "")
    d_val = ck.get("dirghah", "")
    p_val = ck.get("parvani", "")
    m_val = ck.get("matrah", "")
    k_num = ck.get("prapataka_samam_num", "")
    code = ck.get("code", "")
    g_num = ck.get("global_samam_num", "")

    if raw.startswith("दीर्घाः"):
        inner_html = (
            f'<span>दीर्घाः {html.escape(d_val)} । पर्वाणि {html.escape(p_val)} । मात्राः {html.escape(m_val)}</span>'
            f'<span style="margin-left:0.55em;">॥ {html.escape(code)} ॥ {html.escape(g_num)} ॥</span>'
        )
    else:
        inner_html = (
            f'<span>(दी॰ {html.escape(d_val)}। प॰ {html.escape(p_val)}। मा॰ {html.escape(m_val)})</span>'
            f'<span style="margin-left:0.5em;">({html.escape(k_num)})</span>'
            f'<span style="margin-left:0.5em;">॥ {html.escape(code)} ॥ {html.escape(g_num)} ॥</span>'
        )

    return (
        '<div style="display:flex; justify-content:flex-end; margin-top:0.3rem;">'
        '<div class="samam-checksum-box" style="'
        'background: #F7F8FC; '
        'border: 1px solid #D0D4E8; '
        'border-radius: 5px; '
        'padding: 0.1rem 0.55rem; '
        'font-size: 0.8rem; '
        'color: #555; '
        'display: inline-flex; '
        'align-items: center; '
        'white-space: nowrap; '
        'line-height: 1.35;">'
        f'{inner_html}'
        '</div>'
        '</div>'
    )


def render_single_samam_block_html(samam: dict) -> str:
    """Renders a single Samam entry (Header + Mantra lines + Checksum box) within a Rik subsection card."""
    parts = []

    samam_id = samam.get("samam_id", "")
    name = samam.get("name", "")
    meta = samam.get("metadata", "")

    # 1. Header
    header_spans = []
    header_title = samam.get("header_title", "")
    if not header_title:
        if samam_id and not samam_id.startswith("०-"):
            id_str = samam_id.replace(".", "-")
            header_title = f"{id_str} {name}।" if name else id_str
        else:
            header_title = f"{name}।" if name else samam.get("header", "")

    if header_title:
        header_spans.append(f'<span class="header-title">{html.escape(header_title)}</span>')
    if meta:
        header_spans.append(f'<span class="header-meta">{html.escape(meta)} ॥</span>')

    if header_spans:
        parts.append(
            f'<div class="subsection-header" style="text-align:left;">'
            f'{" &nbsp; ".join(header_spans)}'
            f'</div>'
        )

    # 2. Mantra lines (with Prenkha continuous horizontal line over 'ऽ' + syllable)
    mantra_lines = samam.get("mantra_lines", [])
    if mantra_lines:
        lines_html = []
        for ln in mantra_lines:
            lines_html.append(
                f'<div class="sanskrit-text" style="margin: 0.55rem 0; line-height: 2.55; text-align: left; '
                f'font-size: var(--mantra-size); letter-spacing: 0.015em;">'
                f'{format_mantra_line_html(ln)}'
                f'</div>'
            )
        parts.append(f'<div class="samam-text" style="padding: 0.25rem 0.2rem;">{"".join(lines_html)}</div>')

    # 3. Checksum pill box
    ck_html = format_checksum_html(samam.get("checksum"))
    if ck_html:
        parts.append(ck_html)

    return "\n".join(parts)


def format_g1_subsection_html(
    subsection,
    supersection_title=None,
    section_title=None,
    subsection_title=None,
    footnote_dict=None,
    prev_rik_id=None,
    subsection_key=None,
    footnote_counter=0,
    footnotes_accumulator=None,
    seen_content_map=None,
    with_modifiers=True,
    doc_markers_map=None,
):
    """
    Custom subsection formatter hooked into `src/render.py`'s `preprocess_html_data` pipeline.
    Renders all Samams belonging to a single Rik (e.g., 1.1 to 1.3) together in one `.subsection` card.
    """
    samam_group = subsection.get("samam_group", [])
    if not samam_group and "samam_data" in subsection:
        samam_group = [subsection["samam_data"]]

    divider_html = (
        '<hr style="border:none; border-top:1.5px dashed var(--border); margin: 1.25rem 0 1.1rem;" />'
    )
    samam_blocks = [render_single_samam_block_html(s) for s in samam_group]
    parts = [divider_html.join(samam_blocks)]

    # Optional trailing Kandah / Prapataka colophons attached to the last Rik group of a section
    for col_html in subsection.get("trailing_colophons_html", []):
        parts.append(col_html)

    return "\n".join(parts), footnote_counter


def group_samams_by_rik(samams: list) -> list:
    """
    Groups consecutive Samams that share the same `rik_num` (e.g., 1.1, 1.2, 1.3 -> rik_num 1)
    into a list of Rik groups so all Samams for a single Rik are placed in one subsection section.
    """
    groups = []
    for s in samams:
        r_num = s.get("rik_num")
        if groups and groups[-1]["rik_num"] == r_num:
            groups[-1]["samams"].append(s)
        else:
            groups.append({
                "rik_num": r_num,
                "samams": [s],
            })
    return groups


def clean_toc_heading(text: str) -> str:
    """
    Cleans a Parva, Prapataka, or Kandah title for the Table of Contents:
    - Strips surrounding '॥' and whitespace
    - Removes 'अथ' (e.g., 'अथ प्रथम खण्डः' -> 'प्रथम खण्डः', 'अथैन्द्रं पर्व' -> 'ऐन्द्रं पर्व')
    """
    if not text:
        return ""
    t = str(text).replace("॥", "").strip()
    t = t.replace("अथैन्द्रं", "ऐन्द्रं")
    t = re.sub(r"(^|\.\s+)अथ\s+", r"\1", t)
    t = render_engine.toc_header(t)
    return t.strip()


def generate_html_via_render_py(
    json_path: Path,
    html_path: Path,
    template_rel_path: str = DEFAULT_TEMPLATE,
    swara_scale: float = 1.40,
    caret_scale: float = 1.00,
    swara_x_shift: int = 100,
    caret_x_shift: int = 180,
    deergha_gap: int = 380,
):
    """
    Converts the Parva -> Prapataka -> Kandah -> Samam hierarchy into `src/render.py`'s
    `supersections` structure (grouping Samams by Rik into subsections), invokes
    `src/render.py`'s `CreateHtmlFile`, and injects the scaled-swara base64 fonts.
    """
    data = json.loads(json_path.read_text(encoding="utf-8"))

    supersections = {}
    summary_table = []
    total_riks_int = 0
    total_samams_int = 0

    for pv in data.get("parvas", []):
        pv_id = pv.get("parva_id", 1)
        pv_title = clean_toc_heading(pv.get("parva_title", ""))

        for pr in pv.get("prapatakas", []):
            pr_id = pr.get("prapataka_id", "1")
            pr_title = pr.get("prapataka_title", "")
            pr_title_clean = clean_toc_heading(pr_title)

            ss_key = f"parva_{pv_id}_prapataka_{pr_id}"
            full_ss_title = f"{pv_title} — {pr_title_clean}" if pv_title else pr_title_clean

            sections_dict = {}
            khanda_rows = []
            pr_rik_count = 0
            pr_samam_count = 0

            kandahs = pr.get("kandahs", [])
            for k_idx, k in enumerate(kandahs):
                k_id = k.get("kandah_id", str(k_idx + 1))
                k_title = k.get("kandah_title", "")
                k_title_clean = clean_toc_heading(k_title)
                k_colophon = k.get("colophon", "")
                samams = k.get("samams", [])

                rik_groups = group_samams_by_rik(samams)
                k_rik_count = len(rik_groups)
                k_samam_count = len(samams)

                pr_rik_count += k_rik_count
                pr_samam_count += k_samam_count
                total_riks_int += k_rik_count
                total_samams_int += k_samam_count

                sec_key = f"kandah_{k_id}"
                subsections_dict = {}

                for g_idx, r_grp in enumerate(rik_groups, start=1):
                    grp_samams = r_grp["samams"]
                    sub_key = f"rik_{g_idx}"

                    # Bring whatever is in the SS header_title directly to the TOC (with १-१ before the Samam name)
                    ss_titles = []
                    for s in grp_samams:
                        t_title = s.get("toc_title", "").strip()
                        if not t_title:
                            sid = s.get("samam_id", "").replace(".", "-")
                            nm = s.get("name", "").strip()
                            if sid and not sid.startswith("०-"):
                                t_title = f"{sid} {nm}".strip()
                            else:
                                t_title = nm or sid
                        if t_title:
                            ss_titles.append(t_title)

                    idx_header = " / ".join(ss_titles)

                    trailing_colophons = []
                    if g_idx == k_rik_count:
                        if k_colophon:
                            k_col_html = "<br>".join(html.escape(p.strip()) for p in k_colophon.split(" | ") if p.strip())
                            trailing_colophons.append(
                                f'<div style="text-align:center; margin: 1.1rem 0 0.3rem; padding: 0.55rem 1rem; '
                                f'background: #F3FAFF; border: 1px solid #90CAF9; border-radius: 8px; '
                                f'color: var(--maroon); font-weight: 600; font-size: 1.15rem;">'
                                f'{k_col_html}</div>'
                            )
                        pr_colophon = pr.get("colophon", "")
                        if k_idx == len(kandahs) - 1 and pr_colophon and pr_colophon != k_colophon:
                            pr_col_html = "<br>".join(html.escape(p.strip()) for p in pr_colophon.split(" | ") if p.strip())
                            trailing_colophons.append(
                                f'<div style="text-align:center; margin: 0.8rem 0 0.3rem; padding: 0.65rem 1.2rem; '
                                f'background: #FFF3E0; border: 1.5px solid var(--gold); border-radius: 8px; '
                                f'color: var(--maroon); font-weight: 700; font-size: 1.2rem;">'
                                f'{pr_col_html}</div>'
                            )

                    subsections_dict[sub_key] = {
                        "header": {
                            "header": idx_header,
                            "header_number": g_idx,
                        },
                        "samam_group": grp_samams,
                        "trailing_colophons_html": trailing_colophons,
                    }

                sections_dict[sec_key] = {
                    "section_title": k_title,
                    "section_title_toc": k_title_clean,
                    "Count": (
                        f"ऋ-{render_engine.to_devanagari_numeral(k_rik_count)}, "
                        f"सा-{render_engine.to_devanagari_numeral(k_samam_count)}"
                    ),
                    "subsections": subsections_dict,
                }

                khanda_rows.append({
                    "id": f"{ss_key}-{sec_key}",
                    "khanda": k_title_clean,
                    "riks": render_engine.to_devanagari_numeral(k_rik_count),
                    "samams": render_engine.to_devanagari_numeral(k_samam_count),
                })

            supersections[ss_key] = {
                "supersection_title": full_ss_title,
                "supersection_title_toc": full_ss_title,
                "Count": (
                    f"ऋ-{render_engine.to_devanagari_numeral(pr_rik_count)}, "
                    f"सा-{render_engine.to_devanagari_numeral(pr_samam_count)}"
                ),
                "sections": sections_dict,
            }

            summary_table.append({
                "id": ss_key,
                "patha": full_ss_title,
                "patha_riks": render_engine.to_devanagari_numeral(pr_rik_count),
                "patha_samams": render_engine.to_devanagari_numeral(pr_samam_count),
                "khandas": khanda_rows,
            })

    # Hook our Gramageyaganam subsection formatter into src/render.py at runtime
    render_engine.format_samam_only_html = format_g1_subsection_html
    render_engine.format_mantra_sets_html = format_g1_subsection_html
    render_engine.normalize_output_basename = lambda name, doc_family: Path(name).stem

    html_template = render_engine.html_jinja_env.get_template(template_rel_path)

    # Wrap template.render so CreateHtmlFile automatically receives our enlarged-swara base64 fonts
    orig_render = html_template.render
    reg_font_path = FONTS_DIR / "AdishilaVedic.ttf"
    bold_font_path = FONTS_DIR / "AdishilaVedicBold.ttf"
    scaled_reg_b64 = build_scaled_swara_font_b64(
        reg_font_path,
        bold_font_path,
        scale=swara_scale,
        caret_scale=caret_scale,
        swara_x_shift=swara_x_shift,
        caret_x_shift=caret_x_shift,
        deergha_gap=deergha_gap,
    )
    scaled_bold_b64 = build_scaled_swara_font_b64(
        bold_font_path,
        bold_font_path,
        scale=swara_scale,
        caret_scale=caret_scale,
        swara_x_shift=swara_x_shift,
        caret_x_shift=caret_x_shift,
        deergha_gap=deergha_gap,
    )

    def _custom_render(**kwargs):
        if scaled_reg_b64:
            kwargs["adishila_vedic_b64"] = scaled_reg_b64
        if scaled_bold_b64:
            kwargs["adishila_vedic_bold_b64"] = scaled_bold_b64
        return orig_render(**kwargs)

    html_template.render = _custom_render

    doc_title_sa = (
        "अथ प्रकृतिगानम् (ग्रामेगेयगानम्)"
        if len(data.get("parvas", [])) > 1
        else "अथ प्रकृतिगानम् (ग्रामेगेयगानम्) — १. आग्नेयं पर्व"
    )

    render_engine.CreateHtmlFile(
        templateFileName=html_template,
        name=html_path.stem,
        DocfamilyName="Devanagari",
        data=supersections,
        html_font="'AdishilaVedic', 'Adishila San', 'Noto Serif Devanagari', serif",
        output_mode="samam",
        doc_title_sa=doc_title_sa,
        closing_mantras=[],
        summary_table=summary_table,
        total_riks=render_engine.to_devanagari_numeral(total_riks_int),
        total_samams=render_engine.to_devanagari_numeral(total_samams_int),
        summary_title="ग्रामेगेयगानम् सङ्ख्या (Parva / Prapataka / Kandah / Samam)",
        toc_level="section",
        has_riks=True,
        has_samams=True,
        output_dir_override=str(html_path.parent),
        name_override=html_path.stem,
        jsv_version="1.0",
        generated_at=datetime.datetime.now().strftime("%d-%m-%Y"),
        script="devanagari",
        with_modifiers=True,
        kpully=False,
    )


def main():
    parser = argparse.ArgumentParser(description="Generate standalone HTML viewer from g1_extr.json via src/render.py")
    parser.add_argument(
        "--input", "-i",
        default="pdfconverter/data/output/g1_extr.json",
        help="Path to input hierarchical JSON file",
    )
    parser.add_argument(
        "--output", "-o",
        default="pdfconverter/data/output/g1_extr.html",
        help="Path to output standalone HTML file",
    )
    parser.add_argument(
        "--template", "-t",
        default=DEFAULT_TEMPLATE,
        help="Relative path to HTML Jinja2 template",
    )
    parser.add_argument(
        "--swara-scale", "-s",
        type=float,
        default=1.40,
        help="Scale factor for superscript Vedic swara numerals/marks in embedded font (default: 1.40)",
    )
    parser.add_argument(
        "--caret-scale",
        type=float,
        default=1.00,
        help="Scale factor for caret accent symbol U+1CD0 to avoid swara collisions (default: 1.00)",
    )
    parser.add_argument(
        "--swara-shift",
        type=int,
        default=100,
        help="Horizontal shift in font units to left-justify swaras over base syllables (default: 100)",
    )
    parser.add_argument(
        "--caret-shift",
        type=int,
        default=180,
        help="Horizontal shift in font units to center caret marks over avagraha + next syllable (default: 180)",
    )
    parser.add_argument(
        "--deergha-gap",
        type=int,
        default=380,
        help="Horizontal separation in font units between deergha swara pairs like '१र', '२र' in GPOS (default: 380)",
    )
    args = parser.parse_args()

    generate_html_via_render_py(
        Path(args.input),
        Path(args.output),
        args.template,
        swara_scale=args.swara_scale,
        caret_scale=args.caret_scale,
        swara_x_shift=args.swara_shift,
        caret_x_shift=args.caret_shift,
        deergha_gap=args.deergha_gap,
    )


if __name__ == "__main__":
    main()
