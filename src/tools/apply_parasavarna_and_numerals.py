#!/usr/bin/env python3
"""
Applies Parasavarna Sandhi, Inline Rigveda Numerals (टट्य -> ३, ठ -> १ with accents),
and typographical normalizations (ककुप -> ककुप्, )ः -> ः), etc.)
across the Jaiminiya Samaveda corpus.

NOTE: Anusvara before vowels (mo'nusvara in verses) is explicitly PRESERVED as anusvara (ं)
per user instruction ("If yes, revert").
"""

import re
from pathlib import Path

# Varga stop definitions
KAVARGA = 'कखगघ'
CAVARGA = 'चछजझ'
TAVARGA_RETRO = 'टठडढ'
TAVARGA_DENTAL = 'तथदध'
PAVARGA = 'पफबभ'

ANUDATTA_0952 = '\u0952'

def apply_parasavarna_segment(text: str) -> str:
    """
    Applies Paninian Parasavarna sandhi (8.4.58 / 8.4.59) to text:
    ं followed by optional Rik parenthetical swaras (1)-(4) or space + stop -> homorganic nasal.
    """
    # 1. Tavarga Dental -> न् (e.g. अग्निंदूतं -> अग्निन्दूतं, वामदेव्यंतृतीयम् -> वामदेव्यन्तृतीयम्)
    text = re.sub(r'ं(\([1-4]\))\s*([तथदध])', r'\1न्\2', text)
    text = re.sub(r'ं\s*([तथदध])', r'न्\1', text)

    # 2. Kavarga -> ङ् (e.g. वांगिरसौ -> वाङ्गिरसौ, आंगिरस -> आङ्गिरस)
    text = re.sub(r'ं(\([1-4]\))\s*([कखगघ])', r'\1ङ्\2', text)
    text = re.sub(r'ं\s*([कखगघ])', r'ङ्\1', text)

    # 3. Cavarga -> ञ् (e.g. किंच -> किञ्च, संचय -> सञ्चय)
    text = re.sub(r'ं(\([1-4]\))\s*([चछजझ])', r'\1ञ्\2', text)
    text = re.sub(r'ं\s*([चछजझ])', r'ञ्\1', text)

    # 4. Ṭavarga (Retroflex) -> ण् (e.g. खंड -> खण्ड)
    text = re.sub(r'ं(\([1-4]\))\s*([टठडढ])', r'\1ण्\2', text)
    text = re.sub(r'ं\s*([टठडढ])', r'ण्\1', text)

    # 5. Pavarga -> म् (e.g. यंभम् -> यम्भम्, संपूर्ण -> सम्पूर्ण)
    text = re.sub(r'ं(\([1-4]\))\s*([पफबभ])', r'\1म्\2', text)
    text = re.sub(r'ं\s*([पफबभ])', r'म्\1', text)

    return text

def normalize_rik_numerals(text: str) -> str:
    """
    Normalizes Grantha encodings in Rik text:
    - टट्य with optional accent -> ३ with retained accent
    - ठ(1) -> १ with Anudatta mark (U+0952, horizontal accent mark over १)
    - standalone ठ -> १
    - Protects genuine Sanskrit ष्ठ and जठरे words.
    """
    # 1. टट्य with optional accent -> ३
    text = re.sub(r'टट्य(\([1-4]\))?', r'३\1', text)
    text = re.sub(r'३ट्य', '३', text)

    # 2. ठ(1) -> १ with Anudatta (U+0952)
    def repl_tha_1(m):
        prefix = m.group(1)
        if prefix in ['ष्', 'ष', 'ज', 'क', 'पा']:
            return m.group(0)
        return prefix + '१' + ANUDATTA_0952

    text = re.sub(r'([^ष्षजपा\s])ठ\(1\)', repl_tha_1, text)
    text = re.sub(r'(\s+)ठ\(1\)', lambda m: m.group(1) + '१' + ANUDATTA_0952, text)
    text = re.sub(r'^ठ\(1\)', '१' + ANUDATTA_0952, text)

    # Also handle 'ठे(1)' in 'वृ(2)षाह्यु ठे(1) ग्रश्रृण्व' -> 'वृ(2)षाह्यु १॒ ग्रश्रृण्व'
    text = re.sub(r'(\s+)ठे\(1\)', lambda m: m.group(1) + '१' + ANUDATTA_0952, text)

    # Standalone ठ without (1): e.g. " पौं ठ स्यम्" -> " पौं १ स्यम्"
    def repl_tha_bare(m):
        prefix = m.group(1)
        suffix = m.group(2)
        if prefix in ['ष्', 'ष', 'ज', 'क', 'पा']:
            return m.group(0)
        return prefix + '१' + suffix

    text = re.sub(r'(\s+)ठ(\s+)', r'\1१\2', text)
    text = re.sub(r'([^ष्षजपा\s])ठ(\s+)', repl_tha_bare, text)

    return text

def normalize_metadata_and_typos(line: str) -> str:
    """
    Normalizes metadata and common typos:
    1. 'ककुप' without halant (not followed by virama ्) -> 'ककुप्'
    2. Visarga with parenthesis: 'ः)ः' -> 'ः)', '[^ः])ः' -> 'ः)'
    3. Apadanta parasavarna in metadata (वांगिरसौ -> वाङ्गिरसौ)
    4. Visarga of ah before t/th -> st (द्वयोः तोद -> द्वयोस्तोद, आम्बरीषः त्रित -> आम्बरीषस्त्रित)
    """
    line = re.sub(r'ककुप(?!्)\b', 'ककुप्', line)
    line = re.sub(r'ः\s*\)ः', 'ः)', line)
    line = re.sub(r'([^\sः])\)ः', r'\1ः)', line)
    line = re.sub(r'ः\s+([तथ])', r'स्\1', line)

    line = line.replace('वांगिरसौ', 'वाङ्गिरसौ')
    line = line.replace('आंगिरस', 'आङ्गिरस')
    line = line.replace('सप्त्तगुरांगिरस', 'सप्तगुराङ्गिरस')
    line = line.replace('सप्त्त', 'सप्त')

    return line

def process_corpus_file(file_path: Path) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.splitlines(keepends=True)
    out_lines = []

    stats = {
        'tatya_to_3': 0,
        'tha_to_1': 0,
        'parasavarna_applied': 0,
        'reverted_anusvara_before_vowel': 0
    }

    in_rik_text = False
    in_metadata = False
    in_header = False

    for line in lines:
        if '# Start of Rik Text' in line:
            in_rik_text = True
        elif '# End of Rik Text' in line:
            in_rik_text = False

        if '# Start of Rik Metadata' in line or '# Start of Saman Metadata' in line:
            in_metadata = True
        elif '# End of Rik Metadata' in line or '# End of Saman Metadata' in line:
            in_metadata = False

        if '# Start of SubSection Title' in line:
            in_header = True
        elif '# End of SubSection Title' in line:
            in_header = False

        if in_rik_text:
            if 'टट्य' in line or '३ट्य' in line:
                stats['tatya_to_3'] += len(re.findall(r'टट्य|३ट्य', line))
            if re.search(r'[^ष्षजपा\s]ठ\(1\)|(\s+)ठ\(1\)|(\s+)ठ(\s+)', line):
                stats['tha_to_1'] += 1

            line = normalize_rik_numerals(line)

            before_sandhi = line
            line = apply_parasavarna_segment(line)
            if line != before_sandhi:
                stats['parasavarna_applied'] += 1

            # REVERT: ensure Anusvara before vowels is preserved as Anusvara (ं), NOT changed to म्
            # Revert any previously substituted म् [vowel] back to ं [vowel]
            # E.g. माहम् आसि -> माहं आसि, बल्बधानम् आराम्णः -> बल्बधानं आराम्णः, र्वम् आसू -> र्वंआसू
            def revert_m_vowel(m):
                stats['reverted_anusvara_before_vowel'] += 1
                prefix = m.group(1) # word before म्
                space = m.group(2)
                vowel = m.group(3)
                return f"{prefix}ं{space}{vowel}"

            # Only revert when it replaced anusvara in words ending in vowel+m before vowel
            line = re.sub(r'([अ-ह][ािीुूृेैोौ]?)म्(\s*)([अआइईउऊऋएऐओऔ])', revert_m_vowel, line)

        elif in_metadata:
            line = normalize_metadata_and_typos(line)
            line = apply_parasavarna_segment(line)

        elif in_header or line.strip().startswith('॥'):
            line = normalize_metadata_and_typos(line)
            line = apply_parasavarna_segment(line)

        out_lines.append(line)

    new_content = "".join(out_lines)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return stats

if __name__ == '__main__':
    target = Path('data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt')
    stats = process_corpus_file(target)
    print("Corpus transformation completed successfully:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
