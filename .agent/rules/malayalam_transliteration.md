---
description: Malayalam Vedic transliteration and orthography rules for Jaimineeya Samavedam
always_apply: true
---

# Malayalam Vedic Transliteration & Orthography Rules

When transliterating or curating Jaimineeya Samavedam texts in Malayalam script and generating the companion Devanagari KPully edition:

## 1. Short (ह्रस्व) vs Long (दीर्घ) E & O Swaras
- In Devanagari Sanskrit, "ए" and "ओ" are inherently diphthongs/long (दीर्घ).
- In Malayalam Vedic manuscripts (Namboothiri Grantha-Malayalam tradition), **short vowels (ह्रस्व)** are systematically used in place of long vowels in conjuncts, vocatives, stobha particles, and specific sandhi positions:
  - **E Swara**: Use short `െ` (`U+0D46`) / `എ` (`U+0D0E`) instead of long `േ` (`U+0D47`) / `ഏ` (`U+0D0F`) where appropriate:
    - Conjuncts & clusters: `അഗ്നേ` $\rightarrow$ `അഗ്നെ`, `ത്വമഗ്നേ` $\rightarrow$ `ത്വമഗ്നെ`, `വിശ്വേ` $\rightarrow$ `വിശ്വെ`, `ദ്വേ` $\rightarrow$ `ദ്വെ`, `ക്ഷേ` $\rightarrow$ `ക്ഷെ`.
    - Sibilants & verb endings: `ഷേ` $\rightarrow$ `ഷെ` (e.g., `നുഷേ` $\rightarrow$ `നുഷെ`, `സ്തുഷേ` $\rightarrow$ `സ്തുഷെ`, `ജനുഷേ` $\rightarrow$ `ജനുഷെ`, `ശൈരീഷേ` $\rightarrow$ `ശൈരീഷെ`).
    - Particles / Vocatives: `യേ` $\rightarrow$ `യെ`, `ദേ` $\rightarrow$ `ദെ`.
  - **O Swara**: Use short `ൊ` (`U+0D4A`) / `ഒ` (`U+0D12`) instead of long `ോ` (`U+0D4B`) / `ഓ` (`U+0D13`):
    - Sibilants & endings: `ഷോ` $\rightarrow$ `ഷൊ` (e.g., `ആഇഷോ` $\rightarrow$ `ആഇഷൊ`, `സാഇഷോ` $\rightarrow$ `സാഇഷൊ`, `ഹാഇഷോ` $\rightarrow$ `ഹാഇഷൊ`, `ഇഷോ` $\rightarrow$ `ഇഷൊ`, `ദക്ഷോ` $\rightarrow$ `ദക്ഷൊ`, `മാനുഷോ` $\rightarrow$ `മാനുഷൊ`).
    - Conjuncts: `രാക്ഷാണോ` $\rightarrow$ `രാക്ഷാണൊ`, `സ്തോ` $\rightarrow$ `സ്തൊ`, `ദ്രോ` $\rightarrow$ `ദ്രൊ`, `ക്ഷോ` $\rightarrow$ `ക്ഷൊ`.
    - Stobhas & vocatives: `ഹോ` $\rightarrow$ `ഹൊ` (e.g., `ഹോവാ` $\rightarrow$ `ഹൊവാ`, `ഹോഇ` $\rightarrow$ `ഹൊഇ`), `നോ` $\rightarrow$ `നൊ`, `ദോ` $\rightarrow$ `ദൊ`, `ഭോ` $\rightarrow$ `ഭൊ`.

### Malayalam $\rightarrow$ Devanagari KPully Transliteration Policy
- **Default (Native Sanskrit Orthography)**: When transliterating Malayalam to Devanagari for the KPully edition, deergha is **NOT** made hrsva (`preserve_hrsva=False`). Devanagari retains standard classical Sanskrit vowels (`ए`/`े`, `ओ`/`ो`) and standard Sanskrit feminine noun endings (`संहिता`, `माला`).
- **Optional (`preserve_hrsva=True` / CLI `--preserve-hrsva`)**: If explicitly enabled, the Dravidian short vowels (`ऎ`, `ऒ`, `ॆ`, `ॊ`) are preserved in the Devanagari output.
- **Malayalam Source & Displays**: The Malayalam texts remain unmodified as curated in the OCR/manually verified files with authentic short vowels.

## 2. Short (ह्रस्व) I Swara Reductions
- **Root *Gira-***: In Sanskrit roots derived from *giraḥ* / *girā* (गिरा / गिरः):
  - `ഗീരാഃ` $\rightarrow$ `ഗിരാഃ` (e.g., `ങ്ഗീരാഃ` $\rightarrow$ `ങ്ഗിരാഃ`, `യോഗീരാഃ` $\rightarrow$ `യോഗിരാഃ`, `നോഗീരാഃ` $\rightarrow$ `നോഗിരാഃ`).
- **Prefix/Root *Dvi-***: In words with prefix *dvi* (द्वि):
  - `ദ്വീ` $\rightarrow$ `ദ്വി` (e.g., `തദ്വീ` $\rightarrow$ `തദ്വി`, `ദ്വീവിഡ്ഢി` $\rightarrow$ `ദ്വിവിഡ്ഢി`).
- ***Viśā* Form**: In words derived from root *viś* (विशा):
  - `വീശാ` $\rightarrow$ `വിശാ` (e.g., `വീശാഇവാ` $\rightarrow$ `വിശാഇവാ`).
- **Conjunct *Jñi-***: In conjuncts with *jñi* (ज्ञि, such as *yajñiya*):
  - `ജ്ഞീ` $\rightarrow$ `ജ്ഞി` (e.g., `യാജ്ഞീ` $\rightarrow$ `യാജ്ഞി`).

## 3. Conjunct Vya (വ്യാ / വ്യ) — Manual Curation
- While many words with conjunct `വ്യ` use short `അ` (`വ്യ`) in Vedic Malayalam chanting (e.g., `ഹവ്യദാ`, `ഹവ്യവാഹ`, `നവ്യ`), there are context-specific exceptions.
- **Do NOT automatically replace `വ്യാ` $\rightarrow$ `വ്യ` in processing scripts.** Exceptions are to be corrected by hand in input files and must not be reset on subsequent automated runs.

## 4. Repha (Vocalic R)
- Consonant-preceding Repha (`ർ` / `ര\u0D4D`) is rendered with the traditional Vedic Repha symbol `൪` / `ൎ` (e.g., `ർഹാ` $\rightarrow$ `൪ഹാ`, `ർവാ` $\rightarrow$ `൪വാ`).
- In reverse transliteration to Devanagari, `[൪\u0D4E](?=[ക-ഹ])` is restored to `ര്`.

## 5. Vedic LLA / ZHA
- Devanagari Vedic `ळ` (`U+0933`) and `ळ्ह` (`U+0934`) are rendered as Malayalam `ഴ` (`U+0D34`) / `ഴ്` (e.g., `ഇഴാ` for `इळा` / `ഇള`).
- In reverse transliteration to Devanagari, Malayalam `ഴ` / `ऴ` maps to Vedic `ळ`.

## 6. Word-Final Vowels & Anusvara
- Word-final long AA matra is shortened in Malayalam titles (e.g., `സംഹിതാ` $\rightarrow$ `സംഹിത`, `മാലാ` $\rightarrow$ `മാല`).
- When transliterating to Devanagari by default, standard Sanskrit title endings are restored (`संहिता`, `माला`).
- Word-final halant `മ്` is normalized to anusvara `ം` (e.g., `സൂക്തമ്` $\rightarrow$ `സൂക്തം`).
- Word-final halant `ന്` before punctuation simplifies to chillu-n `ൻ`.

## 7. Melodic Arcs & Slurs (MOD-A, MOD-A1, MOD-A2)
- **`MOD-A` (`(A)` / `⁀`, `U+E004`)**: Syllable-spanning arc bridging across to the following syllable (`left: 100%; transform: translateX(-40%)`).
- **`MOD-A1` (`(A1)`, `U+E00D`)**: Syllable-spanning arc over danda separator (`left: 100%; transform: translateX(5%)`).
- **`MOD-A2` (`(A2)`, `U+E02E`)**: Overhead curved arc placed directly centered on top of the single conjunct syllable itself (e.g., `ഹൊ(A2)`, `left: 50%; transform: translateX(-50%)`).
