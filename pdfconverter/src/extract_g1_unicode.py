"""
Extract clean Unicode Devanagari text from g1_extr.pdf (or g1.pdf).
-------------------------------------------------------------------
- Decodes all Siddhanta Private Use Area (PUA) ligatures and width variants.
- Preserves the Vedic Tone Prenkha (U+1CD2 '᳒') horizontal overline strokes
  drawn via PDF vector graphics (.5738 w / .4782 w) over 'ऽ२'.
- Reorders visual pre-base short i-matra ('ि') to logical post-consonant order.
- Reorders visual post-base Repha ('र्') to logical pre-syllable order.
- Composes split vowel sequences ('अा' -> 'आ', 'अाे' -> 'ओ', 'अाै' -> 'औ', etc.).
"""

import argparse
import re
from pathlib import Path
import pypdf


PUA_MAP = {
    '\ua830': '।',
    '\ua831': '॥',
    '\uf306': '\uE001',  # Repha in <0042> (<F3060902>)
    '\uf30a': 'ू',
    # Pre-base short i-matra width variants -> temporary marker \uE000
    '\uf30d': '\uE000',
    '\uf30f': '\uE000',
    '\uf310': '\uE000',
    '\uf311': '\uE000',
    '\uf312': '\uE000',
    '\uf313': '\uE000',
    '\uf314': '\uE000',
    '\uf315': '\uE000',
    '\uf316': '\uE000',
    '\uf317': '\uE000',
    '\uf318': '\uE000',
    '\uf319': '\uE000',
    '\uf31b': '\uE000',
    '\uf31c': '\uE000',
    '\uf31d': '\uE000',
    '\uf31f': '\uE000',
    '\uf320': '\uE000',
    '\u093f': '\uE000',
    # Post-base long ii-matra width variants
    '\uf321': 'ी',
    '\uf322': 'ी',
    '\uf323': 'ी',
    '\uf324': 'ी',
    '\uf325': 'ी',
    '\uf326': 'ी',
    '\uf327': 'ी',
    '\uf328': 'ी',
    '\uf32a': 'ी',
    # Short u-matra variant
    '\uf753': 'ु',
    # Half-consonants
    '\uf337': 'ह्',
    '\uf33a': 'क्',
    '\uf33c': 'ग्',
    '\uf33d': 'घ्',
    '\uf33e': 'च्',
    '\uf33f': 'ज्',
    '\uf343': 'ञ्',
    '\uf344': 'त्',
    '\uf346': 'त्',
    '\uf348': 'ध्',
    '\uf34a': 'न्',
    '\uf34b': 'प्',
    '\uf34c': 'प्',
    '\uf34d': 'ञ्',
    '\uf34e': 'ल्',
    '\uf350': 'म्',
    '\uf356': 'श्',
    '\uf357': 'श्',
    '\uf35b': 'स्',
    '\uf35c': 'ह्',
    '\uf3c6': 'म',
    # Rakar (\uf73c + \uf3xx)
    '\uf73c': '',
    '\uf334': 'छ्र',
    '\uf363': 'क्र',
    '\uf364': 'ख्र',
    '\uf365': 'ग्र',
    '\uf366': 'घ्र',
    '\uf368': 'श्र',
    '\uf369': 'झ्र',
    '\uf36e': 'त्र',
    '\uf370': 'द्र',
    '\uf371': 'ध्र',
    '\uf373': 'न्र',
    '\uf374': 'प्र',
    '\uf375': 'फ्र',
    '\uf376': 'ब्र',
    '\uf377': 'भ्र',
    '\uf379': 'म्र',
    '\uf37a': 'य्र',
    '\uf37c': 'व्र',
    '\uf37d': 'श्र',
    '\uf37f': 'स्र',
    '\uf380': 'ह्र',
    '\uf388': 'गृ',
    '\uf391': 'त्र्',
    '\uf396': 'श्र\u093f',
    '\uf39e': 'ह्र',
    # Special ligatures and sub-forms
    '\uf3a8': 'ग्न',
    '\uf3b4': 'ध्न',
    '\uf3b6': 'ध्र्',
    '\uf3c4': 'म्भ',
    '\uf3e4': 'न्द',
    '\uf469': 'द्ध',
    '\uf480': 'द्भ',
    '\uf48c': 'द्म',
    '\uf493': 'द्म',
    '\uf4d4': 'ल्ल',
    '\uf4e7': 'ष्ट',
    '\uf4f8': 'ह्न',
    '\uf504': 'ह्व',
    '\uf570': '्व',
    '\uf575': '्य',
    '\uf584': '्य',
    '\uf585': '्य',
    '\uf58f': '्य',
    '\uf5a6\uf657': 'द्द',
    '\uf5ab\uf6d8': 'क्ष्व',
    '\uf5ba': 'क',
    '\uf5c5': 'क',
    '\uf5e6': 'ख',
    '\uf5eb': 'ग',
    '\uf5f7': 'घ',
    '\uf5fd': 'ङ',
    '\uf633': 'ढ',
    '\uf669': 'न',
    '\uf693': 'र',
    '\uf69b': 'व',
    '\uf6ba': 'स',
    '\uf6fc': 'ख्',
    '\ue341': 'त्',
    '\ue345': 'न्',
    '\ue34a': 'म्',
    '\ue352': 'स्',
}

# Complete Devanagari syllable with a vowel (independent vowel or consonant cluster + vowel; not a bare halanta coda)
DEV_FULL_SYLLABLE = (
    r"(?:[\u0904-\u0914][\u0901-\u0903]?|"
    r"(?:[\u0915-\u0939]\u093C?\u094D)*[\u0915-\u0939]\u093C?[\u093E-\u094C\u0962\u0963]?[\u0901-\u0903]?(?!\u094D))"
)

# Pattern 1 (Generic): Swara numeral + Caret (U+1CD0) + Syllable with NO swara numeral -> Move caret over that syllable
PAT1_CARET_RE = re.compile(
    r"([\uA8E0-\uA8F1])\u1CD0[ \t]*("
    + DEV_FULL_SYLLABLE
    + r")(?![\u093E-\u094C\u0962\u0963\u0901-\u0903\u094D\uA8E0-\uA8F1])"
)


def decode_siddhanta_text(raw_text: str) -> str:
    """Convert raw Siddhanta PDF extracted text to canonical logical-order Unicode Devanagari."""
    # 1. Mark raw post-base Rephas (\u0930\u094d) with \uE001 before expanding PUA half-forms
    text = raw_text.replace('\u0930\u094d', '\uE001')

    # 2. Remove bogus spaces before combining Vedic marks and Repha markers
    text = re.sub(r'[ \t]+([\u1CD0-\u1CFF\uA8E0-\uA8FF\uE001])', r'\1', text)

    # 3. Apply PUA character mappings
    for k, v in PUA_MAP.items():
        text = text.replace(k, v)

    # 4. Compose split vowels
    text = (
        text.replace('अाै', 'औ')
        .replace('अाे', 'ओ')
        .replace('अा', 'आ')
        .replace('एे', 'ऐ')
        .replace('ाै', 'ौ')
        .replace('ाे', 'ो')
    )

    # 5. Deduplicate accidental double-repha on the same consonant cluster (e.g. page 41 गीर्भिः)
    text = re.sub(
        r'\uE001((?:[\u0915-\u0939]\u094d)*[\u0915-\u0939][\u093e-\u094c\u0962\u0963\u1CD0-\u1CFF\uA8E0-\uA8FF]*)\uE001',
        '\\1\uE001',
        text,
    )

    # 6. Move visual pre-base short i-matra (\uE000) to logical post-consonant position
    text = re.sub(
        r'\uE000((?:[\u0915-\u0939]\u094d)*[\u0915-\u0939])',
        '\\1\u093f',
        text,
    )
    text = text.replace('\uE000', '\u093f')

    # 7. Move visual post-base Repha (\uE001) to logical pre-syllable position
    text = re.sub(
        r'((?:(?:[\u0915-\u0939]\u094d)*[\u0915-\u0939]|[\u0905-\u0914\u0960\u0961])[\u093e-\u094c\u0962\u0963\u1CD0-\u1CFF\uA8E0-\uA8FF]*)\uE001[ \t]*',
        '\u0930\u094d\\1',
        text,
    )
    text = text.replace('\uE001', '\u0930\u094d')

    # 8. Ensure standalone sthitam chant marker 'स्थि' is parenthesized as '(स्थि)'
    text = re.sub(
        r'(?<!\()(?<![\u0900-\u097F\uA8E0-\uA8FF\u1CD0-\u1CFF])स्थि(?![\u0900-\u0963\uA8E0-\uA8FF\u1CD0-\u1CFF])(?!\))',
        '(स्थि)',
        text,
    )

    # 9. Normalize any double Prenkha mark across avagraha+numeral ('ऽ᳒२᳒' -> 'ऽ२᳒')
    text = text.replace('ऽ\u1cd2२\u1cd2', 'ऽ२\u1cd2')

    # 10. Normalize Caret (U+1CD0) order: Caret over avagraha before following chant syllables/swaras ('᳐ऽ' -> 'ऽ᳐')
    text = re.sub(r'\u1cd0[ \t]*ऽ', 'ऽ\u1cd0', text)

    # 11. Pattern 1 (Generic): Move caret to next syllable without space when preceding swara carries caret and next syllable has NO swara numeral (e.g. 'रौ꣢᳐वा' -> 'रौ꣢वा᳐')
    text = PAT1_CARET_RE.sub(r'\g<1>\g<2>' + '\u1cd0', text)

    return text


def extract_pages_unicode(pdf_path: Path):
    """
    Extract clean Unicode lines per page from g1_extr.pdf, preserving Vedic Tone Prenkha (U+1CD2).
    Returns a list of dicts: [{'page': 1, 'lines': [...]}, ...]
    """
    reader = pypdf.PdfReader(str(pdf_path))
    pages_data = []

    prenkha_pattern = re.compile(
        r'ET\s+q\s+\.(?:5738|4782)\s+w\s+[\d.-]+\s+[\d.-]+\s+m\s+[\d.-]+\s+[\d.-]+\s+l\s+S\s+Q\s+'
        r'BT\s+/F1\s+[\d.]+\s+Tf\s+[\d.-]+\s+[\d.-]+\s+Td\[<002b0011'
    )

    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        # Inject <051b> (U+1CD2 VEDIC TONE PRENKHA '᳒') onto <002b0011> ('ऽ२') wherever
        # the PDF content stream draws the horizontal Prenkha overline stroke.
        if '/Contents' in page:
            contents_obj = page['/Contents'].get_object()
            stream_objs = contents_obj if isinstance(contents_obj, list) else [contents_obj]
            for s_ref in stream_objs:
                s_obj = s_ref.get_object()
                data = s_obj.get_data().decode('latin1')
                data_mod = prenkha_pattern.sub('0 0 Td[<002b0011051b', data)
                if data_mod != data:
                    s_obj.set_data(data_mod.encode('latin1'))

        raw_page_text = page.extract_text() or ''
        decoded_page_text = decode_siddhanta_text(raw_page_text)

        cleaned_lines = []
        raw_lines = [ln.strip() for ln in decoded_page_text.splitlines() if ln.strip()]
        for ln_idx, ln in enumerate(raw_lines):
            # Strip PDF watermark ('ॐ', 'ppn') at top of page
            if ln_idx < 3 and ln in ('ॐ', 'ppn', 'ॐ ppn'):
                continue
            # Strip standalone page number at bottom of page
            if ln_idx == len(raw_lines) - 1 and re.match(r'^[०-९\d]+$', ln):
                continue
            cleaned_lines.append(ln)

        pages_data.append({
            'page': page_num,
            'lines': cleaned_lines,
        })

    return pages_data


def main():
    parser = argparse.ArgumentParser(description='Extract Unicode Devanagari text from g1_extr.pdf')
    parser.add_argument(
        '--input', '-i',
        default='pdfconverter/data/input/g1_extr.pdf',
        help='Path to input PDF file',
    )
    parser.add_argument(
        '--output', '-o',
        default='pdfconverter/data/output/g1_extr_unicode.txt',
        help='Path to output Unicode text file',
    )
    args = parser.parse_args()

    pdf_path = Path(args.input)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pages_data = extract_pages_unicode(pdf_path)

    out_lines = []
    for p in pages_data:
        out_lines.append(f"--- Page {p['page']} ---")
        out_lines.extend(p['lines'])
        out_lines.append("")

    out_path.write_text('\n'.join(out_lines), encoding='utf-8')
    print(f"[OK] Extracted {len(pages_data)} pages to {out_path}")


if __name__ == '__main__':
    main()
