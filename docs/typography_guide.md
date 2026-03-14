# Jaimineeya Samavedam Typography Guide

This document outlines the font mapping and typography rules applied across the website. Use this as a reference for fine-tuning the visual appearance.

## 🏛️ Core Fonts

| Font Family | Visual Style | Usage |
| :--- | :--- | :--- |
| **Adishila Vedic** | Traditional Serif | Sanskrit text, Mantra metadata, Traditional labels |
| **Adishila San Vedic** | Modern Sans-serif | Numerals, Counts, Navigation links, Table data |

---

## 🎨 Element Specific Mappings

### 1. Traditional Elements (Serif Look)
These elements use the traditional **Adishila Vedic** font for a classical appearance.

| Element | CSS Selector | Description |
| :--- | :--- | :--- |
| **Homepage Stats Labels** | `.stat-label` | "पर्व: (Parva)", "खण्ड: (Kandah)", etc. |
| **Mantra Metadata** | `.rik-metadata` | Purple line: "॥ वसिष्ठो मैत्रावरुणिः ... ॥" |
| **Sama Headers** | `.sama-header-text` | Green line above mantra text |
| **Mantra Numbering** | `.mantra-number` | The "॥ १ ॥" marker inside/below mantra boxes |
| **Navigation Headers** | `.classification-table th` | Headers in the Mantra classification table |
| **Traditional Values** | `.class-value` | Values inside classification tables |
| **Kandah Metadata** | `.page-subtitle`, `.sama-count` | Labels on the Kandah page: "पर्व: ... खण्ड: ...", "साम: ..." |

**Code Location:** `src/generate_website.py` around lines 921-923.
```css
.stat-label, .rik-metadata, .mantra-number, .sama-header-text, .sama-metadata-text, 
.classification-table th, .classification-table td, .class-value, .class-label, 
.page-subtitle, .sama-count {
    font-family: 'AdishilaVedic', 'Noto Serif Devanagari', serif !important;
}
```

---

### 2. Numerical & Dynamic Data (Sans Look)
These elements use the modern **Adishila San Vedic** font for maximum clarity and a scholarly index feel.

| Element | CSS Selector | Description |
| :--- | :--- | :--- |
| **Large Stats Values** | `.stat-value` | Large numbers on the homepage (e.g., "6", "125") |
| **Rank Indices** | `.rishi-rank` | The orange circles with numbers in Top 20 lists |
| **ToC / Nav Links** | `.toc-list li a`, `.nav-links a` | All numeric references in menus |
| **Summary Counts** | `.stats-summary` | Page header stats: "१७२ ऋषयः • ७१९ आर्षेयम्" |
| **Alphabetical Counts** | `.alpha-count` | Small numbers in alphabet navigation buttons |
| **Pill Counts** | `.index-link-item .stats` | Numbers in indices pills: "(172)", "(23)" |

**Code Location:** `src/generate_website.py` around lines 917-919.
```css
.stat-value, .rishi-rank, .number, .nav-links a, .toc-list li a, .jump-links a, 
.footnote-ref, .stats-summary, .stats-summary strong, .count, 
.rishi-count, .stats, .alpha-count, .item-count, .item-refs a, .item-count-badge {
    font-family: 'AdishilaSanVedic', 'Noto Sans Devanagari', 'Inter', sans-serif !important;
}
```

---

## 📐 Fine-Tuning Guide

### Homepage "Anya Vargeekaran" Pills
To adjust the size of the "Other Indices" pills on the homepage:
**Location:** `src/generate_website.py` around lines 1918-1928.

```css
.index-link-item .title {
    font-size: 1.5rem; /* Change the Devanagari label size */
}

.index-link-item .stats {
    font-size: 0.8rem; /* Change the count (numeral) size */
    color: #888;
}
```

### Top 20 Classification Cards
To adjust the font weight or size of the names in the Top 20 lists (e.g., Rishi page):
**Location:** `src/generate_website.py` around lines 2397-2415.

```css
.rishi-name {
    font-weight: 400; /* Regular (400) or Bold (600) */
    font-size: 1.15rem;
}

.rishi-count {
    font-size: 0.8rem;
    font-weight: 400;
}
```

### Mantra Numbering (॥ १ ॥)
To adjust the size of the mantra index:
**Location:** `src/generate_website.py` around lines 1745-1750.

```css
.mantra-number {
    font-size: 1.6rem; /* Adjust this value */
    font-weight: 500;
}
```

### Kandah Page Sub-header (Metadata)
To adjust the second line of text on Kandah pages (labels and numbers):
**Location:** `src/generate_website.py` around lines 1133-1158.

```css
.page-subtitle, .sama-count {
    font-size: 1.1rem; /* Adjust labels and numbers together */
}

.page-meta .number {
    font-size: 0.8rem; /* Fine-tune only the numerals here */
    font-weight: 400;
}
```

---

> [!TIP]
> **Important**: All these styles are injected into the HTML during generation. After editing the fragments in `src/generate_website.py`, you **must** run the generator script to see the changes:
> `python src/generate_website.py --source-file data/output/Vargeekaran.json -o docs`
