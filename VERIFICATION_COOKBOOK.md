# Jaimineeya Samaveda Pipeline — Verification & Non-Regression Cookbook

**Target Audience**: Developers, maintainers, and reviewers working on the JSV pipeline.  
**Primary Purpose**: Step-by-step verification protocols to guarantee that code refactoring, script updates, or text edits introduce **zero liturgical regressions**, **zero accent drift**, and **zero numbering breaks**.

---

## ⚡ The 10-Second Quick Health Check

Before making any git commit or after pulling changes, run the automated regression suite:

```bash
python src/tools/run_regression_suite.py
```

### Expected Output:
```text
============================================================
  JAIMINEEYA SAMAVEDA - REGRESSION VERIFICATION SUITE
============================================================
  Checking: 1. Domain Invariants (6 Pathas, 59 Khandas, 1226 Samas) [PASS]
  Checking: 2. Typed AST Lossless Roundtrip.............. [PASS]
  Checking: 3. Swara Engine & Visarga-Accent Rules....... [PASS]
  Checking: 4. Structural Tag Balance & Integrity........ [PASS]
  Checking: 5. 3-Tier Version & Build Metadata........... [PASS]
  Checking: 6. Active Baseline Input Checksums........... [PASS]
  Checking: 7. Modular Rendering Engines................. [PASS]

============================================================
  VERIFICATION SUMMARY
============================================================
  ALL 7/7 INVARIANT CHECKS PASSED!
  No regressions detected. Repository is liturigically sound.
============================================================
```

> [!TIP]
> If all 7 checks show `[PASS]`, the fundamental liturgical invariants of the codebase are fully intact.

---

## 🧭 "Where Did We Leave Off?" Dashboard

Whenever you return to the repository after days, weeks, or months, run:

```bash
python src/tools/check_status.py
```

### What It Reports:
1. **Current Git Branch & Commit**: Confirms you are on branch `refactor` and shows if working tree has untracked/dirty files.
2. **Active Baseline Manifest**: Displays the active baseline name, date recorded, and git hash.
3. **Staleness / Drift Check**: Alerts you if master input files (`data/input/Samhita_corrected.txt`, etc.) or output files have changed compared to the active baseline.
4. **Recommended Next Actions**: Suggests immediate CLI commands to execute.

---

## 🔬 Step-by-Step Manual Verification Checklist

For deep regression audits during major refactoring phases (e.g. Phase 2 Renderer decomposition or Phase 4 Renumbering), execute each stage in order:

### Stage 1: Domain Metric & Structural Invariants
Verify that the macro structure matches the liturgical gold standard:

```bash
python src/generate_json_summary.py
```

- [ ] **Pathas**: Exactly **6**
- [ ] **Khandas**: Exactly **59**
- [ ] **Samas**: Exactly **1226** (including compound / split sub-verses)
- [ ] Summary CSV matches: `data/output/JSV_Structure_Summary.csv`

---

### Stage 2: Structural Tag Balance Check
Verify that all `# Start of` and `# End of` tags in master texts are balanced and uncorrupted:

```bash
python src/tools/renumber_sooktam.py data/input/Samhita_corrected.txt --type samhita --no-increment --no-renumber
```

- [ ] Output confirms: `Structural Integrity Check...` with **zero tag mismatches** and **zero unclosed tags**.

---

### Stage 3: JSON AST Invariance & Golden Diff
Regenerate the canonical JSON AST from the source text and verify structural equivalence:

```bash
python src/generate_json.py data/input/Samhita_corrected.txt --type samhita
```

Compare the generated JSON against the active baseline:
```bash
python src/tools/baseline.py status
```

- [ ] `data/output/Samhita_corrected_out.json` shows `[MATCH]`.
- [ ] Round-trip validation via Typed AST:
  ```bash
  python -c "from src.core.models import VedicDocument; import json; doc = VedicDocument.from_dict(json.load(open('data/output/Samhita_corrected_out.json', encoding='utf-8'))); assert len(doc.supersections) == 6; print('VedicDocument AST Valid!')"
  ```

---

### Stage 4: Rik Table & Vargeekaran Reconciliation
Verify that the Rik metadata mapping, Devata/Rishi reconciliation, and Vargeekaran structures build properly:

```bash
python src/generate_rik_table.py --type samhita
```

Check continuity across all 1226 Samas:
```bash
python src/tools/check_continuity.py data/output/Vargeekaran.json
```

- [ ] Generated files exist: `data/output/JSV_Rik_Table.csv` and `data/output/Vargeekaran.json`.
- [ ] Total Samams reported: **1226**.

---

### Stage 5: Multi-Format Rendering (LaTeX, PlainText & Kodunthirapully)
Verify that the rendering layer compiles without template or syntax errors:

```bash
# 1. Standard Devanagari Combined Render (LaTeX + PlainText)
python src/render_pdf.py data/output/Vargeekaran.json --type samhita --output-mode combined

# 2. Kodunthirapully Swara Stacking Mode (-kpully)
python src/render_pdf.py data/output/Vargeekaran.json -kpully
```

- [ ] Generated files exist in `data/output/pdf/Devanagari/` and `data/output/txt/Devanagari/`.
- [ ] `.tex` output compiles without LuaLaTeX/XeLaTeX macro errors.
- [ ] Unicode accents (Swarita `॑`, Anudatta `॒`, Kampa `᳸`) and Visarga-accent ordering (`ः॑` / `(1)ः`) match baseline exactly.

---

### Stage 6: Static Website & Search Index Integrity
Verify that the GitHub Pages documentation site (`docs/`) builds cleanly:

```bash
python src/generate_website.py --samhita
python src/generate_website.py --aaranam
```

- [ ] `docs/samhita/index.html` and `docs/aaranam/index.html` generated.
- [ ] `docs/samhita/search_index.json` generated and valid JSON.
- [ ] P.K.S (Parva.Kandah.Samam) anchor navigation links function in browser.

---

### Stage 7: Automated 3-Tier Versioning Verification
Verify that software modifications do not falsely inflate corpus edition numbers:

```bash
python -c "from src.core.version import get_engine_version, get_corpus_edition, get_build_metadata; print('Engine:', get_engine_version()); print('Edition:', get_corpus_edition('samhita')); meta = get_build_metadata('samhita', 'data/input/Samhita_corrected.txt'); print('Input SHA:', meta['input_sha256'][:16]); assert meta['version'] == '3.28'"
```

- [ ] Engine version reflects git tag & commit (e.g. `v4.0.0+<commit>`).
- [ ] Corpus edition matches `src/pipeline_config.yaml` (`samhita: 3.28`).
- [ ] Input file SHA-256 fingerprint is embedded in metadata.

---

## 📦 How to Baseline After Verified Milestone Changes

When you have completed a set of verified improvements and want to freeze the new state as an authoritative baseline:

```bash
# 1. Create a new baseline snapshot
python src/tools/baseline.py create baseline-<date>-<milestone> -d "Description of milestone"

# 2. Verify that the new baseline is active
python src/tools/baseline.py status

# 3. Commit the new baseline manifest to git
git add data/baselines/
git commit -m "chore: record baseline snapshot <milestone>"
```

---

## 🛠️ Regression Troubleshooting Guide

| Symptom | Probable Cause | Action to Resolve |
|---|---|---|
| `Total Samas != 1226` | Verse delimiter tag (`॥ N ॥`) missing, malformed, or split line | Run `python src/tools/check_continuity.py data/output/Vargeekaran.json` and check reported line |
| `Unclosed structural tags` | Missing `# End of SubSection` or Section boundary tag in input text | Run `python src/ingest/renumber.py data/input/Samhita_corrected.txt` to see exact line number |
| `Dotted circle on Visarga (ः) or Anusvara (ं)` | Accent combining mark placed before base character | Run `from src.core.swara_engine import fix_visarga_accent_order` on target text |
| `Baseline status shows [MODIFIED]` | Input or output file changed since last snapshot | Run `git diff <file>` to verify if change was intentional; if intentional, record new baseline |
