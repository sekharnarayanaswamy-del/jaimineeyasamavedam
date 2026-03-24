---
name: render_vedic_latex
description: Instructions for safely rendering complex Vedic accents and footnotes into LuaLaTeX.
---

# Render Vedic LaTeX Skill

This skill dictates the logic for translating parsed JSON into production-ready LaTeX for Jaimineeya Samavedam physical books via `src/render_pdf.py`.

## 1. Visarga-Accent Preprocessing (CRITICAL)
In Vedic Devanagari typesetting, when an accent (e.g., Anudatta, Swarita) follows a Visarga (`ः`), it must be visually shifted to sit atop/below the preceding vowel.
*   **Source Format**: `Wordः(1)` (Logical sequence)
*   **Rendering Need**: The script `src/utils.py` handles the `step_preprocess_visarga_accent` swap, transforming the string to `Word(1)ः` right before emitting LaTeX.
*   **Rule**: NEVER modify the logical format in the source JSON or Text file. This is purely a visual rendering transformation.

## 2. LaTeX Footnote Resolution
*   The raw text uses markers like `(s1)`.
*   These must be mapped against the `footnotes` dictionary within the JSON.
*   Convert to true LaTeX footnotes using `\footnote{...}`.

## 3. Scriptio Continua (Continuous Text)
When generating "Rik Samhita" (Continuous Text):
*   `remove_mantra_spaces()` must collapse word spaces while strictly preserving special markers such as line breaks (`\\`), structural lines (e.g., Colophons like `॥ इति ... ॥`), and footnote hooks.

## 4. Fonts
*   The system uses LuaLaTeX specifically to leverage the `fontspec` package with HarfBuzz rendering (`Renderer=Harfbuzz`).
*   Default Font: **Adishila Vedic**.
