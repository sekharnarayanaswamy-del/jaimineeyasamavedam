# Jaimineeya Samavedam — Traceability & Lineage Report: Samhita

- **Corpus**: `samhita`
- **Edition**: `3.28`
- **Generated Timestamp**: `10-10-2026 21:56:48`
- **Validation Status**: `PASSED`

---

## 1. Liturgical Invariants & Metrics
| Metric | Active Count | Baseline Invariant | Status |
| :--- | :--- | :--- | :--- |
| **Pathas (SuperSections)** | 6 | 6 | PASS |
| **Khandas (Sections)** | 59 | 59 | PASS |
| **Samas (Liturgical Chants)** | 722 | 1226 | CHECK |

---

## 2. Cryptographic Stage Lineage (01 -> 02 -> 04)
| Stage | Canonical File | Size | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| **Stage 01: Input** | `Samhita_Devanagari_Unicode.txt` | 1.21 MB | `ab960427c7691ab8268cef6db0f5963beb49ccef475984027201810d407c8b18` |
| **Stage 02: Parsed AST** | `Samhita_ast.json` | 1.74 MB | `6836dfdcc44bbbc1ca32ff1a55451a4e1f259ff5a03bf8e683cfa4d1c8f45aba` |
| **Stage 04: Canonical AST** | `Vargeekaran.json` | 2.22 MB | `0cb5efcd47a096d5ddbdf4f21e1a6eb8816a818c24b02817afc8df8582cda006` |

---

## 3. Compiled Render Catalog (`05_renders/`)

### PDF Documents (`05_renders/pdf/`)
| File Name | Mode / Edition | Target Script | Size |
| :--- | :--- | :--- | :--- |
| [`Samam_kpully_Malayalam.pdf`](../05_renders/pdf/Samam_kpully_Malayalam.pdf) | Separate (Samam Only) | Malayalam | 85.6 KB |
| [`Samhita_Devanagari.pdf`](../05_renders/pdf/Samhita_Devanagari.pdf) | Combined (Study Edition) | Devanagari (Standard) | 1.12 MB |
| [`Samhita_kpully_Devanagari.pdf`](../05_renders/pdf/Samhita_kpully_Devanagari.pdf) | Combined (Study Edition) | Devanagari (Kodunthirapully) | 110.3 KB |
| [`Samhita_Malayalam.pdf`](../05_renders/pdf/Samhita_Malayalam.pdf) | Combined (Study Edition) | Malayalam | 1.16 MB |
| [`Samhita_Rik_Devanagari.pdf`](../05_renders/pdf/Samhita_Rik_Devanagari.pdf) | Combined (Study Edition) | Devanagari (Standard) | 292.2 KB |
| [`Samhita_Rik_NoMeta_Devanagari.pdf`](../05_renders/pdf/Samhita_Rik_NoMeta_Devanagari.pdf) | NoMeta (Continuous Chanting) | Devanagari (Standard) | 247.1 KB |
| [`Samhita_Samam_Devanagari.pdf`](../05_renders/pdf/Samhita_Samam_Devanagari.pdf) | Combined (Study Edition) | Devanagari (Standard) | 877.7 KB |
| [`Samhita_Samam_NoMeta_Devanagari.pdf`](../05_renders/pdf/Samhita_Samam_NoMeta_Devanagari.pdf) | NoMeta (Continuous Chanting) | Devanagari (Standard) | 845.3 KB |

### HTML Readers (`05_renders/html/`)
| File Name | Mode / Edition | Target Script | Size |
| :--- | :--- | :--- | :--- |
| [`Samam_kpully_Devanagari.html`](../05_renders/html/Samam_kpully_Devanagari.html) | Separate (Samam Only) | Devanagari (Kodunthirapully) | 2.91 MB |
| [`Samam_kpully_Devanagari_Samam.html`](../05_renders/html/Samam_kpully_Devanagari_Samam.html) | Separate (Samam Only) | Devanagari (Kodunthirapully) | 2.90 MB |
| [`Samam_kpully_Malayalam.html`](../05_renders/html/Samam_kpully_Malayalam.html) | Separate (Samam Only) | Malayalam | 1.23 MB |
| [`Samam_kpully_Malayalam_Samam.html`](../05_renders/html/Samam_kpully_Malayalam_Samam.html) | Separate (Samam Only) | Malayalam | 1.23 MB |
| [`Samhita_Devanagari.html`](../05_renders/html/Samhita_Devanagari.html) | Combined (Study Edition) | Devanagari (Standard) | 11.84 MB |
| [`Samhita_kpully_Devanagari.html`](../05_renders/html/Samhita_kpully_Devanagari.html) | Combined (Study Edition) | Devanagari (Kodunthirapully) | 11.84 MB |
| [`Samhita_Malayalam.html`](../05_renders/html/Samhita_Malayalam.html) | Combined (Study Edition) | Malayalam | 1.23 MB |
| [`Samhita_Rik_Devanagari.html`](../05_renders/html/Samhita_Rik_Devanagari.html) | Combined (Study Edition) | Devanagari (Standard) | 3.78 MB |
| [`Samhita_Rik_NoMeta_Devanagari.html`](../05_renders/html/Samhita_Rik_NoMeta_Devanagari.html) | NoMeta (Continuous Chanting) | Devanagari (Standard) | 3.65 MB |
| [`Samhita_Samam_Devanagari.html`](../05_renders/html/Samhita_Samam_Devanagari.html) | Combined (Study Edition) | Devanagari (Standard) | 10.93 MB |
| [`Samhita_Samam_NoMeta_Devanagari.html`](../05_renders/html/Samhita_Samam_NoMeta_Devanagari.html) | NoMeta (Continuous Chanting) | Devanagari (Standard) | 10.80 MB |

### PlainText Exports (`05_renders/txt/`)
| File Name | Mode / Edition | Target Script | Size |
| :--- | :--- | :--- | :--- |
| [`Samam_kpully_Devanagari_Samam_Unicode.txt`](../05_renders/txt/Samam_kpully_Devanagari_Samam_Unicode.txt) | Separate (Samam Only) | Devanagari (Kodunthirapully) | 33.6 KB |
| [`Samam_kpully_Devanagari_Unicode.txt`](../05_renders/txt/Samam_kpully_Devanagari_Unicode.txt) | Separate (Samam Only) | Devanagari (Kodunthirapully) | 33.7 KB |
| [`Samam_kpully_Malayalam_Devanagari_Unicode.txt`](../05_renders/txt/Samam_kpully_Malayalam_Devanagari_Unicode.txt) | Separate (Samam Only) | Malayalam | 33.5 KB |
| [`Samam_kpully_Malayalam_Samam_Devanagari_Unicode.txt`](../05_renders/txt/Samam_kpully_Malayalam_Samam_Devanagari_Unicode.txt) | Separate (Samam Only) | Malayalam | 33.5 KB |
| [`Samam_kpully_Malayalam_Samam_Unicode.txt`](../05_renders/txt/Samam_kpully_Malayalam_Samam_Unicode.txt) | Separate (Samam Only) | Malayalam | 34.9 KB |
| [`Samam_kpully_Malayalam_Unicode.txt`](../05_renders/txt/Samam_kpully_Malayalam_Unicode.txt) | Separate (Samam Only) | Malayalam | 34.9 KB |
| [`Samhita_Devanagari_Unicode.txt`](../05_renders/txt/Samhita_Devanagari_Unicode.txt) | Combined (Study Edition) | Devanagari (Standard) | 1.30 MB |
| [`Samhita_kpully_Devanagari_Unicode.txt`](../05_renders/txt/Samhita_kpully_Devanagari_Unicode.txt) | Combined (Study Edition) | Devanagari (Kodunthirapully) | 1.30 MB |
| [`Samhita_Malayalam_Unicode.txt`](../05_renders/txt/Samhita_Malayalam_Unicode.txt) | Combined (Study Edition) | Malayalam | 1.41 MB |
| [`Samhita_Rik_Devanagari_Unicode.txt`](../05_renders/txt/Samhita_Rik_Devanagari_Unicode.txt) | Combined (Study Edition) | Devanagari (Standard) | 306.3 KB |
| [`Samhita_Rik_NoMeta_Devanagari_Unicode.txt`](../05_renders/txt/Samhita_Rik_NoMeta_Devanagari_Unicode.txt) | NoMeta (Continuous Chanting) | Devanagari (Standard) | 288.6 KB |
| [`Samhita_Samam_Devanagari_Unicode.txt`](../05_renders/txt/Samhita_Samam_Devanagari_Unicode.txt) | Combined (Study Edition) | Devanagari (Standard) | 963.7 KB |
| [`Samhita_Samam_NoMeta_Devanagari_Unicode.txt`](../05_renders/txt/Samhita_Samam_NoMeta_Devanagari_Unicode.txt) | NoMeta (Continuous Chanting) | Devanagari (Standard) | 816.7 KB |

---

## 4. Source & Intermediate Datasets

### 01_input (Source Texts)
| File Name | Size | SHA-256 |
| :--- | :--- | :--- |
| [`rishi_devata_chandas_for_rik.txt`](../01_input/rishi_devata_chandas_for_rik.txt) | 66.8 KB | `eba83833c46e8417...` |
| [`sama_rishi_chandas_out.txt`](../01_input/sama_rishi_chandas_out.txt) | 139.8 KB | `b75d61b0a1dc8745...` |
| [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | 35.0 KB | `f4c79dda06c41315...` |
| [`Samhita_corrected.txt`](../01_input/Samhita_corrected.txt) | 816.7 KB | `737facc955fd87d7...` |
| [`Samhita_corrected_samam.txt`](../01_input/Samhita_corrected_samam.txt) | 816.7 KB | `737facc955fd87d7...` |
| [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | 1.21 MB | `ab960427c7691ab8...` |
| [`vedic_text.txt`](../01_input/vedic_text.txt) | 449.3 KB | `bef2360ac6db0977...` |

### 03_reconciliation (Editorial Tables)
| File Name | Size |
| :--- | :--- |
| [`JSV_Rik_Table - for analysis.xlsx`](../03_reconciliation/JSV_Rik_Table - for analysis.xlsx) | 232.6 KB |
| [`JSV_Rik_Table.csv`](../03_reconciliation/JSV_Rik_Table.csv) | 272.3 KB |
| [`JSV_Rik_Table.txt`](../03_reconciliation/JSV_Rik_Table.txt) | 203.4 KB |
| [`JSV_Samam_Granular_Table.csv`](../03_reconciliation/JSV_Samam_Granular_Table.csv) | 830.0 KB |
| [`JSV_Samam_Granular_Table.xlsx`](../03_reconciliation/JSV_Samam_Granular_Table.xlsx) | 130.7 KB |
| [`Rik Reconciliation table (JSV-KSV).xlsx`](../03_reconciliation/Rik Reconciliation table (JSV-KSV).xlsx) | 2.88 MB |

---

## 5. Audit Reports (`06_reports/`)
| Report File | Size |
| :--- | :--- |
| [`JSON_Samam_Continuity_Report.txt`](JSON_Samam_Continuity_Report.txt) | 823 B |
| [`JSV_Structure_Summary.csv`](JSV_Structure_Summary.csv) | 3.8 KB |
| [`JSV_Structure_Summary.txt`](JSV_Structure_Summary.txt) | 6.4 KB |
| [`Samhita_corrected_out_continuity_report.txt`](Samhita_corrected_out_continuity_report.txt) | 987 B |

---

## 6. Audit & Validation Commands
To verify cryptographic and liturgical invariants against golden baselines:
```bash
python src/tools/validate_run.py samhita
```
