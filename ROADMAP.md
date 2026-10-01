# Jaimineeya Samavedam Roadmap: Pipeline Evolution

This document captures the strategic milestones and architectural evolution of the Jaimineeya Samaveda digital pipeline.

---

## ✅ Phase 1: Tactical Safety & Normalization (Completed)
- [x] **Tag Validation Pre-flight**: Structural `# Start of` and `# End of` tag verification across all 5,263 lines of master texts.
- [x] **Danda Normalization**: Danda-agnostic searching, highlighting, and robust boundary marker handling (`॥ N ॥`).
- [x] **Visarga-Accent Ordering**: Preprocessing ensuring Visargas and Halants precede accents in LaTeX and HTML output.

## ✅ Phase 2: Domain Invariance & Regression Suite (Completed)
- [x] **Automated 9-Point Regression Suite** (`src/tools/run_regression_suite.py`): Continuous validation of 6 Pathas, 59 Khandas, 1226 Samas, checksums, and AST roundtrips.
- [x] **Decoupled 3-Tier Versioning**: Tier 1 Engine (`v4.1.0`), Tier 2 Liturgical Editions (`samhita: 3.28`, `aaranam: 1.14`, `collections: 2.05`, `kpully: 1.00`), Tier 3 Run Manifests.
- [x] **Consolidated Unified Renderer** (`src/render.py`): Single CLI dispatching PDF (LuaLaTeX), HTML, and Plaintext for all corpora and modes.

## ✅ Phase 3: Stage-Numbered Corpus Architecture (Completed)
- [x] **Decoupled Corpora Workspaces** (`data/corpora/{samhita,aaranam,collections,Rik}/`):
  - `01_input/` → Master texts & metadata
  - `02_ast/` → Parsed JSON ASTs
  - `03_reconciliation/` → Granular reconciliation workbooks & CSVs
  - `04_canonical/` → Authoritative canonical ASTs
  - `05_renders/{pdf,html,txt}/` → Strict format subdirectories (zero root clutter)
  - `06_reports/` → Live continuity reports & `TRACEABILITY.md`

## ✅ Phase 4: Modern Website Stabilization & Modularization (Completed)
- [x] **Modern VedaVMS Reader**: Responsive 2-column reader with drawer navigation, font switcher, and smooth scrolling for Samhita, Malayalam, and Collections.
- [x] **Decoupled & Modularized `generate_website.py`** (`src/website/`):
  - Ingests directly from canonical ASTs in `data/corpora/*/04_canonical/`.
  - Extracted 2,700+ lines of CSS/JS strings into dedicated assets module (`src/website/assets.py`).
  - Modularized into focused components: `models.py`, `parser.py`, `formatters.py`, `search.py`, `generator.py`.
  - Full alignment with standalone HTML viewers for Kodunthirapully (`kpully`) swara modifier geometry & typography.
  - Multi-site static suite generating all 8 micro-website targets (`samhita`, `aaranam`, `collections`, `kpully-devanagari`, `malayalam`, `samhita-samam`, `samhita-rik`, `samhita-samam-nometa`, `samhita-rik-nometa`).

## 🔭 Phase 5: Extended Corpora Expansion (Future)
- [ ] **Full Archikam Integration**: Complete publication pipeline for Purvarchikam and Uttararchikam Rik corpora.
- [ ] **Interactive Visual Curation**: Malayalam-Devanagari swara geometry tuning interface.
