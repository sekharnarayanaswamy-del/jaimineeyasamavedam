#!/usr/bin/env python3
"""
Generate a comprehensive visual Glyph Grid PNG and interactive HTML table
showcasing the full set of Jaimineeya Vedic Swara glyphs, composite ligatures,
manuscript overrides (Pla/Sha), and all Canonical Vedic Swara Modifiers (A..H) with their
"Stacked above/below" positions, dotted-circle syllable representations, and typing shortcuts.
"""

from pathlib import Path
import csv
import shutil
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT_PATH = ROOT / "fonts" / "JaimineeyaSwara.ttf"
OUT_IMG = ROOT / "data" / "output" / "malayalam" / "glyph_grid_JaimineeyaSwara.png"
OUT_HTML = ROOT / "data" / "output" / "malayalam" / "glyph_table.html"

ARTIFACT_DIR = Path(r"C:\Users\sekha\.gemini\antigravity-ide\brain\33a78242-ade0-47ff-b909-95b423204936")

# Featured highlights for the high-res visual chart
FEATURED_GLYPHS = [
    # Row 1: The Canonical 8 Vedic Swara Modifiers (A..H)
    ("Modifier (A) Arc", "\uE004", "syllable_arc_jsv", "U+E004 / ╭╮", "Modifier (A)", "Above", "Syllable Spanning Arc"),
    ("Modifier (B) Caret", "\uE005", "caret_jsv", "U+E005 / /\\", "Modifier (B)", "Above", "Peak Elevation Caret"),
    ("Modifier (C) Dot", "\uE001", "high_dot_jsv", "U+E001 / ॱ", "Modifier (C)", "Shoulder", "Shoulder Pause Dot"),
    ("Modifier (D) Chevron", "\uE006", "roof_jsv", "U+E006 / Ʌ", "Modifier (D)", "Above", "Chevron Roof"),
    ("Modifier (E) Danda", "\uE002", "phrasing_danda_jsv", "U+E002 / ┃", "Modifier (E)", "Inline", "Phrasing Heavy Danda"),
    ("Modifier (F) Vert", "\uE002", "phrasing_danda_jsv", "U+E002 / ╷", "Modifier (F)", "Inline", "Light Vertical"),
    ("Modifier (G) Slash", "\uE003", "descending_tone_jsv", "U+E003 / \\", "Modifier (G)", "Below", "Descending Tone Slash"),
    ("Modifier (H) Swarita", "\uE00C", "swarita_jsv", "U+E00C / ॑", "Modifier (H)", "Above", "Overhead Swarita Stroke"),

    # Row 2: Ayugma pure Grantha bases (A01..A08)
    ("A01 Ka (അവരോഹം)", "\U00011315", "ka_gran", "U+11315", "Ayugma Swara", "Above", "Ka (Avaroham)"),
    ("A02 Kha (അന്വംഗുല്യം)", "\U00011316", "kha_gran", "U+11316", "Ayugma Swara", "Above", "Kha (Anvangulyam)"),
    ("A03 Ca (അഭീതം)", "\U0001131A", "ca_gran", "U+1131A", "Ayugma Swara", "Above", "Ca (Abhitam)"),
    ("A04 Cha (അഭ്രം)", "\U0001131B", "cha_gran", "U+1131B", "Ayugma Swara", "Above", "Cha (Abhram)"),
    ("A05 Tta (അനിഷ്ടം)", "\U0001131F", "tta_gran", "U+1131F", "Ayugma Swara", "Above", "Tta (Anishtam)"),
    ("A06 Ttha (അപ്രതിഷ്ഠം)", "\U00011320", "ttha_gran", "U+11320", "Ayugma Swara", "Above", "Ttha (Apratishtham)"),
    ("A07 Dda (അവിപ്രിയം)", "\U00011321", "dda_gran", "U+11321", "Ayugma Swara", "Above", "Dda (Avipriyam)"),
    ("A08 Ddha (അന്തം)", "\U00011322", "ddha_gran", "U+11322", "Ayugma Swara", "Above", "Ddha (Antam)"),

    # Row 3: Ayugma pure Grantha bases (A09..A16)
    ("A09 Nna (നമനം)", "\U00011323", "nna_gran", "U+11323", "Ayugma Swara", "Above", "Nna (Namanam)"),
    ("A10 Ta (അതതം)", "\U00011324", "ta_gran", "U+11324", "Ayugma Swara", "Above", "Ta (Atatam)"),
    ("A11 Tha (അസ്തം)", "\U00011325", "tha_gran", "U+11325", "Ayugma Swara", "Above", "Tha (Astam)"),
    ("A12 Da (ദാനം)", "\U00011326", "da_gran", "U+11326", "Ayugma Swara", "Above", "Da (Danam)"),
    ("A13 Dha (ധൃതം)", "\U00011327", "dha_gran", "U+11327", "Ayugma Swara", "Above", "Dha (Dhritam)"),
    ("A14 Na (നമ്രം)", "\U00011328", "na_gran", "U+11328", "Ayugma Swara", "Above", "Na (Namram)"),
    ("A15 Pa (പാപം)", "\U0001132A", "pa_gran", "U+1132A", "Ayugma Swara", "Above", "Pa (Papam)"),
    ("A16 Pha (ഫലം)", "\U0001132B", "pha_gran", "U+1132B", "Ayugma Swara", "Above", "Pha (Phalam)"),

    # Row 4: Custom bases & Sha-family
    ("A17 Tra (ത്ര)", "\uE01D", "t_ra_gran", "U+11324+11330", "Ayugma Conjunct", "Above", "Tra Conjunct"),
    ("A18 Kra (ക്ര)", "\uE01E", "k_ra_jsv", "U+11315+11330", "Ayugma Conjunct", "Above", "Kra Conjunct"),
    ("A13 Sha (Base)", "\u0D36", "sha_mal", "U+0D36 (ശ)", "Malayalam Base", "Above", "Sha Base (Mal)"),
    ("Shaa (Sha+AA)", "\uE010", "sha_aa_jsv", "U+E010 / ശ+ാ", "Manuscript Ligature", "Above", "Shaa Ligature"),
    ("Shi (Sha+I)", "\uE011", "sha_i_jsv", "U+E011 / ശ+ി", "Manuscript Ligature", "Above", "Shi Ligature"),
    ("Shii (Sha+II)", "\uE012", "sha_ii_jsv", "U+E012 / ശ+ീ", "Manuscript Ligature", "Above", "Shii Ligature"),
    ("Sha+Virama", "\uE013", "sha_virama_jsv", "U+E013 / ശ്", "Manuscript Ligature", "Above", "Sha Virama"),
    ("A15 Pla (Vedic Base)", "\uE020", "pla_jsv", "U+E020 / Pla", "Manuscript Base", "Above", "Authentic Vedic Pla"),

    # Row 5: Pla-family & Complex Ligatures
    ("Plaa (Pla+AA)", "\uE021", "pla_aa_jsv", "U+E021 / Pla+ാ", "Manuscript Ligature", "Above", "Plaa Ligature"),
    ("Pli (Pla+I)", "\uE022", "pla_i_jsv", "U+E022 / Pla+ി", "Manuscript Ligature", "Above", "Pli Ligature"),
    ("Plii (Pla+II)", "\uE023", "pla_ii_jsv", "U+E023 / Pla+ീ", "Manuscript Ligature", "Above", "Plii Ligature"),
    ("Shruu (ശ്രൂ)", "\uE027", "sh_ruu_jsv", "U+E027", "Manuscript Ligature", "Above", "Clean Shruu"),
    ("Shrr (ശ്രൃ)", "\uE028", "sh_r_r_jsv", "U+E028", "Manuscript Ligature", "Above", "Clean Shrr"),
    ("Nna+U (ണു)", "\uE029", "nna_u_jsv", "U+E029", "Manuscript Ligature", "Above", "Clean Nna+U"),
    ("Rik Swarita", "\u0951", "swarita_accent_jsv", "U+0951 / (1)", "Rik Accent", "Above", "Udaatta Accent"),
    ("Rik Anudatta", "\u1CD2", "anudatta_accent_jsv", "U+1CD2 / (2)", "Rik Accent", "Above", "Anudatta Bar"),
]


def render_image_grid() -> None:
    cols = 4
    rows = (len(FEATURED_GLYPHS) + cols - 1) // cols
    cell_w, cell_h = 440, 250
    pad_x, pad_y = 60, 110
    w = cols * cell_w + pad_x * 2
    h = rows * cell_h + pad_y * 2 + 100

    img = Image.new("RGB", (w, h), color=(248, 250, 253))
    draw = ImageDraw.Draw(img)

    kartika_path = Path("C:/Windows/Fonts/kartika.ttf")
    kartika_bold = Path("C:/Windows/Fonts/kartikab.ttf")
    try:
        title_font = ImageFont.truetype("arial.ttf", 36)
        label_font = ImageFont.truetype(str(kartika_bold) if kartika_bold.exists() else "arial.ttf", 19)
        sub_font = ImageFont.truetype(str(kartika_path) if kartika_path.exists() else "arial.ttf", 14)
        swara_font = ImageFont.truetype(str(FONT_PATH), 60)
        dotted_font = ImageFont.truetype("seguisym.ttf", 46) if Path("C:/Windows/Fonts/seguisym.ttf").exists() else ImageFont.truetype("arial.ttf", 46)
    except Exception:
        title_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        swara_font = ImageFont.load_default()
        dotted_font = ImageFont.load_default()

    # Header
    draw.text((pad_x, 35), "Jaimineeya Samavedam — Vedic Swara & Modifier Glyph Inventory", fill=(15, 23, 42), font=title_font)
    draw.text((pad_x, 82), "JaimineeyaSwara.ttf — Swara Pitch Markers (Bold Red) & Mantrakshara Modifiers (Dark Blue)", fill=(71, 85, 105), font=label_font)

    # Grid Cells
    for i, (label, char_str, gname, cp_str, category, stack_pos, desc) in enumerate(FEATURED_GLYPHS):
        r = i // cols
        c = i % cols
        x0 = pad_x + c * cell_w
        y0 = pad_y + 30 + r * cell_h
        x1 = x0 + cell_w - 20
        y1 = y0 + cell_h - 20

        # Background card
        is_mod = "Modifier" in category
        bg_fill = (255, 255, 255)
        border_col = (0, 33, 113) if is_mod else (226, 232, 240)
        border_w = 2 if is_mod else 1
        draw.rounded_rectangle([x0, y0, x1, y1], radius=12, fill=bg_fill, outline=border_col, width=border_w)

        # Header tag
        tag_color = (0, 33, 113) if is_mod else (198, 40, 40) if "Ayugma" in category else (21, 101, 192) if "Ligature" in category else (46, 125, 50)
        draw.rounded_rectangle([x0 + 12, y0 + 12, x0 + 125, y0 + 34], radius=6, fill=tag_color)
        draw.text((x0 + 18, y0 + 15), category[:14], fill=(255, 255, 255), font=sub_font)

        # Stacking position tag
        pos_color = (15, 118, 110) if stack_pos == "Shoulder" else (30, 64, 175) if stack_pos == "Above" else (147, 51, 234) if stack_pos == "Below" else (100, 116, 139)
        draw.rounded_rectangle([x0 + 135, y0 + 12, x0 + 245, y0 + 34], radius=6, fill=pos_color)
        draw.text((x0 + 143, y0 + 15), f"Pos: {stack_pos}", fill=(255, 255, 255), font=sub_font)

        # Glyph Box
        draw.rounded_rectangle([x0 + 12, y0 + 46, x0 + 140, y0 + 185], radius=8, fill=(248, 250, 252), outline=(226, 232, 240), width=1)

        if is_mod:
            # Modifiers rendered in Dark Blue (#002171) with Dotted Circle (◌)
            mod_blue = (0, 33, 113)
            dot_gray = (148, 163, 184)
            if "Arc" in label or "Modifier (A)" in category or "Modifier (B)" in category or "Modifier (D)" in category:
                # 2-syllable spanning modifiers (A, B, D)
                draw.text((x0 + 26, y0 + 100), "◌", fill=dot_gray, font=dotted_font)
                draw.text((x0 + 74, y0 + 100), "◌", fill=dot_gray, font=dotted_font)
                draw.text((x0 + 26, y0 + 48), char_str, fill=mod_blue, font=swara_font)
            elif "Modifier (C)" in category or "Dot" in label:
                # Shoulder dot (C)
                draw.text((x0 + 36, y0 + 95), "◌", fill=dot_gray, font=dotted_font)
                draw.text((x0 + 76, y0 + 62), char_str, fill=mod_blue, font=swara_font)
            elif "Modifier (G)" in category or "Slash" in label:
                # Descending tone slash attached below right base (G)
                draw.text((x0 + 42, y0 + 70), "◌", fill=dot_gray, font=dotted_font)
                draw.text((x0 + 52, y0 + 95), char_str, fill=mod_blue, font=swara_font)
            elif "Modifier (H)" in category or "Swarita" in label:
                # Overhead swarita tick (H)
                draw.text((x0 + 50, y0 + 105), "◌", fill=dot_gray, font=dotted_font)
                draw.text((x0 + 50, y0 + 52), char_str, fill=mod_blue, font=swara_font)
            else:
                draw.text((x0 + 35, y0 + 90), "◌", fill=dot_gray, font=dotted_font)
                draw.text((x0 + 80, y0 + 80), char_str, fill=mod_blue, font=swara_font)
        else:
            # Swara pitch glyphs rendered in Bold SwaraRed (#c62828)
            draw.text((x0 + 45, y0 + 75), char_str, fill=(198, 40, 40), font=swara_font)

        # Labels & metadata
        draw.text((x0 + 155, y0 + 52), label, fill=(15, 23, 42), font=label_font)
        draw.text((x0 + 155, y0 + 82), f"Desc: {desc}", fill=(51, 65, 85), font=sub_font)
        draw.text((x0 + 155, y0 + 108), f"Glyph: {gname}", fill=(71, 85, 105), font=sub_font)
        draw.text((x0 + 155, y0 + 134), f"Code: {cp_str}", fill=(100, 116, 139), font=sub_font)

        # Color note badge
        color_badge_text = "Dark Blue (Mantrakshara Mod)" if is_mod else "Bold Red (Swara Pitch)"
        color_badge_bg = (238, 242, 255) if is_mod else (254, 242, 242)
        color_badge_fg = (0, 33, 113) if is_mod else (198, 40, 40)
        draw.rounded_rectangle([x0 + 12, y0 + 195, x0 + cell_w - 32, y0 + 220], radius=4, fill=color_badge_bg)
        draw.text((x0 + 20, y0 + 200), color_badge_text, fill=color_badge_fg, font=sub_font)

    OUT_IMG.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT_IMG, "PNG")
    print(f"Saved Glyph Grid Image: {OUT_IMG}")
    
    # Copy to artifact directory for UI display
    art_img = ARTIFACT_DIR / "glyph_grid_JaimineeyaSwara.png"
    shutil.copy(OUT_IMG, art_img)
    print(f"Copied to artifact directory: {art_img}")


def render_html_table() -> None:
    csv_path = ROOT / "data" / "output" / "malayalam" / "samhita_marker_review.csv"
    if not csv_path.exists():
        csv_path = ROOT / "Malayalam_JSV" / "samhita_marker_review.csv"

    rows = []
    if csv_path.exists():
        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

    # All Canonical Vedic Swara Modifiers (A..H)
    modifiers = [
        {
            "id": "MOD-A",
            "shortcut": "(A)",
            "name": "Syllable Spanning Arc (Tie / Breve)",
            "glyph": "\uE004",
            "codepoint": "U+E004 / ╭╮",
            "input_methods": "<code>(A)</code> / <code>(a)</code> / <code>(╭╮)</code> / <code>(⁀)</code>",
            "stack_pos": "Stacked Above",
            "dotted_rep": "<span class='dotted-sample'><span class='arc-tie'>╭╮</span><span class='base-circle'>◌◌</span></span>",
            "example_text": "ൠഹാ(𑌪𑌾)(A)",
            "example_preview": "<div class='mantra-preview-box'><div class='stack-top'><span class='swara-red'>𑌪𑌾</span></div><div class='mantra-base'><span class='mod-arc-tie'>╭╮</span>ൠഹാ</div></div>",
            "meaning": "Overhead curved arch spanning across syllables for connected tone transition.",
            "color_note": "ModifierDarkBlue (#002171) on Mantrakshara"
        },
        {
            "id": "MOD-B",
            "shortcut": "(B)",
            "name": "Caret / Peak (/\\ / ^)",
            "glyph": "\uE005",
            "codepoint": "U+E005 / ^ / /\\",
            "input_methods": "<code>(B)</code> / <code>(b)</code> / <code>(^)</code> / <code>(/\\)</code>",
            "stack_pos": "Stacked Above",
            "dotted_rep": "<span class='dotted-sample'><span class='mod-sup-center'>^</span><span class='base-circle'>◌</span></span>",
            "example_text": "മാ(𑌕)(B)",
            "example_preview": "<div class='mantra-preview-box'><div class='stack-top'><span class='swara-red'>𑌕</span></div><div class='mantra-base'>മാ<span class='mod-blue-sup'>^</span></div></div>",
            "meaning": "Overhead peak arrowhead indicating elevated melodic emphasis.",
            "color_note": "ModifierDarkBlue (#002171) on Mantrakshara"
        },
        {
            "id": "MOD-C",
            "shortcut": "(C)",
            "name": "High / Shoulder Dot (ॱ / ·)",
            "glyph": "\uE001",
            "codepoint": "U+E001 / U+0971 / ·",
            "input_methods": "<code>(C)</code> / <code>(c)</code> / <code>(ॱ)</code> / <code>(·)</code>",
            "stack_pos": "Shoulder",
            "dotted_rep": "<span class='dotted-sample'><span class='base-circle'>◌</span><span class='mod-dot'>·</span></span>",
            "example_text": "ഓ(𑌤)(C)",
            "example_preview": "<div class='mantra-preview-box'><div class='stack-top'><span class='swara-red'>𑌤</span></div><div class='mantra-base'>ഓ<span class='mod-blue-dot'>·</span></div></div>",
            "meaning": "Upper-right shoulder pause/spacing dot attached to mantrakshara curve.",
            "color_note": "ModifierDarkBlue (#002171) on Mantrakshara"
        },
        {
            "id": "MOD-D",
            "shortcut": "(D)",
            "name": "Chevron Roof (Ʌ)",
            "glyph": "\uE006",
            "codepoint": "U+E006 / U+0245 / Ʌ",
            "input_methods": "<code>(D)</code> / <code>(d)</code> / <code>(Ʌ)</code>",
            "stack_pos": "Stacked Above",
            "dotted_rep": "<span class='dotted-sample'><span class='mod-sup-center'>Ʌ</span><span class='base-circle'>◌</span></span>",
            "example_text": "ഹോ()(D)",
            "example_preview": "<div class='mantra-preview-box'><div class='stack-top'><span class='swara-red'></span></div><div class='mantra-base'>ഹോ<span class='mod-blue-sup'>Ʌ</span></div></div>",
            "meaning": "Overhead chevron roof marker indicating roof-tone modulation.",
            "color_note": "ModifierDarkBlue (#002171) on Mantrakshara"
        },
        {
            "id": "MOD-E",
            "shortcut": "(E)",
            "name": "Phrasing Heavy Danda (┃)",
            "glyph": "\uE002",
            "codepoint": "U+E002 / U+2503 / ┃",
            "input_methods": "<code>(E)</code> / <code>(e)</code> / <code>(┃)</code>",
            "stack_pos": "Inline",
            "dotted_rep": "<span class='dotted-sample'><span class='base-circle'>◌</span><span class='mod-inline'>┃</span></span>",
            "example_text": "മാ(𑌚)(E)",
            "example_preview": "<div class='mantra-preview-box'><div class='stack-top'><span class='swara-red'>𑌚</span></div><div class='mantra-base'>മാ<span class='mod-blue-inline'>┃</span></div></div>",
            "meaning": "Phrasing heavy vertical line inline with mantrakshara.",
            "color_note": "ModifierDarkBlue (#002171) on Mantrakshara"
        },
        {
            "id": "MOD-F",
            "shortcut": "(F)",
            "name": "Light Vertical Line (╷)",
            "glyph": "\uE002",
            "codepoint": "U+E002 / U+2577 / ╷",
            "input_methods": "<code>(F)</code> / <code>(f)</code> / <code>(╷)</code>",
            "stack_pos": "Inline",
            "dotted_rep": "<span class='dotted-sample'><span class='base-circle'>◌</span><span class='mod-inline'>╷</span></span>",
            "example_text": "മാ(𑌚)(F)",
            "example_preview": "<div class='mantra-preview-box'><div class='stack-top'><span class='swara-red'>𑌚</span></div><div class='mantra-base'>മാ<span class='mod-blue-inline'>╷</span></div></div>",
            "meaning": "Light phrasing vertical tone separator.",
            "color_note": "ModifierDarkBlue (#002171) on Mantrakshara"
        },
        {
            "id": "MOD-G",
            "shortcut": "(G)",
            "name": "Descending Tone Slash (\\ / ⟍)",
            "glyph": "\uE003",
            "codepoint": "U+E003 / U+005C / \\",
            "input_methods": "<code>(G)</code> / <code>(g)</code> / <code>(\\)</code> / <code>(⟍)</code>",
            "stack_pos": "Stacked Below",
            "dotted_rep": "<span class='dotted-sample'><span class='base-circle'>◌</span><span class='mod-sub'>\\</span></span>",
            "example_text": "ആഇഷോ()(G)",
            "example_preview": "<div class='mantra-preview-box'><div class='stack-top'><span class='swara-red'></span></div><div class='mantra-base'>ആഇഷോ<span class='mod-blue-sub'>\\</span></div></div>",
            "meaning": "Downward falling diagonal slash attached beneath the mantrakshara baseline (descending pitch).",
            "color_note": "ModifierDarkBlue (#002171) on Mantrakshara"
        },
        {
            "id": "MOD-H",
            "shortcut": "(H)",
            "name": "Swarita Tone Accent (॑ / |)",
            "glyph": "\uE00C",
            "codepoint": "U+E00C / U+0951 / ॑",
            "input_methods": "<code>(H)</code> / <code>(h)</code> / <code>(L)</code> / <code>(|)</code> / <code>(॑)</code>",
            "stack_pos": "Stacked Above",
            "dotted_rep": "<span class='dotted-sample'><span class='mod-sup-center'>|</span><span class='base-circle'>◌</span></span>",
            "example_text": "ദാ(𑌚𑌿)(H)",
            "example_preview": "<div class='mantra-preview-box'><div class='stack-top'><span class='swara-red'>𑌚𑌿</span></div><div class='mantra-base'>ദാ<span class='mod-blue-sup'>|</span></div></div>",
            "meaning": "Upper tone Swarita vertical stroke situated on top of the preceding mantrakshara.",
            "color_note": "ModifierDarkBlue (#002171) on Mantrakshara"
        },
    ]

    # Modifier HTML Rows
    modifier_rows_html = []
    for m in modifiers:
        stack_badge = "badge-above" if m['stack_pos'] == "Stacked Above" else "badge-below" if m['stack_pos'] == "Stacked Below" else "badge-shoulder" if m['stack_pos'] == "Shoulder" else "badge-inline"
        modifier_rows_html.append(f"""
        <tr class="mod-row" data-type="modifier">
            <td class="idx-col"><strong>{m['id']}</strong></td>
            <td><strong class="shortcut-tag">{m['shortcut']}</strong></td>
            <td><strong>{m['name']}</strong><div class="mod-desc">{m['meaning']}</div></td>
            <td>{m['input_methods']}</td>
            <td class="glyph-cell"><span class="swara-glyph mod-glyph">{m['glyph']}</span></td>
            <td class="dotted-cell">{m['dotted_rep']}</td>
            <td class="preview-cell">{m['example_preview']}</td>
            <td><code>{m['codepoint']}</code></td>
            <td><span class="badge {stack_badge}">{m['stack_pos']}</span></td>
        </tr>
        """)

    # Ayugma Bases table
    ayugma_bases = [
        ("A01", "Ka", "ക", "𑌕", "U+11315", "Avaroham (അവരോഹം)", "Odd swara"),
        ("A02", "Kha", "ഖ", "𑌖", "U+11316", "Anvangulyam (അന്വംഗുല്യം)", "Odd swara"),
        ("A03", "Ca", "ച", "𑌚", "U+1131A", "Abhitam (അഭീതം)", "Odd swara"),
        ("A04", "Cha", "ഛ", "𑌛", "U+1131B", "Abhram (അഭ്രം)", "Odd swara"),
        ("A05", "Tta", "ട", "𑌟", "U+1131F", "Anishtam (അനിഷ്ടം)", "Odd swara"),
        ("A06", "Ttha", "ഠ", "𑌠", "U+11320", "Apratishtham (അപ്രതിഷ്ഠം)", "Odd swara"),
        ("A07", "Dda", "ഡ", "𑌡", "U+11321", "Avipriyam (അവിപ്രിയം)", "Odd swara"),
        ("A08", "Ddha", "ഢ", "𑌢", "U+11322", "Antam (അന്തം)", "Odd swara"),
        ("A09", "Nna", "ണ", "𑌣", "U+11323", "Namanam (നമനം)", "Odd swara"),
        ("A10", "Ta", "ത", "𑌤", "U+11324", "Atatam (അതതം)", "Odd swara"),
        ("A11", "Tha", "ഥ", "𑌥", "U+11325", "Astam (അസ്തം)", "Odd swara"),
        ("A12", "Da", "ദ", "𑌦", "U+11326", "Danam (ദാനം)", "Odd swara"),
        ("A13", "Sha (Mal)", "ശ", "ശ", "U+0D36", "Saa / Shaa (ശ-based manuscript)", "Manuscript Base"),
        ("A14", "Ssa", "ഷ", "𑌷", "U+11337", "Shastam (ശസ്തം)", "Odd swara"),
        ("A15", "Pla (Vedic)", "പ്ല", "\uE020", "U+E020", "Plutam (പ്ലുതം - Vedic custom glyph)", "Manuscript Base"),
        ("A16", "Nga", "ങ", "𑌙", "U+11319", "Nga base", "Odd swara"),
        ("A17", "Tra", "ത്ര", "\uE01D", "U+E01D", "Tra conjunct (𑌤𑍍𑌰)", "Conjunct"),
        ("A18", "Ra", "ര", "𑌰", "U+11330", "Ra base", "Odd swara"),
        ("A19", "Kra", "ക്ര", "\uE01E", "U+E01E", "Kra conjunct (𑌕𑍍𑌰)", "Conjunct"),
    ]

    ayugma_rows_html = []
    for aid, m_name, m_char, g_char, hex_code, meaning, notes in ayugma_bases:
        ayugma_rows_html.append(f"""
        <tr>
            <td class="idx-col"><strong>{aid}</strong></td>
            <td><strong>{m_name}</strong></td>
            <td style="font-family:'Noto Serif Malayalam'; font-size:22px; font-weight:bold;">{m_char}</td>
            <td class="glyph-cell"><span class="swara-glyph swara-red">{g_char}</span></td>
            <td><code>{hex_code}</code></td>
            <td>{meaning}</td>
            <td><span class="badge badge-base">{notes}</span></td>
        </tr>
        """)

    # Manuscript Ligatures table
    ligatures = [
        ("LIG-01", "Shaa (Sha+AA)", "\uE010", "U+E010 / 0D36+1133E", "ശ + 𑌾 (Grantha separate right arm)", "Stacked Above"),
        ("LIG-02", "Shi (Sha+I)", "\uE011", "U+E011 / 0D36+1133F", "ശ + 𑌿 (Grantha authentic iMatra attached to right lobe)", "Stacked Above"),
        ("LIG-03", "Shii (Sha+II)", "\uE012", "U+E012 / 0D36+11340", "ശ + 𑍀 (Grantha iiMatra attached to right lobe)", "Stacked Above"),
        ("LIG-04", "Sha+Virama", "\uE013", "U+E013 / 0D36+1134D", "ശ + ് (Malayalam virama)", "Stacked Above"),
        ("LIG-05", "Plaa (Pla+AA)", "\uE021", "U+E021 / Pla+1133E", "Vedic Pla + Grantha separate right arm", "Stacked Above"),
        ("LIG-06", "Pli (Pla+I)", "\uE022", "U+E022 / Pla+1133F", "pi_gran + subjoined Malayalam La", "Stacked Above"),
        ("LIG-07", "Plii (Pla+II)", "\uE023", "U+E023 / Pla+11340", "pii_gran + subjoined Malayalam La", "Stacked Above"),
        ("LIG-08", "Shruu (ശ്രൂ)", "\uE027", "U+E027", "Clean composite without dotted circles", "Stacked Above"),
        ("LIG-09", "Shrr (ശ്രൃ)", "\uE028", "U+E028", "Clean composite without dotted circles", "Stacked Above"),
        ("LIG-10", "Nna+U (ണു)", "\uE029", "U+E029", "Nna with right-attached uMatra without collision", "Stacked Above"),
    ]

    liga_rows_html = []
    for lid, lname, lglyph, lcode, ldesc, lpos in ligatures:
        liga_rows_html.append(f"""
        <tr>
            <td class="idx-col"><strong>{lid}</strong></td>
            <td><strong>{lname}</strong></td>
            <td class="glyph-cell"><span class="swara-glyph swara-red">{lglyph}</span></td>
            <td><code>{lcode}</code></td>
            <td>{ldesc}</td>
            <td><span class="badge badge-above">{lpos}</span></td>
        </tr>
        """)

    # Swara Markers Rows
    swara_rows_html = []
    for idx, r in enumerate(rows, 1):
        marker = r.get("marker", "")
        count = r.get("count", "")
        hex_str = r.get("grantha_hex", "")
        text_str = r.get("grantha_text", "")
        match_id = r.get("sheet_entry_match", "")

        if any(c in marker for c in ["प्ल", "प्लि", "प्ली", "प्ला"]):
            cat = "Pla Hybrid Base"
            badge_cls = "badge-pla"
        elif "श" in marker:
            cat = "Sha Malayalam Base"
            badge_cls = "badge-sha"
        elif match_id:
            cat = f"Ayugma Base ({match_id})"
            badge_cls = "badge-base"
        elif len(hex_str.split()) > 1:
            cat = "Compound / Ligature"
            badge_cls = "badge-liga"
        else:
            cat = "Grantha Swara"
            badge_cls = "badge-base"

        swara_rows_html.append(f"""
        <tr data-type="swara">
            <td class="idx-col">{idx}</td>
            <td><strong>({marker})</strong></td>
            <td class="glyph-cell"><span class="swara-glyph swara-red">{text_str}</span></td>
            <td><code>{hex_str}</code></td>
            <td><span class="badge {badge_cls}">{cat}</span></td>
            <td class="count-cell">{count}</td>
        </tr>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Jaimineeya Swara Font — Complete Glyph Inventory & Modifiers Review</title>
<style>
    @font-face {{
        font-family: 'JaimineeyaSwara';
        src: url('../../../fonts/JaimineeyaSwara.ttf') format('truetype');
    }}
    @font-face {{
        font-family: 'Noto Serif Malayalam';
        src: url('../../../fonts/NotoSerifMalayalam-Regular.ttf') format('truetype');
    }}

    :root {{
        --bg-main: #f8fafc;
        --card-bg: #ffffff;
        --text-main: #0f172a;
        --text-muted: #64748b;
        --primary-blue: #002171;
        --swara-red: #c62828;
        --border-color: #e2e8f0;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        background: var(--bg-main);
        color: var(--text-main);
        padding: 30px 20px;
        line-height: 1.5;
    }}
    .container {{
        max-width: 1300px;
        margin: 0 auto;
    }}
    header {{
        background: linear-gradient(135deg, #002171 0%, #1e3a8a 100%);
        color: white;
        padding: 36px 32px;
        border-radius: 16px;
        margin-bottom: 30px;
        box-shadow: 0 10px 25px -5px rgba(0, 33, 113, 0.2);
    }}
    h1 {{
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 8px;
    }}
    .subtitle {{
        font-size: 15px;
        color: #bfdbfe;
        max-width: 900px;
        line-height: 1.6;
    }}
    .color-legend {{
        display: flex;
        gap: 20px;
        margin-top: 18px;
        flex-wrap: wrap;
    }}
    .legend-item {{
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        font-weight: 600;
        background: rgba(255, 255, 255, 0.12);
        padding: 6px 14px;
        border-radius: 20px;
        backdrop-filter: blur(4px);
    }}
    .legend-dot {{
        width: 12px;
        height: 12px;
        border-radius: 50%;
    }}
    .dot-red {{ background: #ef4444; border: 2px solid white; }}
    .dot-blue {{ background: #60a5fa; border: 2px solid white; }}

    .nav-tabs {{
        display: flex;
        gap: 10px;
        margin-bottom: 24px;
        border-bottom: 2px solid var(--border-color);
        padding-bottom: 8px;
        overflow-x: auto;
    }}
    .tab-btn {{
        background: transparent;
        border: none;
        padding: 10px 18px;
        font-size: 15px;
        font-weight: 700;
        color: var(--text-muted);
        cursor: pointer;
        border-radius: 8px;
        transition: all 0.2s ease;
    }}
    .tab-btn:hover {{
        background: #e2e8f0;
        color: var(--text-main);
    }}
    .tab-btn.active {{
        background: var(--primary-blue);
        color: white;
    }}

    .section-card {{
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        margin-bottom: 30px;
        overflow: hidden;
    }}
    .section-header {{
        background: #f8fafc;
        border-bottom: 1px solid var(--border-color);
        padding: 16px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .section-title {{
        font-size: 18px;
        font-weight: 700;
        color: var(--text-main);
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .section-tag {{
        font-size: 12px;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        text-transform: uppercase;
    }}
    .tag-modifiers {{ background: #e0e7ff; color: #3730a3; }}
    .tag-ayugma {{ background: #fee2e2; color: #991b1b; }}
    .tag-liga {{ background: #dbeafe; color: #1e40af; }}
    .tag-all {{ background: #dcfce7; color: #166534; }}

    table {{
        width: 100%;
        border-collapse: collapse;
        text-align: left;
    }}
    th {{
        background: #f1f5f9;
        color: #475569;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 14px 18px;
        border-bottom: 1px solid var(--border-color);
    }}
    td {{
        padding: 14px 18px;
        border-bottom: 1px solid #f1f5f9;
        font-size: 14px;
        vertical-align: middle;
    }}
    tr:hover {{
        background: #f8fafc;
    }}
    .idx-col {{
        color: #94a3b8;
        font-size: 13px;
        font-weight: 600;
        width: 75px;
    }}
    .glyph-cell {{
        font-size: 34px;
        line-height: 1;
        width: 100px;
        text-align: center;
    }}
    .swara-glyph {{
        font-family: 'JaimineeyaSwara', serif;
    }}
    .swara-red {{
        color: var(--swara-red);
        font-weight: bold;
    }}
    .mod-glyph {{
        color: var(--primary-blue);
    }}

    .dotted-cell {{
        text-align: center;
        width: 130px;
    }}
    .dotted-sample {{
        position: relative;
        display: inline-flex;
        flex-direction: column;
        align-items: center;
        vertical-align: middle;
        line-height: 1;
        background: #ffffff;
        padding: 6px 14px;
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }}
    .dotted-sample .base-circle {{
        font-family: 'Noto Serif Malayalam', 'Segoe UI Symbol', sans-serif;
        font-size: 22px;
        color: #64748b;
        letter-spacing: 2px;
    }}
    .dotted-sample .arc-tie {{
        color: var(--primary-blue);
        font-family: 'JaimineeyaSwara', serif;
        font-size: 26px;
        line-height: 0.8;
        margin-bottom: -4px;
    }}
    .dotted-sample .mod-sup-center {{
        color: var(--primary-blue);
        font-size: 18px;
        line-height: 0.8;
        margin-bottom: 2px;
        font-weight: bold;
    }}
    .dotted-sample .mod-dot {{
        color: var(--primary-blue);
        font-size: 24px;
        line-height: 0;
        vertical-align: 4px;
        margin-left: 2px;
    }}
    .dotted-sample .mod-sub {{
        color: var(--primary-blue);
        font-size: 18px;
        font-weight: bold;
        margin-top: 2px;
    }}
    .dotted-sample .mod-inline {{
        color: var(--primary-blue);
        font-size: 20px;
        font-weight: bold;
        margin-left: 4px;
    }}

    .preview-cell {{
        width: 180px;
    }}
    .mantra-preview-box {{
        display: inline-flex;
        flex-direction: column;
        align-items: center;
        background: #f8fafc;
        border: 1px solid var(--border-color);
        padding: 6px 14px;
        border-radius: 8px;
        font-family: 'Noto Serif Malayalam', serif;
    }}
    .stack-top {{
        font-size: 17px;
        line-height: 1.1;
        margin-bottom: 1px;
    }}
    .mantra-base {{
        font-size: 20px;
        font-weight: bold;
        color: #0f172a;
        line-height: 1.2;
    }}
    .mod-arc-tie {{
        color: var(--primary-blue);
        font-family: 'JaimineeyaSwara', serif;
        font-size: 22px;
        margin-bottom: -4px;
        display: block;
    }}
    .mod-blue-sup {{
        color: var(--primary-blue);
        font-size: 14px;
        vertical-align: super;
        margin-left: 2px;
        font-weight: bold;
    }}
    .mod-blue-sub {{
        color: var(--primary-blue);
        font-size: 16px;
        vertical-align: sub;
        margin-left: 2px;
        font-weight: bold;
    }}
    .mod-blue-dot {{
        color: var(--primary-blue);
        font-size: 22px;
        line-height: 0;
        vertical-align: 3px;
        margin-left: 2px;
    }}
    .mod-blue-inline {{
        color: var(--primary-blue);
        font-size: 18px;
        font-weight: bold;
        margin-left: 3px;
    }}

    .shortcut-tag {{
        font-family: ui-monospace, monospace;
        font-size: 15px;
        color: #3730a3;
        background: #e0e7ff;
        padding: 4px 10px;
        border-radius: 6px;
        border: 1px solid #c7d2fe;
    }}
    .mod-desc {{
        font-size: 12px;
        color: var(--text-muted);
        font-weight: normal;
        margin-top: 4px;
        line-height: 1.4;
    }}
    code {{
        font-family: ui-monospace, monospace;
        background: #f1f5f9;
        color: #0f172a;
        padding: 3px 6px;
        border-radius: 4px;
        font-size: 12px;
        border: 1px solid #e2e8f0;
    }}
    .badge {{
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }}
    .badge-above {{ background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }}
    .badge-below {{ background: #faf5ff; color: #7e22ce; border: 1px solid #e9d5ff; }}
    .badge-shoulder {{ background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }}
    .badge-inline {{ background: #f8fafc; color: #475569; border: 1px solid #cbd5e1; }}
    .badge-base {{ background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }}
    .badge-sha {{ background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }}
    .badge-pla {{ background: #ecfeff; color: #0e7490; border: 1px solid #a5f3fc; }}
    .badge-liga {{ background: #f5f3ff; color: #6d28d9; border: 1px solid #ddd6fe; }}
    .count-cell {{ font-weight: 700; color: #0f172a; text-align: center; }}
</style>
</head>
<body>
<div class="container">

<header>
    <h1>Jaimineeya Vedic Swara Font (JaimineeyaSwara.ttf) — Complete Glyph Inventory</h1>
    <div class="subtitle">
        Comprehensive reference table and visual preview for all Jaimineeya Samaveda swara markers, manuscript overrides (Pla/Sha), ligatures, and the 8 Canonical Vedic Swara Modifiers (A..H).
    </div>
    <div class="color-legend">
        <div class="legend-item"><span class="legend-dot dot-red"></span> Pure Swara Pitch Markers: Bold Red (#c62828) — Stacked Above</div>
        <div class="legend-item"><span class="legend-dot dot-blue"></span> Vedic Swara Modifiers (A..H): Dark Blue (#002171) — Attached to Mantrakshara</div>
    </div>
</header>

<div class="nav-tabs">
    <button class="tab-btn active" onclick="showTab('modifiers-section')">1. Swara Modifiers (A..H)</button>
    <button class="tab-btn" onclick="showTab('ayugma-section')">2. Ayugma Bases (A01..A19)</button>
    <button class="tab-btn" onclick="showTab('ligatures-section')">3. Manuscript Ligatures</button>
    <button class="tab-btn" onclick="showTab('all-swaras-section')">4. Full Swara Inventory ({len(rows)})</button>
</div>

<!-- SECTION 1: MODIFIERS -->
<div id="modifiers-section" class="section-card">
    <div class="section-header">
        <div class="section-title">Canonical 8 Vedic Swara Modifiers (A..H)</div>
        <span class="section-tag tag-modifiers">Active Modifiers</span>
    </div>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Shortcut</th>
                <th>Name & Tone Meaning</th>
                <th>Input Methods</th>
                <th style="text-align: center;">Direct Glyph</th>
                <th style="text-align: center;">Dotted Representation (◌)</th>
                <th>Mantrakshara Stacking Preview</th>
                <th>Codepoint</th>
                <th>Position</th>
            </tr>
        </thead>
        <tbody>
            {"".join(modifier_rows_html)}
        </tbody>
    </table>
</div>

<!-- SECTION 2: AYUGMA BASES -->
<div id="ayugma-section" class="section-card" style="display:none;">
    <div class="section-header">
        <div class="section-title">Ayugma Swara Bases (A01..A19)</div>
        <span class="section-tag tag-ayugma">Odd Swaras</span>
    </div>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Malayalam Base</th>
                <th style="text-align: center;">Grantha Glyph</th>
                <th>Codepoint</th>
                <th>Traditional Meaning</th>
                <th>Category</th>
            </tr>
        </thead>
        <tbody>
            {"".join(ayugma_rows_html)}
        </tbody>
    </table>
</div>

<!-- SECTION 3: MANUSCRIPT LIGATURES -->
<div id="ligatures-section" class="section-card" style="display:none;">
    <div class="section-header">
        <div class="section-title">Manuscript Overrides & Complex Ligatures (Sha / Pla / Kra / Tra)</div>
        <span class="section-tag tag-liga">Manuscript Ligatures</span>
    </div>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Ligature Name</th>
                <th style="text-align: center;">Rendered Glyph</th>
                <th>Codepoint / Formula</th>
                <th>Typographic Composition</th>
                <th>Stacking Position</th>
            </tr>
        </thead>
        <tbody>
            {"".join(liga_rows_html)}
        </tbody>
    </table>
</div>

<!-- SECTION 4: FULL SWARA INVENTORY -->
<div id="all-swaras-section" class="section-card" style="display:none;">
    <div class="section-header">
        <div class="section-title">Full Samhita Swara Frequency & Character Review</div>
        <span class="section-tag tag-all">All Markers ({len(rows)})</span>
    </div>
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Input Marker</th>
                <th style="text-align: center;">Rendered Glyph</th>
                <th>Grantha Hex</th>
                <th>Category</th>
                <th style="text-align: center;">Corpus Frequency</th>
            </tr>
        </thead>
        <tbody>
            {"".join(swara_rows_html)}
        </tbody>
    </table>
</div>

</div>

<script>
function showTab(sectionId) {{
    var secs = document.querySelectorAll('.section-card');
    for (var i = 0; i < secs.length; i++) {{
        secs[i].style.display = 'none';
    }}
    var btns = document.querySelectorAll('.tab-btn');
    for (var j = 0; j < btns.length; j++) {{
        btns[j].classList.remove('active');
    }}
    document.getElementById(sectionId).style.display = 'block';
    event.currentTarget.classList.add('active');
}}
</script>
</body>
</html>
"""

    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Saved HTML Glyph Table: {OUT_HTML}")
    
    # Copy to artifact directory for browser viewing
    art_html = ARTIFACT_DIR / "glyph_table.html"
    with open(art_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Copied to artifact directory: {art_html}")


if __name__ == "__main__":
    render_image_grid()
    render_html_table()
