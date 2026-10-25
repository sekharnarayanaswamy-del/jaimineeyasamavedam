"""
Ganapathy (legacy Grantha TTF) -> Unicode Devanagari decoder.

Single source of truth for the byte->akshara mapping used by the
Taittiriya Samhita conversion.  Pure module: importing it performs no I/O
and has no side effects (unlike scratch/generate_complete_sanskrit2020.py,
which re-runs the whole conversion on import).

Terminology
-----------
*Grantha bytes* are the ASCII / Latin-1 code points stored in the .docx
runs that are typeset with "GANAPATHY - GRANTHA FONT.ttf".  The encoding is
a legacy 8-bit "Tamil-style" layout encoding: pre-base kombu (`1`) for the
e/o vowels, trailing consonants, and dedicated code points for subscripts.

The decoding model is a small **syllable transducer**, not a character map:

    pass 1  normalise typing noise (swara/virama transposition)
    pass 2  reorder:  kombu `1` (pre-base) -> vowel sign after the cluster
                      repha `9` (trailing) -> `र्` before the cluster
    pass 3  longest-match decode: consonant + subscripts + matra + swaras
    pass 4  canonicalise the Unicode cluster order
    pass 5  punctuation / leftovers

Keep every mapping decision here so the converter, the chunk builder and
the evaluation harness all agree.
"""
from __future__ import annotations

import re

DECODER_VERSION = "2026-10-25.v5-subscripts"

# ---------------------------------------------------------------------------
# 1. Mapping tables
# ---------------------------------------------------------------------------

# Base consonants.  A value may be a multi-character cluster (`त्व`, `श्र`),
# in which case dependents are appended after it.
CONSONANTS: dict[str, str] = {
    "y": "क", "Y": "ख", "„": "ख", "u": "ग", "U": "घ",
    "j": "ब", "i": "च", "I": "च", "C": "न्न",
    "O": "ज", "t": "ए", "A": "ठ", "s": "ड", "d": "ण",
    "D": "त", "f": "थ", "F": "द", "g": "ध", "X": "ध",
    "G": "न", "h": "प", "P": "फ", "b": "ह", "B": "न्त",
    "J": "भ", "k": "म", "K": "य", "l": "र", "L": "ल",
    "z": "व", "x": "श", "c": "ष", "v": "स", "T": "ओ",
    "Ô": "म", "Z": "त्व", ">": "श्र",
    # rare glyphs identified from aligned evidence
    "o": "छ", "a": "ट", "Ö": "व", "Š": "ज्", "?": "ङ्",
    "<": "न्", "N": "ञ्ज", "V": "ञ्च", "&": "ञ्च",
    # `#` is a complete न्द conjunct, not a subscript: the source writes the
    # vowel of the following syllable *after* it (`1#` = न्दे, `11#` = न्दै)
    # and puts a left-side मात्रा *before* it (`F]#` = दि + न्द).
    "#": "न्द",
    "{": "क्त",
}

# Dependent signs: subscript consonants (implicit virama) and virama variants.
SUBSCRIPTS: dict[str, str] = {
    "²": "्व", "ª": "्न", "§": "्थ", "¢": "्ठ", "°": "्म",
    "µ": "्स", "´": "्ष", "¥": "्ण", "£": "्ड", "©": "्ध",
    # `®` is NOT ्र: the print writes `G®Ý:` = न्ब्रह्म,
    # `Y´(+1v83L“®kv]` = क्षत्रस्योल्बमसि, `hF®Ý7K3` = पद्ब्रूया,
    # `F®4b1Fz` = द्बृहदेव, `1i3L®d1k1z3h` = चोल्बणम् — i.e. ्ब.
    # Mapping it to ्र produced the invalid `न्र्रह्म`.
    "®": "्ब", "¯": "्भ", "±": "ल्ँ", "ˆ": "्च", "…": "्ग",
    "†": "्घ", "«": "्प", "»": "्त्व", "Ÿ": "्र",
    "~": "द्व", "ƒ": "्क", "M": "त्", "H": "्फ", "S": "ष्",
    "Ú": "्स्", "0": "्", "8": "्य", "¦": "्त", "\\": "्र",
    "³": "्श", "@": "न्ध", ":": "ह्म", "$": "न्व", "¨": "द्",
    "º": "्द्व", "¹": "्त्र", "Ý": "्र", "Œ": "्न", "¡": "्ट",
    "¬": "्फ", "Ê": "्ण", "‰": "्छ",
    # Rare slots that the typesetter only used a handful of times.  The
    # values come from (a) the SETHU oracle (`Ë` makes
    # `ज्योतिरङ्क्ताम्` exact) and (b) glyph-outline matching inside this
    # font (`Ì` is 98 % identical to `थ`).  `Æ`/`¶` only occur in the
    # द्वित्व demonstration of Prasna 1's prātiśākhya block, where doubled
    # consonants are the point; they are marked for visual review.
    "Ë": "्त", "Ì": "्थ",          # oracle-confirmed / shape-matched
    "Æ": "्ट", "¶": "ह्",          # doubling demo (no oracle)
    # Deep-band duplicates and rare slots, read off enlarged renders of the
    # Grantha print (the द्वित्व table deliberately doubles the subscript):
    #   ‡  प्रत्यङ्ङुपनतः, सदृङ्ङ्, उदङ्ङ्            -> ्ङ
    #   Ð  नस्स्पर्शपरात्                            -> ्प
    #   Î  वृङ्ग्धि                                   -> ्ध
    #   ß  दधिक्क्राव्ण्णः, ब्ब्रु, ग्ग्र              -> ्र
    #   ¼  शल्कैक्कः (क with two stacked क्)          -> ्क
    #   ¾  अग्ग्ग्नये (ग with two stacked ग्)          -> ्ग
    "‡": "्ङ", "Ð": "्प", "Î": "्ध", "ß": "्र", "¼": "्क", "¾": "्ग",
    # `Ù` is the deep-band duplicate of `´` (्ष); it only ever follows ख,
    # spelling क्ष the same way `Y´` does.
    "Ù": "्ष",
}

INDEPENDENT_VOWELS: dict[str, str] = {
    "q": "अ", "Q": "आ", "w": "इ", "W": "ई", "e": "उ", "E": "ऊ",
}

# Post-base vowel signs.
MATRAS: dict[str, str] = {
    "3": "ा", "[": "ी", "]": "ि", "6": "ु", "7": "ू",
    "4": "ृ", "2": "ौ", "r": "ृ",
}

DIGITS: dict[str, str] = {
    "æ": "०", "ç": "१", "è": "२", "é": "३", "ê": "४",
    "ë": "५", "ì": "६", "í": "७", "î": "८", "ï": "९",
    "ä": "(", "å": ")",
}

# Vedic swara accents.
SWARAS: dict[str, str] = {
    "(": "\u0952",   # anudatta
    ")": "ꣳ",        # Vedic anusvara (the source uses a separate glyph)
    "”": "\u0951",   # udatta
    "!": "\u1CDA",   # dirgha svarita / kampam
    "=": "\u1CDA",
}

ACCENTS = "\u0951\u0952\u1CDA"
# characters that may sit *inside* a token without ending a cluster
SWARA_CHARS = "()”!="
DIGIT_CHARS = "".join(DIGITS) + ""

# Whole-token / prefix overrides.  Deliberately empty.
#
# An earlier version carried ~34 whole-phrase entries ("स्वरविधिः",
# "प्रातिशाख्यम्", "संहिता", "सूत्रलक्षणम्", …).  They were not read off the
# Grantha: they were copied from the garbled Devanagari reference in
# `data/input/1st Paadam (First 10 Pages) - Devanagari_corr.docx`, whose table
# is itself broken.  Rendering the Grantha glyphs shows the real readings are
# `सप्तलक्ष`, `प्रातिशा`, `षड्विंशति`, `विलङ्घ्यम्`, `विसर्गान्तम्`,
# `धकारादिः`, `प्रग्रहम्` — i.e. exactly what the compositional transducer
# produces.  Keep this dict for the learners' benefit, but leave it empty:
# a whole-token guess can silently override every rule below it.
COMPOUNDS: dict[str, str] = {}

# Editorial markers.  `{१४}` is an anuvaka number and `[२१]` a page /
# footnote reference; their brackets are literal, unlike the `[`/`]` that also
# serve as ि/ी inside ordinary words (`11D[kv;b]D3` = तैत्तिरीयसंहिता).  Only a
# bracketed run of Grantha *digits* counts, and it may be glued to an ornament
# or a word (`֍{çê}`, `।।{çç}`), so the whole token is searched.
_MARKER_DIGITS = "".join(sorted({k for k, v in DIGITS.items()
                                if v in "०१२३४५६७८९"}))
_MARKER_RE = re.compile(r"([\[{])([" + re.escape(_MARKER_DIGITS) + r"]+)([\]}])")
_MARKER_PAIRS = {"[": "]", "{": "}"}
# The typesetter occasionally put a space after the bracket (`{ èè}`), which
# would split the marker across two whitespace-delimited tokens.
_MARKER_SPACE_RE = re.compile(
    r"([\[{])\s+([" + re.escape(_MARKER_DIGITS) + r"]+)([\]}])")


def join_spaced_markers(text: str) -> str:
    """Glue a marker whose bracket was separated from its digits by a space."""
    def repl(m: re.Match[str]) -> str:
        if _MARKER_PAIRS[m.group(1)] != m.group(3):
            return m.group(0)
        return m.group(1) + m.group(2) + m.group(3)
    return _MARKER_SPACE_RE.sub(repl, text)


def find_marker(word: str) -> tuple[int, int, str, str, str] | None:
    """Locate the first ``(open, digits, close)`` marker in *word*.

    Returns ``(start, end, open, digits, close)`` so the caller can decode the
    text before and after the marker normally.
    """
    for m in _MARKER_RE.finditer(word):
        if _MARKER_PAIRS[m.group(1)] == m.group(3):
            return m.start(), m.end(), m.group(1), m.group(2), m.group(3)
    return None


# Sanskrit 2020 private-use precomposed glyphs.
PUA_GUM_ANUDATTA = "\uE006"
PUA_GUM_UDATTA = "\uE003"
PUA_GUM = "\uE004"

# Backwards-compatible flat view (longest entries first).
GANAPATHY_MAP: dict[str, str] = {}
for _k, _v in COMPOUNDS.items():
    GANAPATHY_MAP[_k] = _v
GANAPATHY_MAP.update({k: v for k, v in SUBSCRIPTS.items()})
GANAPATHY_MAP.update({k: v for k, v in CONSONANTS.items()})
GANAPATHY_MAP.update({k: v for k, v in INDEPENDENT_VOWELS.items()})
GANAPATHY_MAP.update({k: v for k, v in MATRAS.items()})
GANAPATHY_MAP.update({k: v for k, v in DIGITS.items()})
GANAPATHY_MAP.update({k: v for k, v in SWARAS.items()})

# Retained names for older callers.
GRANTHA_DIGITS = {k: v for k, v in DIGITS.items() if v in "०१२३४५६७८९"}
SWARA_MAP = dict(SWARAS)
ASCII_DIGITS = {str(i): str(i) for i in range(10)}

def is_tamil(text: str) -> bool:
    return any(0x0B80 <= ord(ch) <= 0x0BFF for ch in text)



# ---------------------------------------------------------------------------
# 2. Normalisation / canonicalisation
# ---------------------------------------------------------------------------

def normalize_typing(word: str) -> str:
    """Reverse common typing transpositions of swaras and viramas.

    The typesetter sometimes emitted `क(्` instead of `क्(`, or a matra before
    its swara.  Reorder so the transducer sees the canonical byte order.
    """
    word = re.sub(r"([^\s\(\”\!\=\.\,\*\;\-\–\—ã‚֍\d]+)([\(\”\!\=]+)\\",
                  r"\1\\\2", word)
    word = re.sub(r"([^\s\(\”\!\=\.\,\*\;\-\–\—ã‚֍\d]+)([\(\”\!\=]+)([3\[\]6742])",
                  r"\1\3\2", word)
    return word


def canonicalize(text: str) -> str:
    """Enforce the canonical OpenType cluster order expected by Sanskrit 2020."""
    if not text:
        return ""
    text = text.replace("\u25CC", "")
    # a non-breaking space is still a space; the source uses one before the
    # closing danda of a few prātiśākhya lines and the gate counts it as a
    # leftover legacy byte.
    text = text.replace("\u00a0", " ")

    # anusvara + candrabindu -> candrabindu (KYV orthography)
    text = re.sub(r"\u0902\s*\u0901|\u0901\s*\u0902", "\u0901", text)

    # Vedic gum (U+A8E3) + accent -> precomposed PUA glyph
    text = text.replace("\uA8E3\u0952", PUA_GUM_ANUDATTA)
    text = text.replace("\uA8E3\u0951", PUA_GUM_UDATTA)
    text = text.replace("\u0902\u0952", PUA_GUM_ANUDATTA)
    text = text.replace("\uA8E3", PUA_GUM)

    C = r"[\u0915-\u0939]"
    V = r"[\u0905-\u0914]"
    M = r"[\u093E-\u094C\u0962\u0963]"
    A = r"[\u0951\u0952\u1CDA]"

    # accent after a virama belongs to the following consonant
    for _ in range(4):
        text = re.sub(
            r"(" + C + r")(" + A + r")\u094D(" + C + r")",
            lambda m: m.group(1) + "\u094D" + m.group(3) + m.group(2),
            text,
        )
        text = re.sub(r"(" + A + r")\u094D", "\u094D", text)

    # accent must follow the matra, never precede it
    for _ in range(4):
        text = re.sub(
            r"(" + C + r"|" + V + r")(" + A + r")(" + M + r")",
            lambda m: m.group(1) + m.group(3) + m.group(2),
            text,
        )
    text = re.sub(r"(" + M + r")\u094D", lambda m: m.group(1), text)
    text = re.sub(r"(" + A + r")" + A + r"+", lambda m: m.group(1), text)

    # क्ष is typeset as ख + subscript ष (see MULTI `Y´`).  When a swara falls
    # between the two glyphs the MULTI entry cannot fire, so fold the resulting
    # (invalid) ख्ष here, keeping any accent after the cluster.
    text = re.sub(r"ख(" + A + r"*)्ष", lambda m: "क्ष" + m.group(1), text)

    # A Vedic accent before a syllable-closing mark (visarga, anusvara,
    # candrabindu) is drawn with a dotted circle: both characters are marks, so
    # the shaper sees no base for the second one.  Printed editions put the
    # accent after the mark instead (`नमः॒`, `तां॑`, `वायवः॑`), which shapes
    # cleanly.  Same fix the DOM inserts whitespace for elsewhere.
    for _ in range(2):
        text = re.sub("(" + A + r")([\u0901-\u0903])",
                      lambda m: m.group(2) + m.group(1), text)

    # an orphan matra became an independent vowel
    for matra, vowel in {
        "\u0947": "ए", "\u0948": "ऐ", "\u094B": "ओ", "\u094C": "औ",
        "\u093E": "आ", "\u093F": "इ", "\u0940": "ई", "\u0941": "उ",
        "\u0942": "ऊ", "\u0943": "ऋ",
    }.items():
        text = re.sub(r"(^|[^\u0915-\u0939])" + matra, r"\1" + vowel, text)

    text = text.replace("एे", "ए").replace("ओो", "ओ").replace("ऐै", "ऐ")
    text = text.replace("ã", " ")
    text = re.sub(r"\u094D\u094D+", "\u094D", text)
    text = re.sub(r"\u094D(" + A + r")", lambda m: m.group(1), text)

    # a swara with no base character is meaningless
    text = re.sub(r"(^|[^\u0905-\u0939\u093E-\u094C\u0901-\u0903])" + A + r"+",
                  lambda m: m.group(1), text)

    # The editors print a bracketed visarga as `(:)`.  Keep the printed colon:
    # a bare `ः` directly after `(` has no base and is drawn with a dotted
    # circle.  Only the bracketed form changes; visargas in the running text
    # stay Devanagari.
    text = text.replace("(\u0903)", "(:)")
    return text


# ---------------------------------------------------------------------------
# 3. Syllable transducer
# ---------------------------------------------------------------------------

# Multi-byte ligatures, longest first.  Checked before single bytes.
MULTI: list[tuple[str, str]] = [
    ("h\\", "प्र"), ("b\\", "ह्र"), ("v\\", "स्र"),
    ("{6", "क्तु"),
    # SETHU prints every क्ष as ख्ष (150 of them vs 7 real क्ष) — a
    # publisher font artifact.  `Y` on its own really is ख (`खलु`, `सखा`),
    # but the cluster `Y´` is correct क्ष, not the invalid ख्ष.
    ("Y´", "क्ष"),
    # `„` is ख and `Ù` is its deep-band ्ष, so `„Ù` is the same ख+्ष
    # spelling of क्ष that `Y´` uses: `?„Ù[K1D` = ङ्क्षीयते
    # (`अन्नं क्षीयते`), `?„Ù(+h` = ङ्क्ष॒त्रप, `11?=„Ù+h` = ऐक्षत्रपत्य.
    ("„Ù", "क्ष"),
    ("%", "ष्ट"), ("/", "ज्ञ"), ("+", "त्र"),
]

PUNCTUATION: dict[str, str] = {
    ".": "॥",   # end-of-mantra danda in the source
    "-": "।",   # intra-text danda
    "*": "॥",
    ",": "ः",
    # `;` is the anusvara: a small dot above the line, not the letter म्.
    # The print writes `संहिता`, `षड्विंशति`, `द्वित्वं`, `तं`; the separate
    # final म् is the `*` glyph (`विलङ्घ्यम्`, `विसर्गान्तम्`).
    ";": "\u0902",
    "‚": "ऽ",
    "ã": " ",
    "“": "",
    "™": "ꣴ",   # "gum" (nasal) glyph: Sanskrit 2020 A8F4 precomposed form
    "֍": "֎",
    # Editorial marks used in the prātiśākhya block: `^` is the final म् of
    # a word that the demonstration joins to the next one, `˜` is the
    # "insert here" cross printed between the two halves of a sandhi pair.
    "^": "म्",
    "˜": "+",
    # Blank slots.  `û` is an empty glyph with the same 500-unit advance as the
    # space; the typesetter used it for the trailing space of the page-reference
    # cells (`१ –१०û`).  Left unmapped it would surface as a foreign character.
    "û": " ",
    "\u00a0": " ",
}

_CONSONANT_CHARS = set("".join(CONSONANTS.values()))

_GLYPH_TABLES = (COMPOUNDS, SUBSCRIPTS, CONSONANTS, INDEPENDENT_VOWELS,
                 MATRAS, DIGITS, SWARAS, PUNCTUATION)

# Grantha glyphs that must never survive decoding.  Used by the audit.
#
# ASCII keys are deliberately excluded: ASCII letters are covered by the
# separate `latin_letters` audit, and ASCII punctuation / digits (`(`, `)`,
# `,`, `.`, `-`, `0`-`9`) occur legitimately in the already-Unicode Tamil
# commentary and in the table range column (`2-50`).
LEGACY_BYTES = {key for table in _GLYPH_TABLES for key in table
                if len(key) == 1 and not key.isascii()}

# Bytes that can only ever be Grantha text: consonants, subscripts,
# independent vowels and the Ganapathy digits.  Vowel signs are excluded
# because `2`/`3`/`4`/`[`/`]` also occur in ordinary numbers, so a run needs
# one of *these* before it is worth decoding at all.
GRANTHA_TRIGGERS = (set(CONSONANTS) | set(SUBSCRIPTS)
                    | set(INDEPENDENT_VOWELS)
                    | {key for key in DIGITS if not key.isascii()}
                    | {"֍"})   # ornament-only runs (`֍ ֍ ֍`) still convert

# The only legacy glyphs that also occur legitimately in the Tamil
# commentary: the typesetter typed curly quotes around Tamil phrases.  The
# audit therefore has to look at their context instead of banning them.
TAMIL_QUOTES = "\u201C\u201D"

# Tokens built only from these characters keep their Unicode form.
_PLAIN_CHARS = (set(PUNCTUATION) | set(DIGITS) | set("0123456789")) - set(TAMIL_QUOTES)


_CLOSING_PUNCT = ".,;:!?)]\u2019\u201D"
_OPENING_PUNCT = "([\u2018\u201C"


def hugs_tamil(text: str, i: int) -> bool:
    """Is the quote at `i` quoted *by* Tamil rather than a Grantha accent?

    An opening quote hugs the Tamil that follows it, a closing quote hugs the
    Tamil that precedes it (sentence punctuation in between is skipped, as in
    `கார்யம்.”`).  In `त्वा ”என்பது` the `”` is preceded by a space, so it is a
    stray accent and not a quotation mark.
    """
    if text[i] == "\u201C":
        j = i + 1
        while j < len(text) and (text[j] in _OPENING_PUNCT or text[j].isspace()):
            j += 1
        return j < len(text) and 0x0B80 <= ord(text[j]) <= 0x0BFF
    j = i - 1
    while j >= 0 and (text[j] in _CLOSING_PUNCT or text[j].isspace()):
        j -= 1
    if j >= 0 and 0x0B80 <= ord(text[j]) <= 0x0BFF:
        return True
    # `”` is also typed as an *opening* quote in the Tamil commentary.
    j = i + 1
    while j < len(text) and (text[j] in _OPENING_PUNCT or text[j].isspace()):
        j += 1
    return j < len(text) and 0x0B80 <= ord(text[j]) <= 0x0BFF


def leftover_bytes(text: str) -> list[str]:
    """Grantha bytes still present in an already-decoded string."""
    tamil_context = any(0x0B80 <= ord(ch) <= 0x0BFF for ch in text)
    out = set()
    for i, ch in enumerate(text):
        if ch not in LEGACY_BYTES:
            continue
        if ch in TAMIL_QUOTES and (hugs_tamil(text, i) or tamil_context):
            continue
        out.add(ch)
    return sorted(out)


def _take_swaras(word: str, i: int) -> tuple[list[tuple[str, str]], int]:
    """Consume a run of swara bytes as individual units."""
    units = []
    while i < len(word) and word[i] in SWARA_CHARS:
        units.append((word[i], SWARAS[word[i]]))
        i += 1
    return units, i


_ACCENT_CHARS = set(ACCENTS)
# repha is written *after* its syllable but rendered before the onset
REPHA_BYTES = {"9"}
_ACCENT_VALUES = {"\u0951", "\u0952", "\u1CDA"}
_MATRA_VALUES = set(MATRAS.values())


def _consume_onset(word: str, i: int) -> tuple[list[tuple[str, str]], int]:
    """Consume the base consonant (or ligature) of one akshara."""
    multi = next((m for m in MULTI if word.startswith(m[0], i)
                  and m[1][0] in _CONSONANT_CHARS), None)
    if multi is not None:
        return [(multi[0], multi[1])], i + len(multi[0])
    if i < len(word) and word[i] in CONSONANTS:
        return [(word[i], CONSONANTS[word[i]])], i + 1
    return [], i


def _insert_repha(units: list[tuple[str, str]], ch: str) -> None:
    """Attach a trailing repha to the onset of the previous syllable."""
    for k in range(len(units) - 1, -1, -1):
        if units[k][1][:1] in _CONSONANT_CHARS:
            units.insert(k, (ch, "र्"))
            return
    units.append((ch, "र्"))


def _consume_akshara(word: str, i: int, units: list[tuple[str, str]]):
    """Consume swaras and dependent signs after an onset, in source order.

    The typesetter puts swaras *inside* the akshara (`त + ॑ + ्य + ु`), so
    subscripts, accents and repha marks have to be interleaved rather than
    consumed in phases.  A swara that comes *before* a subscript is flushed
    first: that order (`र्॒`) is what lets the canonicaliser move the accent
    onto the full cluster and keep the virama (`र्हि॒`).  If the swara were
    emitted after the virama instead, the virama would look stray and be
    dropped (`बर्हि` became `बरहि`).
    """
    swaras: list[tuple[str, str]] = []
    while i < len(word):
        ch = word[i]
        if ch in SWARA_CHARS:
            swaras.append((ch, SWARAS[ch]))
            i += 1
        elif ch in REPHA_BYTES:
            units.extend(swaras)
            swaras = []
            _insert_repha(units, ch)
            i += 1
        elif ch in SUBSCRIPTS:
            units.extend(swaras)
            swaras = []
            _insert_subscript(units, ch, SUBSCRIPTS[ch])
            i += 1
        else:
            break
    return swaras, i


def _insert_subscript(units: list[tuple[str, str]], ch: str, value: str) -> None:
    """Attach a subscript; the source writes it *after* a vowel sign, but it
    belongs to the consonant before that sign (`ग ी ्र` -> `ग ्र ी`)."""
    k = len(units) - 1
    while k >= 0 and units[k][1] in _ACCENT_VALUES:
        k -= 1
    # A dependent glyph that itself spells a full cluster (`~` = द्व, `@` =
    # न्ध) starts a new syllable when a vowel sign precedes it: `व ि + द्व` is
    # विद्व, not वद्वि.  A true subscript (`्र`, `्ष`, ...) begins with a
    # virama and keeps the reordering rule below.
    if (not value.startswith("\u094D")
            and value[:1] in _CONSONANT_CHARS
            and k >= 0 and units[k][1] in _MATRA_VALUES):
        units.append((ch, value))
        return
    if k >= 0 and units[k][1] in _MATRA_VALUES:
        units.insert(k, (ch, value))
        return
    # a subscript that starts with a virama replaces a virama that is already
    # there (`ङ्` + `्ग` is `ङ्ग`, not `ङ््ग`)
    if value.startswith("\u094D") and units:
        j = len(units) - 1
        while j >= 0 and units[j][1] in _ACCENT_VALUES:
            j -= 1
        if j >= 0 and units[j][1].endswith("\u094D"):
            src, out = units[j]
            units[j] = (src, out[:-1])
    units.append((ch, value))


def _decode_kombu(word: str, i: int) -> tuple[list[tuple[str, str]], int]:
    """Decode a pre-base `1` (e / ai / o / au) syllable starting at i."""
    n = len(word)
    start = i
    is_ai = word.startswith("11", i)
    i += 2 if is_ai else 1

    cluster, i = _consume_onset(word, i)
    sw, i = _consume_akshara(word, i, cluster)

    if i < n and word[i] == "3":
        sign = "ौ" if is_ai else "ो"
        i += 1
    else:
        sign = "ै" if is_ai else "े"

    extra, i = _take_swaras(word, i)

    if not cluster:
        base = {"ो": "ओ", "ौ": "औ", "ै": "ऐ", "े": "ए"}[sign]
        return [(word[start:i], base)] + sw + extra, i
    return cluster + [("11" if is_ai else "1", sign)] + sw + extra, i


def _append_matra(units: list[tuple[str, str]], ch: str, matra: str) -> None:
    """Attach a vowel sign, dropping a stray virama just before it."""
    if units and units[-1][1].endswith("्"):
        src, out = units[-1]
        units[-1] = (src, out[:-1])
    units.append((ch, matra))


def _literal_paren_close(word: str) -> int | None:
    """Index of the `)` that belongs to an editorial `( … )` citation.

    The editors cite grammatical forms as `(सः)`; the opening bracket cannot
    be an anudatta (it would have no base) and the closing one directly
    follows a visarga, where a gum is impossible.  Only then is the pair read
    as literal parentheses.
    """
    for idx, ch in enumerate(word):
        if ch == ")" and idx and word[idx - 1] == ",":
            return idx
    return None


def decode_units(word: str) -> list[tuple[str, str]]:
    """Decode a token into ``[(source_bytes, output_text), ...]``.

    Each unit is one source byte (or one multi-byte ligature) and its fixed
    output.  Units are emitted in *decoded* order; concatenating them and
    running `canonicalize` gives the final text.  Exact spans are what the
    map learners need to attribute an error back to its source byte.
    """
    if not word:
        return []

    if word.startswith("("):
        close = _literal_paren_close(word)
        if close is not None:
            return ([("(", "(")] + decode_units(word[1:close]) + [(")", ")")]
                    + (decode_units(word[close + 1:]) if close + 1 < len(word) else []))

    for src, tgt in COMPOUNDS.items():
        if word.startswith(src):
            return [(src, tgt)] + decode_units(word[len(src):])

    # `{N}` anuvaka numbers and `[N]` page references: the brackets are
    # literal here, while `[`/`]` are also the ि/ी vowel signs inside a word
    # (`11D[kv;b]D3` = तैत्तिरीयसंहिता), so only a bracketed run of digits
    # counts as a marker.  The marker may be glued to an ornament (`֍{चे}`),
    # so decode the text before and after it as usual.
    marker = find_marker(word)
    if marker:
        start, end, open_, inner, close = marker
        units = decode_units(word[:start]) if start else []
        units += [(open_, open_)] + decode_units(inner) + [(close, close)]
        if end < len(word):
            units += decode_units(word[end:])
        return units

    # a lone `*` is the final म् of the printed invocation `हरिः ओम्`, not a
    # danda: `bl], T äêå *` reads `हरिः ओ (४) म्` and carries no `॥`.
    if word == "*":
        return [("*", "म्")]

    # pure punctuation / digits: map punctuation, leave digits and ASCII
    # punctuation alone.  `”`/`“` are excluded on purpose: they are swara
    # bytes here and must reach the transducer (and then be discarded if
    # they end up orphaned).
    if all(ch in _PLAIN_CHARS for ch in word):
        return [(ch, PUNCTUATION.get(ch, DIGITS.get(ch, ch))) for ch in word]

    word = normalize_typing(word)
    word = word.replace("ã1", "1")

    units: list[tuple[str, str]] = []
    i, n = 0, len(word)
    while i < n:
        ch = word[i]

        multi = next((m for m in MULTI if word.startswith(m[0], i)), None)
        if multi is not None:
            units.append((multi[0], multi[1]))
            i += len(multi[0])
            continue

        if ch in DIGITS:
            units.append((ch, DIGITS[ch]))
            i += 1
            continue
        if ch in SWARA_CHARS:
            units.append((ch, SWARAS[ch]))
            i += 1
            continue
        if ch == "*":  # word-final म् (a lone `*` was handled above)
            units.append((ch, "म्"))
            i += 1
            continue
        if ch in PUNCTUATION:
            units.append((ch, PUNCTUATION[ch]))
            i += 1
            continue
        if ch in REPHA_BYTES:
            _insert_repha(units, ch)
            i += 1
            continue
        if ch == "1":
            piece, i = _decode_kombu(word, i)
            units.extend(piece)
            continue
        if ch in INDEPENDENT_VOWELS:
            units.append((ch, INDEPENDENT_VOWELS[ch]))
            i += 1
            sw, i = _take_swaras(word, i)
            units.extend(sw)
            continue
        if ch in CONSONANTS:
            cluster, i = _consume_onset(word, i)
            units.extend(cluster)
            sw, i = _consume_akshara(word, i, units)
            units.extend(sw)
            if i < n and word[i] in MATRAS:
                _append_matra(units, word[i], MATRAS[word[i]])
                i += 1
                extra, i = _take_swaras(word, i)
                units.extend(extra)
            continue
        if ch in MATRAS:
            _append_matra(units, ch, MATRAS[ch])
            i += 1
            continue
        if ch in SUBSCRIPTS:
            _insert_subscript(units, ch, SUBSCRIPTS[ch])
            i += 1
            continue

        units.append((ch, ch))
        i += 1

    return units


_LEADING_MARKS = re.compile(r"^[\u0900-\u0903\u093A-\u093C\u093E-\u094D"
                            r"\u0951\u0952\u1CDA]+")


def decode_token(word: str) -> str:
    """Decode one whitespace-delimited Grantha token."""
    text = canonicalize("".join(out for _, out in decode_units(word)))
    # A token that starts with a combining mark has no base: the typesetter's
    # stray space split the mark off its syllable (`नैः ः`, `थकार, ्फकार`).
    # Left alone it prints with a dotted circle, so drop the orphan marks.
    return _LEADING_MARKS.sub("", text)


def decode_text(text: str) -> str:
    """Decode a full paragraph, leaving Tamil commentary untouched."""
    if not text:
        return ""
    text = join_spaced_markers(text)
    parts = re.split(r"(\s+)", text)
    return "".join(
        p if p.isspace() else (p if is_tamil(p) else decode_token(p)) for p in parts
    )


def strip_accents(text: str) -> str:
    """Base-text form used for diagnostic scoring (swaras removed)."""
    text = text.replace(PUA_GUM_ANUDATTA, "\uA8E3").replace(PUA_GUM_UDATTA, "\uA8E3")
    text = text.replace(PUA_GUM, "\uA8E3")
    return re.sub(r"[\u0951\u0952\u1CDA]", "", text)
