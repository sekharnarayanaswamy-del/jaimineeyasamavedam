---
name: parse_vedic_markup
description: Guidelines for converting Jaimineeya Samavedam structured text into hierarchical JSON.
---

# Parse Vedic Markup Skill

This skill provides the standard rules for taking raw Vedic text markup and properly parsing/modifying the Python parsing scripts (e.g., `src/generate_json.py`).

## 1. Hierarchy Rules
The JSON structure must rigidly follow this path:
`Parva (SuperSection) -> Kandah (Section) -> Arsheyam (Subsection/Header) -> Samam (Mantra Sets) -> Rik (Individual verse)`

## 2. Text Markup Conventions
*   **SuperSection**: Starts with `# ` and ends with `# End of ...`
*   **Section**: Starts with `## ` and ends with `## End of ...`
*   **Subsection**: Starts with `### ` and ends with `### End of ...`
*   **Mantras**: Block starts with `# Start of Mantra Sets` and ends with `# End of Mantra Sets`.
*   **Samam boundaries**: Marked by double dandas with Devanagari numerals, e.g., `॥ २ ॥`. All pipeline components must convert Arabic numerals to Devanagari numerals when modifying text files.
*   **Dandas**: Always output `॥` instead of `||` or `| |`.

## 3. Safe Parsing Rules
*   **Invisible Characters**: Always use UTF-8 stripping for invisible Unicode characters like Zero-Width Joiners (ZWJ) that may break regex matching.
*   **Metadata Embedding**: Footnotes must appear immediately after the swara (no space). Format: `Word(Swara)(sN)`.
