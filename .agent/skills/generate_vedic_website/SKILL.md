---
name: generate_vedic_website
description: Instructions for maintaining and generating the Jaimineeya static site (Varnanukramanika, Typography).
---

# Generate Vedic Website Skill

This skill covers the mechanics of translating the Source of Truth JSON into the static GitHub Pages layout (`src/generate_website.py`).

## 1. Site Architecture
*   The site uses a dual sub-site approach: one for **Samhita** (`docs/samhita/`) and one for **Aaranam** (`docs/aranam/`).
*   There is a single static Gateway landing page (`docs/index.html`).

## 2. Indices Generation (Varnanukramanika)
*   The website generator abstracts the JSON into `Parva`, `Kandah`, `Arsheyam` objects via `JSVParser`.
*   It generates cross-referenced Alphabetical Indices (Varnanukramanika) based on the `Vargeekaran.json` metadata block `rik_classifications`.
*   **Rule**: Always maintain the numeric `Global_Rik_Num` mappings when updating HTML links, guaranteeing a robust "Jump To" interface.

## 3. Typography Rules
*   Mantra text, standard Sanskrit, and Labels must use class `.sanskrit-text` -> outputs **Adishila Vedic** (Serif font).
*   Numerals, counters, and UI Elements must use class `.sanskrit-numeral` -> outputs **Adishila San Vedic** (Sans-serif font).
*   CSS styling relies on a predefined variable indirection system. Avoid `!important`; update the CSS template strings in `src/generate_website.py` logically by modifying specific class definitions.
