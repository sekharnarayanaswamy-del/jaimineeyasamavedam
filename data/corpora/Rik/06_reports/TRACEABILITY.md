# Jaimineeya Samavedam — Traceability & Lineage Report: Rik

- **Corpus**: `Rik`
- **Edition**: `1.00`
- **Generated Timestamp**: `01-10-2026 23:07:48`
- **Validation Status**: `PASSED`

---

## 1. Liturgical Invariants & Metrics
| Metric | Active Count | Baseline Invariant | Status |
| :--- | :--- | :--- | :--- |
| **Pathas (SuperSections)** | 10 | 10 | PASS |
| **Khandas (Sections)** | 155 | 155 | PASS |
| **Samas (Liturgical Chants)** | 0 | 0 | PASS |
| **Riks (Verses)** | 1666 | 1666 | PASS |

---

## 2. Cryptographic Stage Lineage (01 -> 02 -> 04)
| Stage | Canonical File | Size | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| **Stage 01: Input** | `vedic_text.txt` | 449.3 KB | `bef2360ac6db097710e05c2accaaa8001c7d9eda96d03114160152b9fd517002` |
| **Stage 02: Parsed AST** | `Purvarchikam_out.json` | 508.0 KB | `31752dd462db7d44832a7c4cb13ee37bfadc93698558942aa00e915dadf713c8` |
| **Stage 04: Canonical AST** | `Uttararchikam_out.json` | 764.4 KB | `cd682a3de068d9e5d8544922ba40785c9e8e8012654990cf9809c82da1055329` |

---

## 3. Compiled Render Catalog (`05_renders/`)

### PDF Documents (`05_renders/pdf/`)
| File Name | Mode / Edition | Target Script | Size |
| :--- | :--- | :--- | :--- |
| [`Purvarchikam_Rik_Devanagari.pdf`](../05_renders/pdf/Purvarchikam_Rik_Devanagari.pdf) | Separate (Rik Only) | Devanagari (Standard) | 268.0 KB |
| [`Uttararchikam_Rik_Devanagari.pdf`](../05_renders/pdf/Uttararchikam_Rik_Devanagari.pdf) | Separate (Rik Only) | Devanagari (Standard) | 345.2 KB |

### HTML Readers (`05_renders/html/`)
| File Name | Mode / Edition | Target Script | Size |
| :--- | :--- | :--- | :--- |
| [`Purvarchikam_Rik_Devanagari.html`](../05_renders/html/Purvarchikam_Rik_Devanagari.html) | Separate (Rik Only) | Devanagari (Standard) | 3.38 MB |
| [`Uttararchikam_Rik_Devanagari.html`](../05_renders/html/Uttararchikam_Rik_Devanagari.html) | Separate (Rik Only) | Devanagari (Standard) | 3.68 MB |

### PlainText Exports (`05_renders/txt/`)
| File Name | Mode / Edition | Target Script | Size |
| :--- | :--- | :--- | :--- |
| [`Purvarchikam_Rik_Devanagari_Unicode.txt`](../05_renders/txt/Purvarchikam_Rik_Devanagari_Unicode.txt) | Separate (Rik Only) | Devanagari (Standard) | 209.7 KB |
| [`Uttararchikam_Rik_Devanagari_Unicode.txt`](../05_renders/txt/Uttararchikam_Rik_Devanagari_Unicode.txt) | Separate (Rik Only) | Devanagari (Standard) | 288.9 KB |

---

## 4. Source & Intermediate Datasets

### 01_input (Source Texts)
| File Name | Size | SHA-256 |
| :--- | :--- | :--- |
| [`vedic_text.txt`](../01_input/vedic_text.txt) | 449.3 KB | `bef2360ac6db0977...` |

---

## 5. Audit Reports (`06_reports/`)
| Report File | Size |
| :--- | :--- |

---

## 6. Audit & Validation Commands
To verify cryptographic and liturgical invariants against golden baselines:
```bash
python src/tools/validate_run.py Rik
```
