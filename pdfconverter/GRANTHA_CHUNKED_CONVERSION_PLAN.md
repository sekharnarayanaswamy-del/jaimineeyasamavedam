# Grantha → Sanskrit 2020: Chunked Conversion & Verification Plan

Status: **Phases 1, 3, 5 and the K1P1–K1P4 review loop working; Phases 4/6 ongoing** · 2026-10-24
Scope: `pdfconverter/data/input/1st Paadam Final-Grantha*.docx` → Word-2013-safe
Devanagari (`Sanskrit 2020`), verified against the SETHU reference wherever it exists.

---

## 1. Where the project stands (measured today, not estimated)

### 1.1 Corpus structure

The cleaned source (`1st Paadam Final-Grantha-Cleaned.docx`, 2,097 paragraphs,
237 tables, 249,515 non-Tamil characters) splits cleanly on the encoded Prasna
headings (`h\fk, h\xª,` … `q%k, h\xª,`), so **a chunk = one Prasna**:

| Chunk | Paragraphs | Tables | Tamil paras | Characters | Ground truth |
| :--- | ---: | ---: | ---: | ---: | :--- |
| K1 P1 | 56 | 13 | 15 | 14,125 | ✅ SETHU |
| K1 P2 | 51 | 14 | 11 | 14,055 | ✅ SETHU |
| K1 P3 | 48 | 16 | 9 | 12,564 | ✅ SETHU |
| K1 P4 | 77 | 16 | 0 | 17,021 | ✅ SETHU |
| K1 P5 | 50 | 20 | 9 | 20,583 | — |
| K1 P6 | 54 | 24 | 7 | 19,147 | — |
| K1 P7 | 54 | 23 | 6 | 19,139 | — |
| K1 P8 | 77 | 24 | 15 | 19,946 | — |
| K2 P1 | 56 | 27 | 9 | 23,545 | — |
| K2 P2 | 59 | 30 | 11 | 26,879 | — |
| K2 P3 + appendices | 1,265 | 30 | 26 | 62,511 | — |

Notes:

* The reference (`THAITHIREEYA SAMHITHA 1 (SETHU) प्रथम पादः .docx`) contains
  **88 anuvakas** = Kandam 1 Prasnas 1–4 (4,475 words, 45,086 chars), one
  paragraph per anuvaka.
* Everything after `॥ द्वितीयकाण्डः ॥` (para 1167) is *not* another Prasna: it is
  K2 P1–P3 followed by an appendix block (padānukrama / varṇa lists / śākhā
  lists, paras 1167–2067). That block currently hides inside "K2 P3" and needs
  its own chunk + its own rules (it is a word index, not prose).
* A faithful conversion is achievable: grantha bytes are ≈0.906 × the reference
  character count (median per anuvaka 0.91) — the encoding is simply more
  compact (`Z`→`त्व`, `#`→`न्द`, …). **No text is missing.** ~100 % is reachable.

### 1.2 Decoder quality today (88 anuvakas, swaras stripped)

| Decoder | Word recall | Base-text CER |
| :--- | ---: | ---: |
| `scratch/generate_complete_sanskrit2020.py` (`GANAPATHY_MAP`) | 17.2 % | 38.7 % |
| `src/convert_grantha_with_ref.py` (`CONSONANTS`/`SUBSCRIPTS`/`COMPOUNDS`) | 37.1 % | 25.2 % |
| `tools/ganapathy_map.py` v2 (merged tables, per-byte transducer) | **70.2 %** | **6.6 %** |

The v2 decoder is the current working baseline (`DECODER_VERSION =
2026-10-24.v2-merged`). Both older decoders are unusable for delivery. The
gap was *not* missing text, it was:

* 77 distinct code points (24,234 occurrences) are simply absent from the older
  map and fall through as Latin letters (`K`→`य`, `O`→`ज`, `L`→`ल`, `[`→`ी`,
  `²`→`्व`, `)`→`ꣳ`, `+`→`त्र`, `f`→`थ`, `¥`→`्ण`, `ˆ`→`्च`, …).
* Several entries are actively wrong. Verified against aligned words:
  `B`→`ট` should be **`न्त`** (`DB”` → `तन्त॑`), `J`→`भ` should be **`त्व`**
  (`zv”6J8v»3` → `वसु॑भ्यस्त्वा`), `²`→`ँ` should be **`्व`** (`v(²gK(3` →
  `स्व॒धया॒`), `4`→`ि` should be **`ृ`** (`y(4D3` → `कृ॒ता`),
  `O`→`ल` should be **`ज`** (`O6%”k](b` → `जुष्ट॑मि॒ह`), and `K`/`L` are
  not mapped at all (`K`→`य`, `L`→`ल`).
* Reordering is only half-modelled: kombu `1`, repha `9`, accent-before-matra,
  and two-part `ो/ौ` (`1 … 3`) are the source of most remaining errors.

The better map already exists in the repo (`src/convert_grantha_with_ref.py`);
the two untracked `src/convert_grantha*.py` files are near-duplicates of each
other and duplicate the scratch pipeline. **Consolidation is itself a deliverable.**

### 1.3 What the existing tools are good for

| Tool | Verdict |
| :--- | :--- |
| `scratch/deep_sanitize_input.py` | Keep — Stage 0 (strip ink/drawings/bookmarks). |
| `scratch/purify_namespaces.py` | Keep — called after every save. |
| `scratch/apply_final_polish.py` | Fold its regexes into the canonicalizer; keep the file as a thin wrapper. |
| `scratch/audit_complete_devanagari.py` | Keep + extend (new gates below). |
| `scratch/apply_all_10_tables_ss2.py` | Keep as the **hand-verified fixture** for tables 0–9, not as logic. |
| `scratch/generate_complete_sanskrit2020.py` | Refactor: it (a) runs the whole conversion **on import**, (b) copies reference text over prasnas 1–4, hiding conversion errors. Split into library + CLI. |
| `scratch/run_chunk1_complete_generation.py` | **Retire from production** — `PARAS_MAP` is hand-typed text, not a conversion. Keep the map as a golden regression fixture. |
| `scratch/compare_decoded_vs_sethu.py` | Superseded by `tools/align_reference.py`. |
| `scratch/extract_chunk1_grantha.py` | Generalize into `tools/build_chunks.py`. |
| Glyph tooling (`render_glyphs_table.py`, `build_glyph_inventory.py`, `ganapathy_glyphs.html`) | Keep — needed for visual identification of unknown code points. |
| `src/convert_grantha_with_ref.py` | **Source of the better map**; move it into `tools/`. |
| `src/convert_grantha_docx.py` | Duplicate of the above — delete after merge. |
| `src/convert_full_grantha_document.py` | Older duplicate of the scratch decoder — retire. |

### 1.4 New foundation added today

| File | Purpose |
| :--- | :--- |
| `tools/ganapathy_map.py` | Single source of truth: map, swara codes, canonicalizer, `decode_text()`. Pure module, no side effects, `DECODER_VERSION`. |
| `tools/align_reference.py` | Grader. Segments both docs on `{N}` markers, decodes, reports word recall/precision, base CER per anuvaka, and top character confusions. Pluggable decoder (`--decoder module:function`). |
| `tools/learn_map.py` | Proposal miner: re-decodes tokens with source spans, diffs against the reference, and votes for `(grantha source → Devanagari target)` rewrites. |
| `tools/induce_map.py` | Vote table: per source byte, what the aligned reference actually says (confidence + rivals). This is what found `J`→भ, `8`→्य, `@`→न्ध, `…`→्ग, … |
| `tools/tune_map.py` | Fast evaluator + greedy search: scores a candidate map change in ~2 s, so fixes are measured instead of guessed. |
| `tools/codepoint_inventory.py` | Per-code-point frequency, coverage, current target, contexts → `reports/codepoints.csv`. |
| `tools/export_reference.py` | Freezes the oracle to versioned `data/reference/sethu_anuvakas.json` (the .docx is git-ignored). |

Run it:

```powershell
python pdfconverter\tools\align_reference.py
python pdfconverter\tools\tune_map.py                    # baseline score
python pdfconverter\tools\tune_map.py --set 'J=भ'        # score one change
python pdfconverter\tools\tune_map.py --auto --rounds 5  # greedy search
python pdfconverter\tools\induce_map.py --csv reports\induced.csv
python pdfconverter\tools\codepoint_inventory.py --csv reports\codepoints.csv
```

---

## 2. Target pipeline

```
data/input/1st Paadam Final-Grantha.docx
  │  scratch/deep_sanitize_input.py                    (once)
  ▼
data/input/...-Cleaned.docx
  │  tools/build_chunks.py        → data/chunks/K1P1.grantha.docx + manifest.json
  ▼
  │  tools/convert_chunk.py       (map + transducer + canonicalizer + tables)
  ▼
data/chunks/K1P1.devanagari.docx
  │  tools/purify_namespaces.py
  ├─ tools/align_reference.py     → reports/K1P1.grade.json     (K1P1–P4 only)
  ├─ tools/render_diff.py         → reports/K1P1.diff.html      (human review)
  └─ tools/audit_docx.py          → reports/K1P1.audit.json     (hard gates)
  ▼
tools/assemble.py → data/output/1st Paadam Complete - Devanagari.docx
```

**Rule:** the converter never reads the reference document. The reference is
only ever an *oracle* for grading. (Remove the reference-substitution branch in
`generate_complete_sanskrit2020.py` §4.)

**Rule:** the ground truth must be exported to versioned JSON/text
(`data/reference/sethu_anuvakas.json`), because `*.docx` is git-ignored — right
now the only copy of the oracle is an ignored binary with a Devanagari filename.

---

## 3. Phases

### Phase 1 — Make the map right (highest ROI; do this first)

Target: **base CER < 1 %**, word recall > 99 % on the 88 ground-truth anuvakas.

1. **Merge the two maps.** Adopt the `src/convert_grantha_with_ref.py`
   consonant/subscript/compound tables into `ganapathy_map.py` (they are
   measurably better), keep the scratch canonicalizer's dotted-circle rules.
   *Acceptance: CER ≤ 25.2 % (no regression) before adding anything new.*
2. **Code-point inventory.** New `tools/codepoint_inventory.py`: for every
   non-Tamil code point emit frequency, coverage %, previous/next contexts, and
   current target → `reports/codepoints.csv`. Prioritise by occurrence; ~40
   code points cover > 95 % of the corpus, so this is an afternoon of review,
   not a full alphabet.
3. **Glyph sheet for the unsure ones.** Extend
   `scratch/render_glyphs_table.py` to render each unknown code point from
   `fonts/GANAPATHY - GRANTHA FONT.ttf` at 96 px beside 2–3 candidate
   Devanagari aksharas. One HTML page, one visual pass, no guessing.
4. **Model the encoding as a syllable transducer**, not a char map
   (port `convert_grantha_token` from `src/convert_grantha_with_ref.py`):
   * pass 1 — reorder: kombu `1` before consonant → e/o-matra after; accent
     before matra → after matra; `9` repha after syllable → `र्` before onset.
   * pass 2 — longest-match decode: consonant + subscripts + matra + swaras.
   * pass 3 — `canonicalize()` (existing rules).
   * pass 4 — punctuation: `.`→`॥`, `-`→`।`, `֍`→space, `[N]` footnote refs,
     `ã`/`å`→`(`/`)`, drop `֎`, collapse runs.
5. **Bootstrap the remaining entries** with `tools/learn_map.py --iterate`:
   token-align, pair only equal-length replace blocks (otherwise skip — this
   removes the junk votes), use transducer spans for exact source attribution,
   apply proposals above threshold, re-grade, stop when ΔCER < 0.1 %.
   Keep the accepted table in `tools/ganapathy_map.py`; emit rejected ones to
   `reports/map_rejected.json` for auditability.
6. **Freeze v1** with `DECODER_VERSION` + a golden score file
   (`tests/golden_scores.json`) that CI can diff.

### Phase 2 — Swaras and orthography

* Score accents separately: base text vs. accent *sequence per akshara*.
  A word can be letter-perfect and still wrong by one `॒`.
* Validate the canonicalizer gates on real text: `U+25CC` = 0, `ंँ` = 0,
  accent-before-virama = 0, PUA gum recomposition (`\uE006`, `\uE003`).
* Establish the arbitration rule when grantha and reference disagree on an
  accent (the reference is "manually verified", so: reference wins, and log
  every disagreement to `reports/accent_disagreements.csv` for review).

### Phase 3 — Chunking and conversion CLI

* `tools/build_chunks.py`: split on Prasna/Kandam headings; keep tables and
  `sectPr`; move the appendix block after `॥ द्वितीयकाण्डः ॥` into its own
  chunk; write `data/chunks/manifest.json` (source SHA-256, para/table counts,
  first/last text, table indices) so every chunk is reproducible and traceable.
* `tools/convert_chunk.py --chunk K1P1`: deterministic, idempotent, no
  reference access. Emits a `report.json` with per-paragraph classification
  (heading / mantra / Tamil / table / footnote / ornament).
* Chunk size stays at Prasna level (12k–27k chars) — small enough to review,
  large enough that per-chunk setup cost is irrelevant.

### Phase 4 — Tables (no ground truth)

237 tables. Three safeguards, in this order:

1. **Lexicon first.** Seed from `TABLE_TERMS`
   (`generate_complete_sanskrit2020.py:194`) plus the 10 verified tables in
   `apply_all_10_tables_ss2.py`. Add a `tools/table_lexicon.py`; every new term
   discovered is added with its evidence.
2. **Structural audit.** Column 0 must be ASCII digits (`1-7`, `2-50`), 5
   columns (or documented exception), no empty cells, no Latin letters left
   after decode, no `U+25CC`. Failures are listed, not silently patched.
3. **Visual review.** `tools/render_tables.py` → HTML page per chunk, side by
   side grantha-vs-devanagari (rendered with the actual TTFs), for sign-off.
   Store per-table status in `tables_status.json` (`auto` / `reviewed` /
   `manual`), and never overwrite a `manual` table on re-run.

### Phase 5 — Assembly, Word 2013 QA, regression

* Reuse `purify_namespaces.py` + `audit_complete_devanagari.py` as hard gates.
  Add: no unresolved Latin letters in Devanagari runs, no `\u25CC`, no `ंँ`,
  no accent-before-virama, fonts ∈ {`Sanskrit 2020`, `Vijaya`}, `line="360"`
  on mantra paragraphs, `jc ∈ {both, center, left}`, 0 body-level bookmarks.
* `tools/assemble.py` concatenates chunks in manifest order and re-applies the
  section properties once.
* **Golden regression**: K1P1–P4 grade + audit counts must not regress on any
  map change. This is what makes the loop safe.

### Phase 6 — Human review loop

* `tools/render_diff.py`: HTML per chunk, word-level diff against the reference,
  colour-coded (missing / extra / substituted), plus accent-only diffs in a
  separate lighter colour.
* Review order: K1P1 → K1P4 (oracle available, fix the map), then spot-check
  K1P5–K2P3 (no oracle) by sampling 2 anuvakas per Prasna + every table.
* Optional oracle extension: public Unicode TS text (e.g. the wikisource dump
  already in `scratch/ts_1_1_wikisource.txt`) for K1 P5–P8 / K2. Usable for
  base-text comparison only (editions differ on swaras and sandhi splits).

---

## 4. Acceptance criteria per chunk

| Gate | Threshold (K1P1–P4) | Threshold (no-oracle chunks) |
| :--- | :--- | :--- |
| Base-text CER vs reference | ≤ 0.5 % | n/a (sampled review) |
| Word recall / precision | ≥ 99.5 % / ≥ 99 % | n/a |
| Accent accuracy per akshara | ≥ 99 % | sampled |
| Unmapped grantha code points | 0 | 0 |
| Latin letters in Devanagari runs | 0 | 0 |
| Dotted circles `U+25CC` / `ंँ` / accent-virama | 0 / 0 / 0 | same |
| Tables: structure audit | 100 % pass | 100 % pass |
| Tables: reviewed | 100 % | 100 % |
| Word 2013 pagination | no crash, no repair prompt | same |

---

## 5. Sequencing and effort

| Step | Effort | Blocking? |
| :--- | :--- | :--- |
| Phase 1.1–1.3 (merge map, inventory, glyph sheet) | 0.5 day | yes |
| Phase 1.4–1.6 (transducer + bootstrap + freeze) | 1–1.5 days | yes |
| Phase 2 (swaras) | 0.5 day | yes |
| Phase 3 (chunks + CLI) | 0.5 day | — (parallel with 1) |
| Phase 4 (tables) | 1–2 days (review-heavy) | — |
| Phase 5 (assembly + QA) | 0.5 day | yes |
| Phase 6 (review) | 1–2 days | — |

Phase 1 is the critical path: with the current 25 % CER, converting the other
seven chunks just produces seven unusable documents. Do **one** chunk end to
end (K1P1) as the pilot, then fan out.

---

## 6. Decisions (agreed 2026-10-24)

1. **Chunk granularity** — **one Prasna per chunk** (12 chunks: K1P1–K1P8,
   K2P1–K2P3, APPENDIX). Small enough to review, large enough that per-chunk
   setup cost is irrelevant.
2. **Reference substitution** — **decode only**. The converter never reads the
   reference; SETHU is an oracle for grading, never a source of output text.
3. **Appendix block** (paras 1167–2067) — **separate "index" chunk** with its
   own rules (one entry per line, no mantra formatting), not prose rules.
4. **Oracle for K1P5–K2** — **add the public Unicode TS text** for base-text
   (not swara) comparison, with sampling review on top.
5. **SETHU is an oracle, not a target** — where the oracle is demonstrably wrong
   (क्ष → ख्ष, dropped viramas, `॥`/`।`, shifted anuvaka boundaries) the output
   keeps correct Devanagari; the divergence is documented in
   `tests/golden_scores.json` (`note`) and in the diff report.
6. **Markers are digit-bracketed** — `{१४}` / `[२१]` are editorial numbers and
   their brackets are literal, even when glued to an ornament (`֍{१४}`) or
   split by a stray space (`{ १४}`); `[`/`]` inside a word stay ि/ी.
7. **Fonts** — Sanskrit 2020 and Vijaya are installed on the review machine, so
   Word and the HTML report show final shaping; `render_pages.py` (LibreOffice →
   PNG) is available when a page image is easier to inspect than the .docx.
8. **Bracketed visarga keeps the printed colon** — where the Grantha prints a
   visarga inside parentheses, the output is `(:)` with an **ASCII colon**,
   never `(ः)`. Visargas in running text are unchanged (`वायव॑(:)` but
   `न॒मः॒`). The rule is a literal `(ः)` → `(:)` replacement, applied in
   `canonicalize` and again after literal-run placeholders are spliced back in
   `decode_paragraph`, so it holds across the whole document and in tables.
9. **Accents go after the syllable-closing mark** — `ः`, `ं`, `ँ` close the
   syllable, so a Vedic accent is written *after* them (`वायवः॑`, `तां॑`,
   `अँ॑`). An accent *before* the mark (`वायव॑ः`) is two combining marks in a
   row, which DirectWrite/HarfBuzz both draw with a dotted circle — this was
   the real cause of the reported dotted circles, not the parentheses. The
   reorder happens in `canonicalize`; `accent_before_mark` gates it.
10. **Ornaments keep the source face and spacing** — the flower motif
    (U+058D/U+058E) is set in `ORNAMENT_FONT = "Calibri"`, where Word
    substitutes the wide, clearly separated flower of the printed page.
    Sanskrit 2020 draws a tighter, circled glyph, so ornament runs keep the
    source face; whitespace *inside* an ornament span is not collapsed by
    `decode()`, which preserves the gap before `{५}`. `split_ornaments()`
    splits the paragraph so only the motif run carries that face.
11. **ASCII braces/brackets from a Latin-font run are literal** — `{` is also
    the Grantha glyph for क्त, so `run_is_literal` treats only *non-ASCII*
    trigger characters as proof of encoded text. A Calibri `{`/`}` survives as
    a brace, which is what the `{५}` markers need; likewise `(`/`)` from a
    Latin run are real parentheses, not the `॒`/`ꣳ` accent glyphs.
12. **No orphan combining marks** — the typesetter occasionally spaced a mark
    off its syllable (`नैः ः`, `थकार, ्फकार`). `decode_token` strips leading
    combining marks at the start of a whitespace-delimited token, and
    `orphan_mark` gates any that remain.
13. **The print wins over the reference** (2026-10-25) — where the Grantha
    prints an anusvara the output keeps `ं`, even though SETHU normalises to
    `म्`; where the reference's table disagreed with the Grantha, the
    reference was discarded and `COMPOUNDS` emptied. This is decision 2 applied
    to tables: the converter decodes, it never substitutes reference text. The
    CER cost is an oracle artefact and is recorded in the golden baseline note.
14. **Unknown glyphs stay visible** — a code point whose shape has not been
    proven is *not* guessed. It is left as the Latin-1 letter, counted by
    `unknown_chars`, and red-outlined in `reports/tables.html`, so the user can
    fix it from the Grantha original. A silent wrong mapping is worse than
    visible junk.

## 7. Phase 1 progress log

| Step | State | Result |
| :--- | :--- | :--- |
| 1.1 Merge maps | done | v2 tables + per-byte transducer; CER 25.2 % → 19.0 % |
| 1.2 Code-point inventory | done | 165 code points; unmapped share 10.45 % (mostly structural `1`/`9`) |
| 1.3 Evidence-driven fixes | done | `J`→भ, `8`→्य, `Ÿ`→्र, `#`→न्द्, `@`→न्ध, `…`→्ग, `)`→ꣳ, `;`→म् … → **CER 6.6 %** |
| 1.4 Transducer cleanup | done | per-byte provenance, kombu, repha, matra-after-ligature |
| 1.5 Greedy tuning | done | cluster rules: swara flush before subscript/repha, full-cluster dependents (`~` द्व, `@` न्ध) start a new syllable |
| 1.6 Freeze v1 | done | `DECODER_VERSION 2026-10-24.v4-clusters` + `tests/golden_scores.json` |
| 1.7 Freeze v2 | done | `DECODER_VERSION 2026-10-25.v5-subscripts` + re-baselined `tests/golden_scores.json` (word recall 75.6 %, base CER 3.81 %, aligned CER 3.19 %, aligned exact 88.2 %, accents 95.9 %). CER rises only because the output now follows the print's anusvara (`;` → `ं`) where SETHU normalises to `म्`; word-level and accent scores are unchanged. |
| 3 Chunking + CLI | done | `build_chunks.py` (12 chunks), `convert_chunk.py`, `convert_all.py --review` |
| 5 Assembly + gates | done | 12 `.devanagari.docx`; every gate zero except known source junk (see below) |
| 5b Accent order / `(:)` | done | accents moved after `ः/ं/ँ`, bracketed visarga printed `(:)`, ornament runs split; new `accent_before_mark` + `orphan_mark` gates |
| 6 Review loop | in progress | `diff_report.py` (Grantha / generated / SETHU), `grade_chunk.py`, `render_pages.py` |
| 7 Table repair | done | root-caused the broken table cells to reference-derived `COMPOUNDS`; `COMPOUNDS` emptied, `;`→anusvara, lone `*`→म्, blank glyphs→space, `®`→्ब, deep-band subscripts added; `table_report.py` reviews every cell. Bad cells 24 → 5 (all APPENDIX). See §8. |

Chunk grades (SETHU oracle, K1 only):

| Chunk | Anuvakas | Word recall | Base CER | Exact words | Accents |
| :--- | ---: | ---: | ---: | ---: | ---: |
| K1P1 | 14 / 14 | 72.9 % | 3.75 % | 88.8 % | 95.3 % |
| K1P2 | 14 / 14 | 77.9 % | 3.31 % | 88.6 % | 96.4 % |
| K1P3 | 14 / 14 | 73.7 % | 4.23 % | 85.2 % | 95.5 % |
| K1P4 | 46 / 46 | 77.6 % | 3.85 % | 90.1 % | 96.3 % |

Audit gates on the finished `.docx` (`convert_chunk.py --chunk …`), all zero on
every chunk except the documented source junk:

| Gate | What it catches |
| :--- | :--- |
| `legacy_bytes` | any Ganapathy byte left undecoded |
| `dotted_circle` | a literal `U+25CC` in the text |
| `double_nasal` | `ंँ` / `ँं` sequences |
| `accent_before_virama` | an accent in front of `्` (shaper draws a dotted circle) |
| `accent_before_mark` | an accent in front of `ः`/`ं`/`ँ` (same) |
| `orphan_mark` | a combining mark with no base (after space/danda/bracket) |
| `latin_letters` | Latin text that should have been Grantha |
| `unknown_chars` | unmapped glyphs outside the allowed set |

Residual differences are dominated by oracle artifacts, not decoder errors:
SETHU prints every क्ष as ख्ष (150 : 7), drops viramas in clusters
(`बर्हि` → `बरहि`), closes mantras with `॥` where the source uses `।`, and
sometimes shifts an anuvaka boundary (its A40 ends `सर्वस्य षड्विंशतिः`,
which the source prints at the start of A41). The source also repeats the
count word at some anuvaka ends (`… विंशति र्विंशतिः`); the output keeps the
source reading.

Remaining known error classes: six unmapped Grantha code points (`Ï`, `Ó`, `Ù`
— now only in a few words — `Á`, `Å`, `Õ`), the `R`/`n` typos in APPENDIX
(Latin letters typed outside the Ganapathy font), one stray Telugu sign in
K1P5, and kombu `1` e/o disambiguation. `‡ Ð Î ß ¼ ¾ Ù` were resolved in the
table pass (§8).

Known gate exceptions (source typos, reported not deleted):
`latin_letters=5` in APPENDIX (`R`, `n` inside otherwise-Devanagari words);
`unknown_chars` 0–8 per chunk (Latin-1 letters / one stray Telugu sign in
non-Ganapathy runs; seven chunks are at zero). Both are listed with context in
each `reports/<chunk>.diff.html`. Every other gate above reads zero for all
twelve chunks as of 2026-10-25.

## 8. Table repair pass (2026-10-25)

### 8.1 Root cause

Table cells were wrong even though the same bytes decoded correctly in body
paragraphs. The cause was not the transducer but `COMPOUNDS`: ~34 whole-phrase
overrides (`स्वरविधिः`, `प्रातिशाख्यम्`, `संहिता`, …) that had been copied from
the garbled Devanagari reference `data/input/1st Paadam (First 10 Pages) -
Devanagari_corr.docx`, whose table is itself broken. Because the prātiśākhya
tables are exactly where those phrases occur, every table hit an override and
never reached the compositional decoder.

`COMPOUNDS` is now **empty**. Rendering the Grantha glyphs of the same cells
with PIL (`fonts/GANAPATHY - GRANTHA FONT.ttf`) confirms the compositional
readings: `सप्तलक्ष`, `प्रातिशा`, `षड्विंशति`, `विलङ्घ्यम्`, `विसर्गान्तम्`,
`धकारादिः`, `प्रग्रहम्`, `तैत्तिरीयसंहितायाम्`. No whole-phrase table is needed.

The header row of K1P1 table 0 was also verified against the printed page: five
grid columns (1152/2250/1701/3544/992 twips), a four-cell header with the last
cell spanning two columns, and the narrow fifth column carrying the category
abbreviations `षड्वि` / `सप्त` / `प्राति` — it is not truncated text.

### 8.2 Decoder changes in this pass

| Change | Evidence |
| :--- | :--- |
| `COMPOUNDS = {}` | compositional decode matches the rendered Grantha |
| `;` → `ं` (anusvara) | `v;b]` = संहि, `~]Z;` = द्वित्वं, title `…संहितायाम्`; the separate final म् is `*` |
| lone `*` → `म्` | all 19 lone-`*` tokens are the invocation `bl], T äêå *` |
| `û` and NBSP → space | `û` has 0 contours and a 500-unit advance (identical to space); 15 uses, all trailing table-cell padding |
| `®` → `्ब` (was `्र`) | `G®Ý:` = न्ब्रह्म, `Y´(+1v83L“®kv]` = क्षत्रस्योल्बमसि, `hF®Ý7K3` = पद्ब्रूया, `F®4b1Fz` = द्बृहदेव, `1i3L®d1k1z3h` = चोल्बणम् (84 uses) |
| `¯` → `्भ` (was `्भ्`) | 119 uses, always a subscript भ: `F¯8` = द्भ्य, `k(F¯8,` = मद्भ्यः, `F¯7K3` = द्भूया. The trailing virama produced invalid `ल्ब्भ्ः` before a visarga. |
| `‡` → `्ङ` | प्रत्यङ्ङुपनतः, सदृङ्ङ्, उदङ्ङ् |
| `Ð` → `्प` | नस्स्पर्शपरात् |
| `Î` → `्ध` | वृङ्ग्धि |
| `ß` → `्र` | दधिक्क्राव्ण्णः, ब्ब्रु, ग्ग्र |
| `¼` → `्क` | शल्कैक्कः (क with two stacked क्; द्वित्व demo) |
| `¾` → `्ग` | अग्ग्ग्नये (ग with two stacked ग्; द्वित्व demo) |
| `Ù` → `्ष`, `„Ù` → `क्ष` | `?„Ù[K1D` = ङ्क्षीयते (`अन्नं क्षीयते`), `?„Ù(+h` = ङ्क्ष॒त्रप, `11?=„Ù+h` = ऐक्षत्रपत्य |
| fold stray `ख्ष` → `क्ष` | क्ष is typeset ख + subscript ष (`Y´`); a swara between the two glyphs blocks the MULTI rule, so `canonicalize` folds the invalid result |

Still unmapped and therefore visible as Latin-1 letters in the output (flagged
by `unknown_chars`, red-outlined in `reports/tables.html`): `Ï` (7), `Á` (3),
`Ó`, `Å`, `Õ`. They are confined to the prātiśākhya demo tables and a handful
of K1P5–K1P8 words; the Grantha original is the reference for those.

### 8.3 Review artefact

`tools/table_report.py` writes a self-contained `reports/tables.html`:

* every table cell of all 12 chunks, with the **Grantha source rendered in the
  embedded Ganapathy face** above the generated Devanagari, plus the raw bytes;
* cells whose output still contains foreign characters get a red outline and a
  count in the per-chunk summary.

Current result: **237 tables, 4 729 cells, 5 cells with foreign characters**
(K1P1–K2P3 all zero; APPENDIX 5). Before the pass it was 24 cells across six
chunks.

---

## Appendix A — Commands

```powershell
# full pipeline: convert, audit, grade, three-way review report
python pdfconverter\tools\convert_all.py --review
python pdfconverter\tools\convert_all.py --review --chunk K1P4

# one chunk
python pdfconverter\tools\convert_chunk.py --chunk K1P1 --json reports\K1P1.convert.json
python pdfconverter\tools\grade_chunk.py  --chunk K1P1
python pdfconverter\tools\diff_report.py  --chunk K1P1

# table-only review (Grantha render + Devanagari + raw bytes, every cell)
python pdfconverter\tools\table_report.py

# optional page images (LibreOffice + pypdfium2)
python pdfconverter\tools\render_pages.py --chunk K1P1 --pages 1-2

# while the canonical .docx is open in Word, work on the side build instead
python pdfconverter\tools\render_pages.py --chunk K1P1 --pages 1-2 `
  --path data\chunks\K1P1.devanagari.docx.new.docx --out reports\preview\new
python pdfconverter\tools\grade_chunk.py --chunk K1P1 `
  --path data\chunks\K1P1.devanagari.docx.new.docx

# regression gate (fails on any metric worse than the frozen baseline)
python pdfconverter\tools\check_scores.py
python pdfconverter\tools\check_scores.py --update --note "why this is intended"

# grade current decoders
python pdfconverter\tools\align_reference.py
$env:PYTHONPATH="pdfconverter\src"; python pdfconverter\tools\align_reference.py `
  --decoder convert_grantha_with_ref:convert_grantha_text

# mine map corrections
python pdfconverter\tools\learn_map.py --json reports\map_proposals.json
```

## Appendix B — Known measurement caveats

* Word-level confusions are noisy where the token counts differ (footnotes are
  inline in the grantha source). The next iteration of `learn_map.py` must skip
  unequal-length replace blocks; the current numbers are a *lower bound* on
  decoder quality, not an upper bound.
* `scratch/generate_complete_sanskrit2020.py` overwrites
  `data/output/1st Paadam Complete - Devanagari.docx` **on import**. It did so
  today during measurement; the file is a build artifact and is git-ignored, but
  the import side effect is a real bug to fix in Phase 3.
