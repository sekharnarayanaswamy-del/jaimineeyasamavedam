# Vision Extraction Prompt — JSV Samhita Malayalam Swara Modifiers

Canonical session preamble for every vision-extraction pass over manuscript
page crops. Read this in full before annotating any subsection.

---

## 1. Goal

Insert swara-modifier annotations `(A)`, `(A1)`, `(B)`, `(C)`, `(D)`, `(E)`,
`(F)`, `(G)`, `(H)`, `(L)` and inline phrasing marks (`_`, `.`, `,`) into
the master mantra body of `data/input/Malayalam/Samam_Malayalam_Unicode.txt`
by reading the rendered manuscript crops in `Malayalam_JSV/scans/`.

The master body is provided verbatim as the anchor. **You only insert tokens;
you never alter base Malayalam text, Grantha swara parenthesized tokens
(`(𑌤𑌿)`, `(𑌪𑍍𑌲)` …), dandas (`।`, `॥`), samam numerals, or whitespace.**

---

## 2. THE COLOR RULE (critical — this is the K2 pilot fix)

The manuscript is printed/written in **two inks**:

| Ink | What it is | Action |
|---|---|---|
| **RED** | Grantha swara *letters* and their handwritten flourishes (e.g. തി, ത്ത്, ഖ, ടു, and the hook/"4"-shaped ligatures). These are the swara markers **already transliterated from Devanagari** and already present in the master body as parenthesized Grantha tokens. | **IGNORE unconditionally.** Never emit a modifier token for anything red. Never transcribe a red mark into the body. |
| **BLACK** | Base Malayalam aksharas, dandas, numerals — **and the swara modifiers** (arcs, slashes, dots, bars, carets, underbars, commas, periods). | Extract the **non-base black marks** as modifier/inline tokens. |

> The previous (v1) pilot failed because it hunted *red* marks for modifiers.
> In the real manuscript, modifiers are written in the **same black pen as the
> base text**. Red ink is reserved for Grantha swara letters which are already
> captured downstream. **If you look at red ink for modifiers, you are doing it
> wrong.**

Spot-check before annotating: confirm you can see black period-dots after
words, black commas, black underbar connectors, and (for Kandah 2) many
black under-slashes. If you cannot see any black non-base marks on a line,
re-scan that line at higher zoom before concluding there are none.

---

## 3. Canonical Token Lexicon

From `Malayalam_JSV/malayalam/glyph_table.html` (12 modifiers & marks).
Write tokens exactly as shown in the "Token" column.

| Token | Name | Ink | Shape & Position | Footprint |
|---|---|---|---|---|
| `(A)` | Syllable-spanning arc | black | Flat/slur arch **above** the line, bridging two adjacent syllables/words | 2 syllables, above |
| `(A1)` | Arc over danda | black | Same arch centered **over a danda `।`** between phrases | over `।` |
| `(B)` | Peak caret | black | `^`-shaped roof **above** a syllable; may carry a swara glyph on its apex | above, 1–2 syl |
| `(C)` | Shoulder dot | black | Small dot at the **upper-right shoulder** of a syllable (raised, *not* on the baseline) | on 1 syllable |
| `(D)` | Chevron roof | black | Wide `Ʌ`-shaped roof **above** the line, spanning **2+ syllables across a word boundary** | above, 2+ syl |
| `(E)` | Heavy column | black | Bold vertical stroke **inline** at baseline height (heavier than a danda) | inline |
| `(F)` | Light tick | black | Thin short vertical tick **inline** | inline |
| `(G)` | **Descending slash** | black | Short straight/curved diagonal stroke attached **below** the baseline at the **bottom-right** of a single akshara; looks like a small `\`, `L`, or `4`-hook hanging beneath the character | **below, 1 syllable** |
| `(H)` | Swarita bar | black | Vertical stroke **above** and centered on a syllable (Vedic swarita) | above, 1 syl |
| `(L)` | Lower danda | black | Downward stem/inline bar (deep cadence) | inline |
| `_` | Sustain underbar | black | Horizontal low-line **connecting words at the baseline** (joins two adjacent mantra units) | inline, between words |
| `.` | Pause dot | black | Dot **inline at the baseline** after a word (stobha/breath pause) | inline |
| `,` | Low comma | black | Comma **inline** at baseline (minor cadence pause) | inline |

Notes:
- Dandas `।` (single) and `॥` (double) are **base punctuation**, already
  present in the master body. Never wrap them as a modifier.
- Numerals inside `॥ N ॥` samam-end markers are base text. Leave them.
- Grantha swara parenthesized tokens like `(𑌤𑌿)` already exist in the
  master body. Leave them untouched; only insert modifier tokens around them.

---

## 4. Density Priors (sanity floors)

From the curated corpus (`sub_1`–`sub_48`), measured distributions:

| Modifier | Share of all mods | Notes |
|---|---|---|
| `(C)` | ~38% (61/161) | Most frequent overall |
| `(G)` | ~29% (47/161) | Second overall; **in Kandah 2 it is 56% (33/59)** |
| `(H)` | ~16% (25/161) | |
| `(A)` | ~14% (22/161) | |
| `(D)` | ~3% (5/161) | Rare; **zero in K2 ground truth** |
| `(B)` | <1% (1/161) | Very rare |
| `(A1)`,`(E)`,`(F)`,`(L)` | trace | |

Kandah 2 (`sub_14`–`sub_24`) ground truth: **59 modifiers** →
G=33, C=21, A=2, H=2, B=1, D=0; plus 81 inline marks (`_`=37, `.`=33, `,`=11).

**Practical floor:** across ~11 K2 subsections you should find *dozens* of
`(G)` tokens. If your `(G)` count for a samam is zero or near-zero, you are
almost certainly missing them — re-scan the bottom-right of every akshara
before finalizing.

---

## 5. Two-Pass Protocol (mandatory per crop)

### Pass 1 — Transcription & all-mark scan
For each mantra line on the crop:
1. Locate the corresponding master body (the anchor). Copy it verbatim.
2. Walking left→right over the manuscript line, insert every **black** mark
   you can identify at the correct akshara, using the lexicon above.
3. If a samam continues across a crop boundary (e.g. samam 6 split as
   `k2_samam_5_6a.png` / `k2_samam_6b_7.png`), read **both** crops before
   annotating that samam, so the split is not double-counted or missed.

### Pass 2 — Dedicated `(G)` sweep (the most-missed mark)
Before emitting any line, do a second pass whose **only** job is to find `(G)`:
- For **every akshara** on the line, inspect the area **below its baseline,
  bottom-right corner**.
- `(G)` is a small black diagonal tick (often `\`, `L`, or `4`-hook shaped)
  hanging beneath a single akshara. It is subtle.
- Re-check every word that already received a `(C)`, `(H)`, or `(A)` —
  those aksharas frequently *also* carry a `(G)`.
- If in doubt between "no mark" and a faint `(G)`, look for the ink trace
  against the ruled baseline.

### Pass 3 — `(C)` shoulder sweep
Quick dedicated scan of the upper-right shoulder of every akshara for raised
black dots (distinguish from baseline `.` pause dots — see §6).

Only after all three passes, emit the annotated line.

### Samam boundary rule (critical)

A modifier mark belongs to the **samam in which it was detected**. It must
**not** carry over into the next samam. Concretely:

- The `॥ N ॥` numeral marker terminates a samam. Any modifier on an akshara
  **before** the marker belongs to samam N; any modifier on an akshara
  **after** the marker belongs to samam N+1.
- When a modifier visually sits at the boundary (e.g., an arc or underbar
  near the danda), assign it to the samam whose text it physically annotates
  — never push it forward.
- Each samam line in the candidate is annotated independently. Do not let
  a modifier detected in one samam "leak" into the next line.

---

## 6. Disambiguation Rules

| Confusion | Rule |
|---|---|
| `(G)` vs `(D)` | `(G)`: **narrow, below** the baseline, attached to **one** akshara, looks like `\`/`L`/`4`. `(D)`: **wide chevron above** the line, spanning **2+ syllables across a word boundary**. When a below-baseline single-akshara mark is ambiguous between G and D → **choose `(G)`**. (K2 ground truth has 0 true `(D)`; almost every "D" in the v1 pilot was a misread `(G)`.) |
| baseline `.` vs `(C)` | `.` sits **inline at the baseline** after a word (stobha pause). `(C)` sits **raised at the upper-right shoulder** of a syllable (Bindu-Svara). Both are black dots; position decides. |
| `_` vs decorative flourish | `_` is a **baseline low-line that connects two adjacent words/units**. A long ornamental underline beneath a samam's opening word (often wavy, spanning the whole word) is **decoration — skip it**, do not emit `_`. |
| danda `।`/`॥` vs `(E)`/`(L)` | Dandas are base punctuation (already in the master body). `(E)` is a **bold inline column heavier than a danda**; `(L)` is a downward stem. Only emit `(E)`/`(L)`/`(F)` for marks clearly heavier/lighter than the surrounding dandas. |
| `(A)` vs `(D)` | `(A)` is a flat/slur arch (smooth bridge). `(D)` is a peaked `Ʌ` chevron. Both span 2+ syllables above the line. |
| `(A1)` | Use only when the arch is centered **over a danda `।`** between phrases. |
| red hook/"4"-shape | Red ink = swara-letter flourish → **ignore**. A black `4`/`L`-hook **below** an akshara is `(G)`. |

---

## 7. Anchor & Output Contract

For each subsection you are given:
1. The master mantra body (one line per samam), verbatim, e.g.:
   ```
   ദൂ(𑌣) താം(𑌫). വോ(𑌖) വിശ്വവേദസാം(𑌶𑍁) ।ഹാ(𑌥) വ്യാവാ(𑌚), ഹാ(𑌟) മമാ(𑌟𑍁). ൪ത്താ(𑌖) യം(𑌣) ।യാ(𑌚)(G)_ ജിഷ്ഠ(𑌚)(G), മൃഞ്ജസേ(𑌟𑍁). ഹാ(𑌤) ഇ(𑌶) ।ഗീ(𑌚) രാ(C)ഔ(𑌟𑌾). ഹോ(𑌖)(A) ബാ(𑌪𑍍𑌲)(G) ।ഹോ(𑌪𑍍𑌲) ഇഴാ(𑌶𑌾)॥2॥
   ```
2. The matching manuscript crop(s).

Your output for that subsection is the same body with modifier tokens
**inserted** at the correct positions. Do not:
- reorder, delete, or add base aksharas
- change any `(𑌶𑌾)`-style Grantha parenthesized token
- change dandas, numerals, or whitespace runs
- introduce tokens outside the canonical lexicon in §3

Emit the candidate in the exact structural skeleton the merge tool expects
(see `Malayalam_JSV/extraction/merge_candidates.py` `SUBSECTION_RE`):

```
# Start of SubSection Title -- subsection_NN ## DO NOT EDIT
<title verbatim>
# End of SubSection Title -- subsection_NN ## DO NOT EDIT
#Start of Mantra Sets -- subsection_NN ## DO NOT EDIT
<annotated mantra line 1>
<annotated mantra line 2>
...
#End of Mantra Sets -- subsection_NN ## DO NOT EDIT
```

One body line per samam, matching the master's line layout exactly.

---

## 8. Uncertainty

Do **not** pollute the candidate file with annotations like `(?)`. If a mark
is genuinely unreadable, make your best-guess call inside the candidate
(per the disambiguation rules) and record the uncertain position in a separate
notes file `<candidate_basename>_notes.txt` in the same directory, e.g.:

```
subsection_18 samam_6 akshara "ഹാ(𑌟)" : unclear mark below baseline, guessed (G)
```

The merge tool only reads the candidate `.txt`; the notes file is for the
human curation pass in the interactive tool.

---

## 9. Pre-Emit Self-Checklist

Before writing a candidate file, verify:
- [ ] **Zero** red marks were transcribed as modifiers.
- [ ] `(G)` count is not suspiciously low (K2: expect several per samam).
- [ ] Every akshara's bottom-right was inspected for `(G)`.
- [ ] Baseline `.` vs raised `(C)` distinction held.
- [ ] Connecting `_` (between words) vs decorative flourish (single word)
      distinction held.
- [ ] Base text, Grantha parens, dandas, numerals are byte-identical to the
      master anchor (run `validate_modifiers.py` mentally; the merge tool
      will reject on any mismatch).
- [ ] No tokens outside the §3 lexicon.
- [ ] Split samams were annotated using both adjacent crops.
- [ ] Uncertain positions logged to `_notes.txt`, not into the candidate.

After emitting, the candidate will be validated by
`Malayalam_JSV/extraction/validate_modifiers.py` (zero base-text regressions
required) and scored by `Malayalam_JSV/extraction/eval_modifiers.py`
(token-level precision/recall vs ground truth).
