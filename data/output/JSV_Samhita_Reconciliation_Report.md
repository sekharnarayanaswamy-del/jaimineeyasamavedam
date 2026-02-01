# Jaimineeya Samaveda Samhita - Data Reconciliation Report

**Generated:** 2026-02-01 (Updated)

---

## Executive Summary

This report summarizes the data reconciliation analysis performed on the Jaimineeya Samaveda Samhita source text and its various processed outputs.

### Overall Structure

| Metric | Value |
|--------|-------|
| **Pathas (SuperSections)** | 6 |
| **Khandas (Sections)** | 59 |
| **Arsheyams (Subsections)** | 722 |
| **Samams** | 1,225 |

**Data Status:** ✅ **RECONCILED**

---

## Section 1: Patha-wise Breakdown

| Patha | Khandas | Arsheyams | Samams |
|-------|---------|-----------|--------|
| आग्नेयपाठः | 12 | 125 | 182 |
| तद्वपाठः | 12 | 124 | 200 |
| बृहतिपाठः | 8 | 95 | 152 |
| असाविपाठः | 6 | 64 | 106 |
| ऐन्द्रपाठः | 10 | 105 | 186 |
| पवमानपाठः | 11 | 209 | 399 |
| **TOTAL** | **59** | **722** | **1,225** |

> **Note:** 
> - **Arsheyam** = Named sub-unit (e.g., ॥गौतमस्यपर्कः॥), each may contain multiple Samams
> - **Samam** = Individual chant/verse number, counted from the `॥N॥` markers in the text

---

## Section 2: Counting Methodology

The Samam count is derived using a **unified counting method** implemented in `src/samam_utils.py`:

```python
# Pattern matches both Devanagari (॥) and ASCII (||) danda markers
# With both Devanagari (०-९) and Arabic (0-9) numerals
SAMAM_PATTERN = re.compile(r'(?:॥|\|\|)\s*[\d०-९]+\s*(?:॥|\|\|)')
```

This ensures consistency between:
- Website homepage statistics
- Summary table generation
- Granular table generation

---

## Section 3: Data Source Comparison

Comparison between website, JSON output, and granular table:

| Metric | Website | JSON Summary | Granular Table | Status |
|--------|---------|--------------|----------------|--------|
| Khandas | 59 | 59 | 59 | ✅ MATCH |
| Arsheyams | 722 | 722 | - | ✅ MATCH |
| Samams | 1,225 | 1,225 | 1,225 | ✅ MATCH |

---

## Section 4: Output Files Generated

The following data files have been generated:

| File | Description | Records |
|------|-------------|---------|
| `JSV_Structure_Summary.csv` | Aggregated Sama counts by Patha/Khanda | 59 rows |
| `JSV_Structure_Summary.txt` | Human-readable summary | - |
| `JSV_Samam_Granular_Table.csv` | Row-per-Samam table with all details | 1,225 rows |
| `samam_numbering_errors.txt` | List of any numbering issues found | - |

---

## Section 5: Terminology Reference

| Term | Also Known As | Description |
|------|---------------|-------------|
| **Patha** | SuperSection | The 6 major divisions (आग्नेय, तद्व, बृहति, असावि, ऐन्द्र, पवमान) |
| **Khanda** | Section | Chapters within each Patha (प्रथम खण्डः, द्वितीय खण्डः, etc.) |
| **Arsheyam** | Subsection | Named sub-unit, often containing multiple Samams (e.g., ॥गौतमस्यपर्कः॥) |
| **Samam** | Sama | Individual chant/verse, identified by `॥N॥` markers in mantra text |

---

## Section 6: Scripts Reference

| Script | Purpose |
|--------|---------|
| `src/samam_utils.py` | Shared utility for consistent Samam counting |
| `src/generate_website.py` | Generates static website with correct counts |
| `src/generate_json_summary.py` | Generates structure summary CSV/TXT |
| `src/generate_granular_table.py` | Generates row-per-Samam CSV |

---

## Conclusion

| Check | Status |
|-------|--------|
| **Data Integrity** | ✅ Source text extraction is accurate and complete |
| **Khandas** | ✅ All 59 Khandas across 6 Pathas correctly identified |
| **Arsheyams** | ✅ All 722 Arsheyams correctly counted |
| **Samams** | ✅ 1,225 Samams confirmed (unified counting method) |
| **Website** | ✅ Homepage displays correct statistics |
| **Consistency** | ✅ All outputs use same counting methodology |

---

*Report generated as part of the Jaimineeya Samaveda digitization project.*
