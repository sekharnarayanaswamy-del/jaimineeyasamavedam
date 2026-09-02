# Malayalam Jaimineeya Samavedam: Processing Rules & Pipeline Specification

This document provides a comprehensive reference for all automated and manual processing rules governing Malayalam text generation, orthography, transliteration, and rendering in the Jaimineeya Samavedam project.

---

## 1. Automated Orthography & Transliteration Rules

Implemented in [`src/malayalam/ml_transliterate.py`](file:///c:/Users/sekha/OneDrive/Documents/GitHub/jaimineeyasamavedam/src/malayalam/ml_transliterate.py) within `post_process_malayalam()` and `normalize_combining_marks()`:

| Rule | Description | Input $\rightarrow$ Output |
| :--- | :--- | :--- |
| **Vocalic R / Repha** | Converts `ർ` or `ര\u0D4D` before consonants (`ക`–`ഹ`) to the traditional Vedic Repha symbol `൪`. | `र्हा` $\rightarrow$ `൪ഹാ`<br>`र्वा` $\rightarrow$ `൪വാ` |
| **Vedic LLA $\rightarrow$ ZHA** | Maps Devanagari Vedic `ळ` (`U+0933`) $\rightarrow$ Malayalam `ഴ` (`U+0D34`) and `ൾ` $\rightarrow$ `ഴ്`. | `ഇള` / `इळा` $\rightarrow$ `ഇഴാ`<br>`ഇൾ` $\rightarrow$ `ഇഴ്` |
| **Root *Gira-* Shortening** | Shortens long `ഗീ` to short `ഗി` before `രാഃ` in words derived from roots *gir* / *giraḥ* (speech/song of praise). | `ഗീരാഃ` $\rightarrow$ `ഗിരാഃ`<br>`ങ്ഗീരാഃ` $\rightarrow$ `ങ്ഗിരാഃ`<br>`യോഗീരാഃ` $\rightarrow$ `യോഗിരാഃ` |
| **Conjunct *Dvi-* Shortening** | Shortens long `ദ്വീ` to short `ദ്വി` in words from prefix/root *dvi* (द्वि). | `ദ്വീ` $\rightarrow$ `ദ്വി`<br>`തദ്വീ` $\rightarrow$ `തദ്വി`<br>`ദ്വീവിഡ്ഢി` $\rightarrow$ `ദ്വിവിഡ്ഢി` |
| ***Viśā* Shortening** | Shortens long `വീശാ` to short `വിശാ` in words derived from root *viś* (विशा). | `വീശാ` $\rightarrow$ `വിശാ`<br>`വീശാഇവാ` $\rightarrow$ `വിശാഇവാ` |
| **Conjunct *Jñi-* Shortening** | Shortens long `ജ്ഞീ` to short `ജ്ഞി` in conjunct syllables (such as *yajñiya*). | `ജ്ഞീ` $\rightarrow$ `ജ്ഞി`<br>`യാജ്ഞീ` $\rightarrow$ `യാജ്ഞി` |
| **Word-Final AA Shortening** | Converts trailing long `ാ` to short `അ` before dandas, spaces, or line ends in titles. | `സംഹിതാ` $\rightarrow$ `സംഹിത`<br>`മാലാ` $\rightarrow$ `മാല` |
| **Word-Final Halant Ma** | Normalizes word-final `മ്` before punctuation/spaces/end to anusvara `ം` to prevent orphaned combining marks. | `സൂക്തമ്` $\rightarrow$ `സൂക്തം` |
| **Word-Final Halant Na** | Normalizes word-final `ന്` before dandas or line ends to chillu-n `ൻ`. | `ന്।` $\rightarrow$ `ൻ।`<br>`ന്॥` $\rightarrow$ `ൻ॥` |
| **Duplicate Matra Collapse** | Collapses accidental consecutive `ാ+` into a single `ാ`. | `ാാ` $\rightarrow$ `ാ` |
| **Virama Before Vocalic R** | Removes spurious virama before `ൃ` (`U+0D43`) or `ൄ` (`U+0D44`). | `്ൃ` $\rightarrow$ `ൃ`<br>`്ൄ` $\rightarrow$ `ൄ` |
| **Combining Mark Cleanup** | Eliminates dotted-circle artifacts caused by viramas before matras, detached marks, or NFD decomposition. | `ാെ` $\rightarrow$ `ോ`<br>`ാേ` $\rightarrow$ `ൌ` |
| **Numeral Conversion** | Translates Devanagari (`०-९`) and Malayalam (`൦-൯`, excluding `൪`) digits to standard ASCII numerals. | `॥१॥` $\rightarrow$ `॥ 1 ॥`<br>`॥൧॥` $\rightarrow$ `॥ 1 ॥` |

---

## 2. Danda & Word-Boundary Mechanics

Implemented in [`src/malayalam/ml_text.py`](file:///c:/Users/sekha/OneDrive/Documents/GitHub/jaimineeyasamavedam/src/malayalam/ml_text.py):

- **Danda Masking & Restoration**: Dandas (`।` and `॥`) are protected via internal placeholder tokens during aksharamukha transliteration to prevent script confusion or character loss.
- **Trailing Anusvara Re-attachment**: Source manuscripts often transcribe a trailing anusvara as a separate token with its own swara (e.g. `താ(ത) മ് ।`). The pipeline re-attaches `മ്` to the parent word (`താം`) so the combining sign `ം` (`U+0D02`) always attaches to a valid Malayalam consonant base.
- **Verse Number Spacing**: Standardizes verse numbers within dandas to standard spacing (e.g., `॥ 1 ॥`).

---

## 3. Swara Marker & Modifier System

Implemented in [`src/malayalam/ml_map.py`](file:///c:/Users/sekha/OneDrive/Documents/GitHub/jaimineeyasamavedam/src/malayalam/ml_map.py) and [`src/render_pdf.py`](file:///c:/Users/sekha/OneDrive/Documents/GitHub/jaimineeyasamavedam/src/render_pdf.py):

- **Parenthesized Swara Markers**: Markers enclosed in parentheses (e.g., `(𑌤)`, `(𑌟𑌾)`, `(ശ)`) represent Grantha/Malayalam swara notations and are mapped directly to custom Vedic font glyphs.
- **Melodic Arcs & Slurs (MOD-A, MOD-A1, MOD-A2)**:
  - **`MOD-A` (`(A)` / `⁀`, `U+E004`)**: Syllable-spanning arc bridging across to the following syllable (`left: 100%; transform: translateX(-40%)`).
  - **`MOD-A1` (`(A1)`, `U+E00D`)**: Syllable-spanning arc across a danda separator (`left: 100%; transform: translateX(5%)`).
  - **`MOD-A2` (`(A2)`, `U+E02E`)**: Overhead curved arc placed directly centered on top of the single conjunct syllable itself (e.g., `ഹൊ(A2)`, `left: 50%; transform: translateX(-50%)`).
- **Micro-modifier Placement**: Chant modifiers such as `·` (MOD-C), `┃` (MOD-E), `\` (MOD-G), `↗` (MOD-D1), `✓` (MOD-D2), `⫽` (MOD-I), `¯` (MOD-J), `⨯` (MOD-K) are parsed into dedicated CSS classes/spans to ensure vertical and horizontal geometric synchronization with the Malayalam base aksharas.

---

## 4. Manual Curation Principles (Excluded from Automated Scripts)

To protect precise manuscript fidelity and avoid overwriting valid chanting variations, the following rules are **strictly manual** and must **not** be automated via blanket regex in the pipeline:

1. **`വ്യാ` vs `വ്യ`**:
   - In many words with conjunct `വ്യ` (`vy`), Vedic Malayalam chanting uses short `അ` (`വ്യ`) instead of long `ആ` (`വ്യാ`) (e.g., `ഹവ്യദാ`, `ഹവ്യവാഹ`, `നവ്യ`).
   - However, specific chant endings, sandhis, and elongated notes are legitimate exceptions.
   - **Policy**: All corrections are maintained manually in the input files (`data/input/Malayalam/`). Automated scripts must never overwrite `വ്യാ` $\rightarrow$ `വ്യ`.

2. **Short E & O Swaras (`െ` vs `േ`, `ൊ` vs `ോ`)**:
   - Short vowels (ह्रस्व) are standard in Malayalam chanting for conjuncts, vocatives, and stobhas (`അഗ്നെ`, `സ്തൊ`, `ഹൊവാ`, `നൊ`).
   - Handled exclusively via source transcription curation, as context dictates vowel duration.

---

## 5. Malayalam Pipeline Execution Scope

Implemented in [`src/run_malayalam_pipeline.py`](file:///c:/Users/sekha/OneDrive/Documents/GitHub/jaimineeyasamavedam/src/run_malayalam_pipeline.py):

- **Default Execution**: Configured to run in **Samam-only mode** (`--modes separate --samam-only`).
- **Generated Outputs**:
  - **HTML**: `data/output/Samam_Malayalam_Samam_Malayalam.html`
  - **Plaintext TXT (Malayalam)**: `data/output/txt/Malayalam/Samam_Malayalam_Samam.txt`
  - **Devanagari TXT**: `data/output/txt/Devanagari/Samam_Malayalam_Samam.txt`
- **Bypassed**: All Rik-only (`*_Rik_*.html`) and combined (`*_Malayalam.html`) outputs are bypassed to keep execution fast and focused exclusively on the Malayalam Samam corpus.
