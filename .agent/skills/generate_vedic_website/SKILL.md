---
name: generate_vedic_website
description: Instructions for maintain and generating the Jaimineeya static site (Gateway, Curation, Samam display).
---

# Generate Vedic Website Skill

This skill covers the mechanics of translating the Source of Truth JSON into the static GitHub Pages layout (`src/generate_website.py`) for Samhita and Aaranam.

## 1. Site Architecture
*   **Dual Sub-site Model**: The static archive maintains two primary independent sub-sites: **Samhita** (`docs/samhita/`) and **Aaranam** (`docs/aranam/`).
*   **Gateway Landing Page**: A manually maintained premium landing page at `docs/index.html` provides the primary entry point to both collections.
*   **Common Assets**: CSS and JS are shared locally within each sub-site to ensure full portability and offline functionality.

## 2. UI/UX & Typography Standards
*   **Samam Count Display**: 
    *   **Homepage**: Aggregate Samam counts (e.g., `19 साम`) are displayed on individual Kandah Cards. Parva headers remain clean.
    *   **Kandah Pages**: Display the current count in a `<span class="sama-count">` inside the `<h1>` header.
    *   **Navigation Cleaning**: The sticky top-right navigation title must avoid showing Samam counts. Ensure counts are wrapped in `.section-samam-count` or `.sama-count` so the JavaScript in `main.js` can dynamically strip them from the navigation bar.
*   **Typography Rules**:
    *   **Sanskrit Text/Labels**: Use class `.sanskrit-text` (Adishila Vedic / Serif).
    *   **Numerals/UI Counters**: Use class `.number`, `.count`, or `.stat-value` (Adishila San Vedic / Sans-serif).
    *   **Font Variables**: Styling relies on CSS variables in `styles.css`. Update the base template (`templates/html/Devanagari_main_html.template`) for structural changes.

## 3. Curation & Custom Collections (Sooktamala)
*   **Tool**: Use `src/curate_jsv.py` to generate bespoke JSON collections (e.g., *Ritu Shanti Japam*).
*   **Filtering (P.K.S)**: Uses `Parva.Kandah.Samam` identifiers to isolate specific mantras.
*   **Grouping Rule**: If consecutive Samams in a filter file belong to the same original Arsheyam (Subsection), the tool groups them under a **single Arsheyam header** in the output to avoid redundant repetition.
*   **Metadata Stripping**: Collections usually drop Rik text and detailed metadata (Rishi/Devata/Chandas) to present a clean text for recitation (Japam).

## 4. Generation Commands
*   **Samhita**: `python src/generate_website.py --samhita -o docs/samhita`
*   **Aaranam**: `python src/generate_website.py --aaranam -o docs/aranam`
*   **Custom Collection**: `python src/curate_jsv.py --sources data/output/Vargeekaran.json --filter logic.txt --output docs/custom/`
