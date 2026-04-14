# Specification Notes & Session Checkpoint

**Purpose**: This document captures all discovered business rules, edge cases, bug fixes, 
and design decisions from development sessions. It serves as a checkpoint for future 
specification and test case development.

**Last Updated**: March 2026  
**Session Context**: Iterative development from OCR analysis → Scholar Tool completion

---

## Table of Contents

1. [Core Business Rules](#1-core-business-rules)
2. [Data Model Details](#2-data-model-details)
3. [Correction Types Catalog](#3-correction-types-catalog)
4. [Edge Cases & Bug Fixes](#4-edge-cases--bug-fixes)
5. [Performance Optimizations](#5-performance-optimizations)
6. [Test Case Ideas](#6-test-case-ideas)
7. [Design Decisions & Rationale](#7-design-decisions--rationale)
8. [Known Issues & Future Work](#8-known-issues--future-work)

---

## 1. Core Business Rules

### 1.1 "Between Markers" Extraction Logic

**Critical Discovery**: Reference markers work as boundaries, not labels.

```
Text for reference N = everything BETWEEN ^N^ and ^N+1^ markers
```

**Example**:
```
^7^वसन्तेति ॥ सुपां सुलुक् इति...^8^ग्रीष्मे राजन्य इत्यादि...
     ↑________________________↑
     This is bhashya for ref 7
```

**Implementation**: `word_to_bhashya.py` extracts text using this "between" logic.

### 1.2 Reference Marker Formats

OCR produces **three different marker formats** that must all be handled:

| Format | Example | Regex |
|--------|---------|-------|
| Unicode superscripts | ¹, ², ³, ⁴... | `[¹²³⁴⁵⁶⁷⁸⁹⁰]+` |
| Double caret | `^1^`, `^12^` | `\^(\d+)\^` |
| Single caret | `^1`, `^12` | `\^(\d+)(?!\^)` |

**Priority**: Check all three patterns when extracting references.

### 1.3 Page-to-Anuvaka Assignment Priority

When determining which anuvaka a page belongs to:

```
Priority Order (highest to lowest):
1. Scholar corrections (page_assignments.json)
2. Manual config overrides (in books.py)
3. Auto-detected HIGH confidence markers only
4. Inherit from previous page
```

**Rationale**: Scholar corrections always win because they represent human review.

### 1.4 Page-Proximity Matching

Shloka and Bhashya references are only paired if they appear on the same or adjacent pages:

```python
MAX_PAGE_DISTANCE = 1  # Same page or adjacent
```

**Example**:
- Shloka ref 7 on page 11, Bhashya ref 7 on page 11 → MATCH ✓
- Shloka ref 7 on page 11, Bhashya ref 7 on page 12 → MATCH ✓
- Shloka ref 7 on page 11, Bhashya ref 7 on page 15 → NO MATCH ✗

**Rationale**: Prevents false matches when same reference number appears in different anuvakas.

### 1.5 Sequential Sanity Check for Anuvaka Detection

OCR often misreads "Anuvaka 1" markers within pages. To prevent pages jumping backwards:

```python
# Don't allow anuvaka number to decrease within same prapaataka
if new_anuvaka < current_anuvaka and same_prapaataka:
    # Ignore this detection, likely OCR error
    continue_with_current_anuvaka()
```

**Example Bug Fixed**: Page 50+ was being assigned to "Anuvaka 1" because OCR misread 
a text phrase as an anuvaka marker.

### 1.6 Fuzzy Matching for SamhitaPaata

Shloka phrases from OCR are matched to SamhitaPaata using fuzzy matching:

```python
# Match threshold
MIN_FUZZY_SCORE = 70  # Out of 100

# Matching process
1. Clean both strings (remove punctuation, normalize)
2. Calculate Levenshtein similarity
3. Accept if score >= threshold
```

**Fields Used**:
- `panchasat_id`: Unique identifier (e.g., "1.1.1.7")
- `fuzzy_score`: Match confidence
- `samhitapaata`: The matched authoritative text

---

## 2. Data Model Details

### 2.1 Book Configuration (`config/books.py`)

```python
BOOKS = {
    "TB_Prasna_1": {
        "name": "Taittiriya Brahmana - Prasna 1",
        "ocr_path": "../brahmana_01_images",
        "base_file": "data/base/TB_base.json",
        "structure_path": ["Taittiriya Brahmana", "Prasna 1"],
        "prapaataka_boundaries": {
            1: (4, 68),    # Pages 4-68
            2: (69, 130),
            # ... etc
        },
        "anuvaka_boundaries": {
            "1.1": (4, 8),   # Prapaataka 1, Anuvaka 1
            "1.2": (9, 14),
            # ... etc
        }
    }
}
```

### 2.2 Word-to-Bhashya Reference

```python
{
    "ref_num": 7,
    "anuvaka_key": "P1.Pr1.A2",
    "shloka_text": "वसन्तो वै ब्राह्मणस्यर्तुः",  # OCR extracted
    "shloka_phrase": "वसन्तो वै",                   # Cleaned phrase
    "bhashya_text": "वसन्तेति ॥ सुपां सुलुक्...",  # Commentary
    "shloka_page": 11,
    "bhashya_page": 11,
    "status": "matched",  # or "shloka_only", "bhashya_only"
    "panchasat_id": "1.1.2.7",  # SamhitaPaata match
    "fuzzy_score": 85,
    "source": "ocr"  # or "scholar_correction"
}
```

### 2.3 Correction Record

```python
{
    "id": "corr_1234567890",
    "type": "remove_ref_from_page",  # See correction types below
    "anuvaka_key": "P1.Pr1.A2",
    "page_num": 14,
    "details": {
        "ref_num": 7,
        "target": "both"  # or "shloka", "bhashya"
    },
    "notes": "OCR artifact - not a real reference",
    "timestamp": "2026-03-15T10:30:00Z"
}
```

### 2.4 Page Assignment Correction

```python
{
    "page_num": 15,
    "prapaataka": 1,
    "anuvaka": 3,
    "anuvaka_key": "P1.Pr1.A3",
    "reason": "Scholar override - page contains A3 content"
}
```

---

## 3. Correction Types Catalog

### 3.1 `remove_ref`
Remove a reference entirely from an anuvaka.

```python
{
    "type": "remove_ref",
    "anuvaka_key": "P1.Pr1.A2",
    "details": {"ref_num": 11}
}
```

### 3.2 `remove_ref_from_page`
Remove a reference from a specific page only (page-level granularity).

```python
{
    "type": "remove_ref_from_page",
    "anuvaka_key": "P1.Pr1.A2",
    "page_num": 14,
    "details": {
        "ref_num": 7,
        "target": "both"  # or "shloka" or "bhashya"
    }
}
```

**Use Case**: Same reference number appears legitimately on multiple pages, but one 
occurrence is an OCR error.

### 3.3 `add_shloka`
Add a shloka phrase to an existing bhashya-only reference or create new.

```python
{
    "type": "add_shloka",
    "anuvaka_key": "P1.Pr1.A2",
    "page_num": 11,
    "details": {
        "ref_num": 7,
        "shloka_phrase": "वसन्तो वै ब्राह्मणस्यर्तुः"
    }
}
```

### 3.4 `add_bhashya`
Add bhashya text to an existing shloka-only reference or create new.

```python
{
    "type": "add_bhashya",
    "anuvaka_key": "P1.Pr1.A2",
    "page_num": 11,
    "details": {
        "ref_num": 7,
        "bhashya_text": "वसन्तेति ॥ सुपां सुलुक्..."
    }
}
```

### 3.5 `combine_refs`
Combine two separate references into one (OCR split them incorrectly).

```python
{
    "type": "combine_refs",
    "anuvaka_key": "P1.Pr1.A2",
    "details": {
        "primary_ref": 7,
        "merge_ref": 8
    }
}
```

### 3.6 `renumber_ref`
Change a reference number on a specific page (OCR misread).

```python
{
    "type": "renumber_ref",
    "anuvaka_key": "P1.Pr1.A2",
    "page_num": 14,
    "details": {
        "old_ref_num": 1,
        "new_ref_num": 11
    }
}
```

**Use Case**: OCR read "11" as "1" or "7" as "1" etc.

### 3.7 `page_assignment`
Override the anuvaka assignment for a page.

```python
{
    "page_num": 15,
    "prapaataka": 1,
    "anuvaka": 3,
    "anuvaka_key": "P1.Pr1.A3"
}
```

---

## 4. Edge Cases & Bug Fixes

### 4.1 Bug: Selection Change Clears Pending Insert

**Symptom**: Insert Reference popup shows correct section (Shloka/Bhashya) but 
submission fails with "Could not detect section".

**Root Cause**: `document.addEventListener('selectionchange')` fires when user 
clicks inside the popup, which calls `checkTextSelection()` and clears 
`pendingInsertSection` because the selection is no longer in `.text-content`.

**Fix**: Skip selection check when popup is open:
```javascript
function checkTextSelection() {
    const popup = document.getElementById('insert-ref-popup');
    if (popup && popup.style.display === 'flex') {
        return;  // Don't process while popup is open
    }
    // ... rest of function
}
```

### 4.2 Bug: Page Numbers Extracted from "Adhyaya X, Prashna Y"

**Symptom**: `parse_devanagari_number()` extracted "11" from "Adhyaya 1, Prashna 1".

**Root Cause**: Regex matched digits without context validation.

**Fix**: Added sanity check - extracted anuvaka number must be reasonable (< 50).

### 4.3 Bug: Pages Jump Backwards in Anuvaka Sequence

**Symptom**: Page 50+ assigned to Anuvaka 1 instead of continuing sequence.

**Root Cause**: OCR misread text as anuvaka marker.

**Fix**: Sequential sanity check - don't allow anuvaka number to decrease 
within same prapaataka unless explicitly starting a new prapaataka.

### 4.4 Edge Case: Multiple Marker Formats on Same Page

**Scenario**: Page contains both `^7^` and `⁷` (unicode superscript).

**Handling**: Extract all formats, deduplicate by reference number, prefer 
the one with more context.

### 4.5 Edge Case: Reference Number at Page Boundary

**Scenario**: Shloka marker `^7^` at end of page 10, bhashya text for 7 
starts on page 11.

**Handling**: Page-proximity matching allows 1 page distance, so these will match.

### 4.6 Edge Case: Duplicate Reference Numbers in Different Anuvakas

**Scenario**: Ref 1 exists in both Anuvaka 1 and Anuvaka 2.

**Handling**: References are scoped by anuvaka_key. Each anuvaka has its own 
reference numbering starting from 1.

### 4.7 Edge Case: OCR Explanations as Fallback

**Scenario**: No markers found in lyrics/commentary sections, but OCR 
"explanations" field contains reference info.

**Handling**: Fall back to parsing `page_analysis.commentary_section.explanations` 
array when primary extraction yields no results.

---

## 5. Performance Optimizations

### 5.1 Caching System

**Problem**: Full rebuild took ~3.5 minutes due to fuzzy matching.

**Solution**: Cache raw OCR extractions before corrections are applied.

```
data/cache/{book_id}/page_extractions.json
```

**Cache Contents**:
```python
{
    "pages": {
        "11": {
            "shloka_refs": [{"ref_num": 1, "text": "...", "position": 45}],
            "bhashya_refs": [{"ref_num": 7, "text": "...", "position": 120}],
            "anuvaka_key": "P1.Pr1.A2"
        }
    },
    "cache_version": "1.0",
    "created_at": "2026-03-15T10:00:00Z"
}
```

**Rebuild Time**: ~1 second with cache (corrections applied on-the-fly).

### 5.2 Skip Fuzzy Matching Flag

```bash
python -m stage2_analysis.word_to_bhashya --book TB_Prasna_1 --skip-fuzzy
```

**Behavior**: Uses ref_num as panchasat_id fallback, skips expensive fuzzy 
matching. Useful for quick correction testing.

### 5.3 Lazy Loading in Scholar Tool

- Images loaded on-demand when switching views
- SamhitaPaata section collapsed by default (many entries)
- Reference details shown on click, not on load

---

## 6. Test Case Ideas

### 6.1 Unit Tests - Reference Extraction

```python
def test_between_markers_extraction():
    """Text between ^7^ and ^8^ should be ref 7 content"""
    
def test_unicode_superscript_extraction():
    """Should handle ¹²³ format markers"""
    
def test_double_caret_extraction():
    """Should handle ^12^ format markers"""
    
def test_single_caret_extraction():
    """Should handle ^12 format (no closing caret)"""
    
def test_mixed_marker_formats():
    """Page with multiple formats should extract all"""
```

### 6.2 Unit Tests - Corrections

```python
def test_remove_ref_from_page():
    """Should remove ref from specific page only"""
    
def test_remove_ref_with_target_shloka():
    """Should remove only shloka, keep bhashya"""
    
def test_renumber_ref():
    """Should change ref number on specific page"""
    
def test_add_shloka_to_existing_bhashya():
    """Should add shloka to bhashya-only ref"""
```

### 6.3 Integration Tests - Pipeline

```python
def test_full_pipeline_prasna1():
    """Run stages 2-4 and verify output structure"""
    
def test_correction_persistence():
    """Corrections survive multiple regenerations"""
    
def test_cache_invalidation():
    """Cache regenerated when OCR files change"""
```

### 6.4 Edge Case Tests

```python
def test_page_boundary_reference():
    """Marker on page N, text on page N+1"""
    
def test_backward_anuvaka_prevention():
    """Should not jump from A5 back to A1"""
    
def test_duplicate_ref_different_anuvakas():
    """Same ref num in different anuvakas are separate"""
```

### 6.5 UI Tests (Scholar Tool)

```python
def test_insert_reference_shloka_section():
    """Select in shloka, verify add_shloka correction"""
    
def test_insert_reference_bhashya_section():
    """Select in bhashya, verify add_bhashya correction"""
    
def test_popup_selection_not_cleared():
    """Selection preserved when clicking popup elements"""
    
def test_bulk_remove_range():
    """Remove refs 7-12 creates 6 corrections"""
```

---

## 7. Design Decisions & Rationale

### 7.1 Separate Corrections from Base Data

**Decision**: Corrections stored in separate JSON files, not modifying base data.

**Rationale**:
- Base data can be regenerated from OCR without losing corrections
- Corrections are auditable and reversible
- Multiple scholars can work on different pages without conflicts

### 7.2 Page-Level vs Anuvaka-Level Corrections

**Decision**: Support both granularities.

**Rationale**:
- `remove_ref` (anuvaka-level): When reference is completely wrong
- `remove_ref_from_page` (page-level): When same ref appears correctly 
  elsewhere but is OCR error on specific page

### 7.3 Cache Raw Extractions, Apply Corrections On-the-fly

**Decision**: Don't bake corrections into cache.

**Rationale**:
- Correction changes don't require cache regeneration
- Quick iteration during scholar review
- Cache only needs regeneration when OCR changes

### 7.4 Priority-Based Page Assignment

**Decision**: Scholar > Config > Auto-detect

**Rationale**:
- Scholar has final authority
- Config provides manual overrides for known issues
- Auto-detect is fallible (OCR errors)

### 7.5 Batch Corrections via Text File

**Decision**: Simple text format for batch corrections.

**Format**:
```
# Page 14
1->11        # renumber 1 to 11
remove 7-12  # remove range
remove shloka 1-5  # remove only shloka markers
```

**Rationale**:
- Faster than clicking through UI for each correction
- Easy to share and review correction sets
- Supports ranges and targeted removal

---

## 8. Known Issues & Future Work

### 8.1 Known Issues

1. **Fuzzy matching accuracy**: Some false positives/negatives in SamhitaPaata matching
2. **Unicode normalization**: Some Sanskrit characters have multiple representations
3. **Nested references**: Rarely, bhashya contains sub-references not handled

### 8.2 Future Work

1. **Multi-user support**: Currently single-user, need conflict resolution
2. **Undo/redo**: No correction history UI yet
3. **Diff view**: Show changes between OCR and corrected version
4. **Audio alignment**: Stage 5 could include audio sync
5. **TA support**: Currently focused on TB, TA has different structure

### 8.3 Books Pending Processing

| Book | Pages | Status |
|------|-------|--------|
| TB Prasna 1 | 449 | In Progress |
| TB Prasna 2 | ~590 | Not Started |
| TB Prasna 3 | ~800 | Not Started |
| TA Part 1 | ~300 | Not Started |
| TA Part 2 | ~300 | Not Started |

---

## Appendix: File Locations

### Configuration
- `config/settings.py` - Path constants
- `config/books.py` - Book definitions with boundaries

### Data Files
- `data/base/TB_base.json` - Ground truth structure
- `data/cache/{book_id}/page_extractions.json` - Extraction cache
- `data/analysis/{book_id}/word_to_bhashya.json` - Reference mappings
- `data/corrections/{book_id}/corrections.json` - Scholar corrections
- `data/corrections/{book_id}/page_assignments.json` - Page overrides
- `data/corrections/{book_id}/batch_corrections.txt` - Batch file
- `data/integrated/{book_id}/web_export.json` - Final output

### Scripts
- `stage2_analysis/word_to_bhashya.py` - Main extraction logic
- `stage3_scholar_tool/app.py` - Flask application
- `stage4_integration/apply_corrections.py` - Correction application

---

## 9. Technical Decision: Rendering Revert (April 2026)

**Issue**: Display of "dotted circle" (`◌`) in standard browsers/fonts when Vedic accents follow a Visarga (`ः`).

**Experimental Fixes Attempted**:
1. **Zero Width Joiner (ZWJ)**: Inserting `\u200D` between components to force ligature or glyph combinations.
2. **Visarga-Accent Swapping**: A pre-processing step to swap order (`ः(1)` → `(1)ः`) to trick the font engine.
3. **CSS Visarga Wrapping**: Wrapping `ः` in a `<span>` to apply `font-feature-settings` or `::after` content hacks.

**Outcome**: **Reverted and Abandoned**.
The experimental fixes proved unstable. Specifically, ZWJ did not consistently resolve the issue across different operating systems, and swapping/wrapping logic introduced layout regressions and search highlighting bugs.

**Current Strategy**: 
- Reverted to standard Unicode sequences.
- Maintained **Zero-width CSS positioning** (overlay method) as the most compatible stable approach.
- Deferred further glyph-level fixes to future custom font development or browser engine improvements.

---

*This document should be updated as new edge cases are discovered or design 
decisions are made. It serves as the primary reference for generating formal 
specifications and test suites.*
