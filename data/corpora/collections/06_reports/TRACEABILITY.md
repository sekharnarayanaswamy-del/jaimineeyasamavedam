# Jaimineeya Samavedam — Traceability & Lineage Report: Collections

- **Corpus**: `collections`
- **Edition**: `2.05`
- **Generated Timestamp**: `07-10-2026 08:15:24`
- **Validation Status**: `PASSED`

---

## 1. Liturgical Invariants & Metrics
| Metric | Active Count | Baseline Invariant | Status |
| :--- | :--- | :--- | :--- |
| **Pathas (SuperSections)** | 1 | None | PASS |
| **Khandas (Sections)** | 25 | None | PASS |
| **Samas (Liturgical Chants)** | 143 | None | PASS |

---

## 2. Cryptographic Stage Lineage (01 -> 02 -> 04)
| Stage | Canonical File | Size | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| **Stage 01: Input** | `Ashirvachana_samani.txt` | 704 B | `0cc58a89a0f4c0e3750e0baa3732773385a908966bd38b3b17127b07d3a9cc5c` |
| **Stage 02: Parsed AST** | `Sooktamala.json` | 320.3 KB | `cd371af08e09d20f58e1b329b0be58112422ac7eb1d78cd7e6bb8795dd9ee6e9` |
| **Stage 04: Canonical AST** | `Sooktamala.json` | 320.3 KB | `cd371af08e09d20f58e1b329b0be58112422ac7eb1d78cd7e6bb8795dd9ee6e9` |

---

## 3. Compiled Render Catalog (`05_renders/`)

### PDF Documents (`05_renders/pdf/`)
| File Name | Mode / Edition | Target Script | Size |
| :--- | :--- | :--- | :--- |
| [`Prayogamala-Purvabhagam_Devanagari.pdf`](../05_renders/pdf/Prayogamala-Purvabhagam_Devanagari.pdf) | Combined (Study Edition) | Devanagari (Standard) | 292.5 KB |
| [`prayogamala-Uttarabhagam_Devanagari.pdf`](../05_renders/pdf/prayogamala-Uttarabhagam_Devanagari.pdf) | Standard | Devanagari (Standard) | 140.0 KB |
| [`Sooktamala_Devanagari.pdf`](../05_renders/pdf/Sooktamala_Devanagari.pdf) | Combined (Study Edition) | Devanagari (Standard) | 265.3 KB |

### HTML Readers (`05_renders/html/`)
| File Name | Mode / Edition | Target Script | Size |
| :--- | :--- | :--- | :--- |
| [`Prayogamala-Purvabhagam_Devanagari.html`](../05_renders/html/Prayogamala-Purvabhagam_Devanagari.html) | Combined (Study Edition) | Devanagari (Standard) | 5.04 MB |
| [`prayogamala-Uttarabhagam_Devanagari.html`](../05_renders/html/prayogamala-Uttarabhagam_Devanagari.html) | Standard | Devanagari (Standard) | 3.40 MB |
| [`Sooktamala_Devanagari.html`](../05_renders/html/Sooktamala_Devanagari.html) | Combined (Study Edition) | Devanagari (Standard) | 4.54 MB |

### PlainText Exports (`05_renders/txt/`)
| File Name | Mode / Edition | Target Script | Size |
| :--- | :--- | :--- | :--- |
| [`Prayogamala-Purvabhagam_Devanagari_Unicode.txt`](../05_renders/txt/Prayogamala-Purvabhagam_Devanagari_Unicode.txt) | Combined (Study Edition) | Devanagari (Standard) | 232.5 KB |
| [`prayogamala-Uttarabhagam_Devanagari_Unicode.txt`](../05_renders/txt/prayogamala-Uttarabhagam_Devanagari_Unicode.txt) | Standard | Devanagari (Standard) | 72.4 KB |
| [`Sooktamala_Devanagari_Unicode.txt`](../05_renders/txt/Sooktamala_Devanagari_Unicode.txt) | Combined (Study Edition) | Devanagari (Standard) | 206.3 KB |

---

## 4. Source & Intermediate Datasets

### 01_input (Source Texts)
| File Name | Size | SHA-256 |
| :--- | :--- | :--- |
| [`Ashirvachana_samani.txt`](../01_input/Ashirvachana_samani.txt) | 704 B | `0cc58a89a0f4c0e3...` |
| [`Filter_file_superset.txt`](../01_input/Filter_file_superset.txt) | 3.9 KB | `aa5097c4722b9afd...` |
| [`Nakshatra_sooktam.txt`](../01_input/Nakshatra_sooktam.txt) | 1.5 KB | `7ab1598508d0dbb1...` |
| [`PM-PB_filter.txt`](../01_input/PM-PB_filter.txt) | 6.0 KB | `2d66508f95d9c300...` |
| [`PM-UB_filter.txt`](../01_input/PM-UB_filter.txt) | 1.2 KB | `d347f51a8019b501...` |
| [`Ritu-shanti.txt`](../01_input/Ritu-shanti.txt) | 1.5 KB | `2643fda236a70eb7...` |

---

## 5. Audit Reports (`06_reports/`)
| Report File | Size |
| :--- | :--- |

---

## 6. Audit & Validation Commands
To verify cryptographic and liturgical invariants against golden baselines:
```bash
python src/tools/validate_run.py collections
```
