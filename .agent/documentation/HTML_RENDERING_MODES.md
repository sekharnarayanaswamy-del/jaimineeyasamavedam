# HTML Rendering Modes & Typography Documentation

This document describes the architecture, typography options, and usage of the **Modern Interactive Reader** and the **Legacy Single-Column** HTML rendering modes in the Jaimineeya Samavedam pipeline.

---

## 1. Overview of HTML Rendering Modes

The pipeline provides two HTML generation templates for each supported script family (**Devanagari** and **Malayalam**):

| Script | Modern Interactive Reader (Default) | Legacy Mode (`--legacy-html`) |
| :--- | :--- | :--- |
| **Devanagari** | `templates/html/Devanagari_main_html.template` | `templates/html/Devanagari_main_html_legacy.template` |
| **Malayalam** | `templates/html/Malayalam_main_html.template` | `templates/html/Malayalam_main_html_legacy.template` |

### Mode Comparison Matrix

| Feature | Modern Interactive Reader (Default) | Legacy Mode (`--legacy-html`) |
| :--- | :--- | :--- |
| **Layout** | **2-Column Responsive Grid**: Sticky TOC sidebar + reading pane | Single-column linear layout with static top TOC |
| **Header** | Sticky header bar with dynamic navigation controls | Static text banner |
| **TOC Navigation** | Multi-level collapsible tree (Chapters, Kandahs, Samams) with Samam counts | Simple unordered bullet list at top of page |
| **Scroll-Spy** | Real-time `IntersectionObserver` highlighting active Samam & Kandah in TOC | None |
| **Font Switcher** | Live font dropdown/toggle button | None (fixed font stack) |
| **Font Resizing** | `A-`, percentage indicator (with reset), `A+` controls with localStorage persistence | None |
| **Print System** | **Fast Cached Print Modal**: Print active Kandah (~1-3 pages), active Parva, or full text via hidden iframe | Browser standard full document print |
| **Script Support** | Devanagari & Malayalam | Devanagari & Malayalam |
| **Font Embedding** | Base64-embedded fonts (`JaimineeyaSwara`, `AdishilaVedic`, `RIT Rachana`) + CDN fallback | Relative font paths |

---

## 2. Typography & Supported Fonts

Both HTML templates render authentic Vedic swaras and modifier symbols using dedicated font stacks and CSS configurations.

### 2.1 Malayalam Fonts

In Malayalam mode (`--script malayalam`), the viewer defaults to **Noto Serif Malayalam** and provides live switching via the **"Font: ..."** button across five typography stacks:

1. **Noto Serif** (`'Noto Serif Malayalam', 'Noto Sans Malayalam', serif`)
   - Google Font designed for high legibility and classical appearance.
2. **Rachana** (`'RIT Rachana', 'Rachana', 'Noto Serif Malayalam', serif`)
   - **Traditional Orthography Font**: Developed by the Rachana Institute of Typography (RIT).
   - Features complete conjunct ligatures (കൂട്ടക്ഷരങ്ങൾ) essential for classical Vedic and Sanskrit recitation texts in Malayalam script.
   - Embedded directly as base64 WOFF2 from `fonts/RIT-Rachana-Regular.woff2` and `fonts/RIT-Rachana-Bold.woff2`, with local relative paths and jsDelivr CDN fallbacks.
3. **Noto Sans** (`'Noto Sans Malayalam', 'Noto Serif Malayalam', sans-serif`)
   - Clean sans-serif Malayalam typeface.
4. **Gayathri** (`'Gayathri', 'Noto Serif Malayalam', sans-serif`)
   - Modern curved aesthetic from Swathanthra Malayalam Computing (SMC).
5. **Manjari** (`'Manjari', 'Noto Sans Malayalam', sans-serif`)
   - Rounded spiral terminal style.

### 2.2 Devanagari Fonts

In Devanagari mode (`--script devanagari`), the viewer includes:
1. **AdiShila Vedic** (`'AdishilaVedic', 'Noto Serif Devanagari', serif`)
   - Custom font designed with metric adjustments for Jaimineeya Vedic swaras and conjuncts.
2. **Noto Serif** (`'Noto Serif Devanagari', 'Tiro Devanagari Sanskrit', serif`)
3. **Tiro Sanskrit** (`'Tiro Devanagari Sanskrit', 'Noto Serif Devanagari', serif`)
4. **Noto Sans** (`'Noto Sans Devanagari', sans-serif`)

### 2.3 Vedic Swara Font

Both Devanagari and Malayalam readers use the dedicated custom font **`JaimineeyaSwara`** for swara letters and modifier glyphs:
- Embedded base64 TrueType font (`fonts/JaimineeyaSwara.ttf`).
- Supports all MOD glyphs:
  - **MOD-A / MOD-A1 / MOD-A2**: Melodic overhead arcs and danda arcs.
  - **MOD-B / MOD-B1**: Overhead tone carets and diagonal bridging slashes.
  - **MOD-C**: Upper shoulder dots.
  - **MOD-D / MOD-D1 / MOD-D2**: Overhead roof chevrons, rising strokes, check ticks.
  - **MOD-E / MOD-F**: Bold tone columns and dandas with overhead dots.
  - **MOD-G**: Under-syllable horizontal base tone bars (`bottom: 0.12em; transform: translateX(-50%) translateX(-0.16em);`).
  - **MOD-H**: High-pitch swarita markers (`top: -0.32em; left: 100%; transform: translateX(-0.40em);`).
  - **MOD-I / MOD-J / MOD-K**: Double shoulder dashes, horizontal bars, shoulder cross marks.

---

## 3. CLI Usage & Generation Flags

### 3.1 Generating Modern Interactive HTML (Default)

The pipeline defaults to generating the modern interactive reader:

```bash
# Render Malayalam Samam HTML (Modern Reader)
python -X utf8 src/render_pdf.py Malayalam_JSV/malayalam/Samam_Malayalam_out.json --script malayalam --output-mode separate -o data/output/Samam_Malayalam --samam-only --html-only

# Run the complete automated Malayalam pipeline (generates modern HTML and publishes to docs/)
python -X utf8 src/run_malayalam_pipeline.py --html-only
```

### 3.2 Generating Legacy Single-Column HTML (`--legacy-html`)

To generate the lightweight legacy single-column format, supply the `--legacy-html` flag:

```bash
# Render Malayalam using legacy mode template
python -X utf8 src/render_pdf.py Malayalam_JSV/malayalam/Samam_Malayalam_out.json --script malayalam --output-mode separate -o data/output/Samam_Malayalam_legacy --samam-only --html-only --legacy-html

# Render Devanagari using legacy mode template
python -X utf8 src/render_pdf.py data/output/Agneyam-Pavamanam_latest_out.json --script devanagari -o data/output/Samhita_legacy --html-only --legacy-html

# Run pipeline with legacy mode enabled
python -X utf8 src/run_malayalam_pipeline.py --html-only --legacy-html
```

---

## 4. Architectural Details

### 4.1 Ruby Stacking for Malayalam Samam

Malayalam Samam mantras stack Vedic swara letters above Malayalam base aksharas using CSS ruby:

```html
<ruby class="vedic-ruby">
  <rb class="akshara-base">സാ</rb>
  <rt class="swara-above">൧</rt>
</ruby>
```

```css
ruby.vedic-ruby {
  ruby-position: over;
  ruby-align: center;
  display: inline-flex;
  flex-direction: column-reverse;
  align-items: center;
  vertical-align: bottom;
}

rt.swara-above {
  font-family: var(--font-swara);
  font-size: var(--swara-size);
  color: var(--swara-red) !important;
  font-weight: 700;
  line-height: 1;
}

rb.akshara-base {
  font-family: var(--font-doc);
  font-size: var(--mantra-size);
  color: var(--primary-color);
  line-height: 1.25;
}
```

### 4.2 Fast Cached Print Engine

The modern reader avoids browser lock-up on large multi-megabyte Samhita documents by:
1. Creating a hidden `<iframe>` (`id="jsv-print-frame"`).
2. Extracting only the requested scope (active Kandah or Parva) with document styling.
3. Caching the extracted markup in a JavaScript `Map` (`printCache`).
4. Calling `.focus()` and `.print()` on the isolated frame.
5. Intercepting `Ctrl+P` / `Cmd+P` to open the print options dialog instead of printing 800+ pages unfiltered.
