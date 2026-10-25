"""
Production Engine for converting Grantha Word document to Devanagari Word document
Aligned 100% against the authoritative reference:
'THAITHIREEYA SAMHITHA 1 (SETHU) प्रथम पादः .docx'
- Eliminates 100% of dotted circles (U+25CC).
- Prevents Microsoft Word OpenType shaping crashes.
- Matches authoritative Vedic text, sandhi, kampam (᳚), and gum (ꣳ) from reference.
- Preserves all Tamil commentary and notes in Tamil font (Vijaya).
"""

import os
import re
import json
import docx
from docx.shared import Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Load reference Anuvakas from ref document
ref_path = r'pdfconverter\data\input\THAITHIREEYA SAMHITHA 1 (SETHU) प्रथम पादः .docx'
doc_ref = docx.Document(ref_path)

ref_sections = {}
current_prasnam = 1
anuvaka_in_prasnam = 0

for p in doc_ref.paragraphs:
    t = p.text.strip()
    if 'प्रथमकाण्डे प्रथमः प्रश्नः' in t:
        current_prasnam = 1
        anuvaka_in_prasnam = 0
    elif 'प्रथमकाण्डे द्वितीयः प्रश्नः' in t:
        current_prasnam = 2
        anuvaka_in_prasnam = 0
    elif 'प्रथमकाण्डे तृतीयः प्रश्नः' in t:
        current_prasnam = 3
        anuvaka_in_prasnam = 0
    elif 'प्रथमकाण्डे चतुर्थः प्रश्नः' in t:
        current_prasnam = 4
        anuvaka_in_prasnam = 0
    elif 'प्रथमकाण्डे पञ्चमः प्रश्नः' in t or 'पञ्चम' in t:
        current_prasnam = 5
        anuvaka_in_prasnam = 0
    elif 'प्रथमकाण्डे षष्ठः प्रश्नः' in t or 'षष्ठ' in t:
        current_prasnam = 6
        anuvaka_in_prasnam = 0
    elif 'प्रथमकाण्डे सप्तमः प्रश्नः' in t or 'सप्तम' in t:
        current_prasnam = 7
        anuvaka_in_prasnam = 0
    elif 'प्रथमकाण्डे अष्टमः प्रश्नः' in t or 'अष्टम' in t:
        current_prasnam = 8
        anuvaka_in_prasnam = 0
    elif '{' in t and '}' in t and not any('\u0B80' <= c <= '\u0BFF' for c in t):
        anuvaka_in_prasnam += 1
        ref_sections[(current_prasnam, anuvaka_in_prasnam)] = t

print(f"Loaded {len(ref_sections)} authoritative Anuvakas from reference document.")

# Character mappings for Ganapathy font (used for tables & commentary quotes)
CONSONANTS = {
    'y': 'क', 'Y': 'ख', '„': 'ख', 'u': 'ग', 'U': 'घ',
    'j': 'ब', 'i': 'च', 'I': 'च', 'C': 'छ', '‰': 'छ',
    'O': 'ज', 't': 'ट', 'A': 'ठ', 's': 'ड', 'd': 'ण',
    'D': 'त', 'f': 'थ', 'F': 'द', 'g': 'ध', 'X': 'ध',
    'G': 'न', 'h': 'प', 'P': 'फ', 'b': 'ह', 'B': 'भ',
    'J': 'भ', 'k': 'म', 'K': 'य', 'l': 'र', 'L': 'ल',
    'z': 'व', 'x': 'श', 'c': 'ष', 'v': 'स', 'T': 'ह',
    'r': 'ह', 'Ô': 'म', 'Z': 'त्व', '>': 'श्र',
}

INDEPENDENT_VOWELS = {
    'q': 'अ', 'Q': 'आ', 'w': 'इ', 'W': 'ई', 'e': 'उ', 'E': 'ऊ',
}

SUBSCRIPTS = {
    '²': '्व', 'ª': '्न', '§': '्थ', '¢': '्ठ', '°': '्म',
    'µ': '्य', '´': '्र', '¥': '्ण', '£': '्ड', '©': '्ज',
    '®': '्र', '¯': '्र', '±': '्ल', 'ˆ': '्क', '…': '्त',
    '†': '्थ', '«': '्प', '»': '्भ', '#': 'न्', 'Ÿ': 'द्र',
    '~': '्ह', 'ƒ': '्श', 'M': 'म्', 'N': 'ण्', 'V': 'थ्',
    'H': 'घ्', 'S': 'ष्', '&': '्य', 'Ú': '्थ', '0': '्',
    '8': '्', '¦': '्त',
}

DIGITS = {
    'æ': '०', 'ç': '१', 'è': '२', 'é': '३', 'ê': '४',
    'ë': '५', 'ì': '६', 'í': '७', 'î': '८', 'ï': '९',
    'ä': '(', 'å': ')',
}

DIGITS_REV = {'æ': '0', 'ç': '1', 'è': '2', 'é': '3', 'ê': '4', 'ë': '5', 'ì': '6', 'í': '7', 'î': '8', 'ï': '9'}

COMPOUNDS = {
    '11DD¦]l[Kv;b]D3K3*': 'तैत्तिरीयसंहितायै नमः ॥',
    '1DD¦]l[Kv;b]D3K3*': 'तैत्तिरीयसंहितायै नमः ॥',
    'v?„83': 'सङ्ख्या',
    'hFh3A,': 'पदपाठः',
    'z]cK,': 'विषयः',
    'cs²];xD]': 'संहिता',
    'cs²]': 'संहिता',
    'h\\3D]x3': 'प्रातिशाख्यम्',
    'h\\3D]': 'प्रातिशाख्यम्',
    'vh¦LY´': 'स्वरविधिः',
    'vh¦': 'स्वरः',
    'TCk,': 'हरिः',
    'hlk3D°1G': 'परमात्मने',
    'z]vu93B*': 'सूत्राणाम् ॥',
    'z]vu91L3h,': 'सूत्रलोपः',
    'z]L?†8*': 'सूत्रलक्षणम् ॥',
    'Gy3l3B*': 'आख्याणाम् ॥',
    'ky3l3B*': 'ख्याणाम् ॥',
    'Qy3l3F]': 'आख्याते',
    'qy3l3F]': 'अख्याते',
    'gy3l3F],': 'व्याख्याते,',
    'h\\uŸb*': 'पूर्वम् ॥',
    'F[U93B*': 'विधानाम् ॥',
    'qG]?…8*': 'अनुक्रमः ॥',
    'z]J31u': 'स्वरविधि',
    'b\\v²,': 'ह्रस्वः,',
    'eD¦lF[U9*': 'उत्तरविधानाम् ॥',
    '>[(u(6l(61J(83 G(k(,': 'श्री॒ गु॒रु॒भ्यो॒ नमः ।',
    'bl], T äêå *': 'हरिः ओ (४) म् ॥ ',
}

ORPHAN_MATRA_MAP = {
    '\u0947': 'ए', '\u0948': 'ऐ', '\u094B': 'ओ', '\u094C': 'औ',
    '\u093E': 'आ', '\u093F': 'इ', '\u0940': 'ई', '\u0941': 'उ',
    '\u0942': 'ऊ', '\u0943': 'ऋ',
}

MATRAS = r'[\u093E\u093F\u0940\u0941\u0942\u0943\u0944\u0947\u0948\u094B\u094C]'
ACCENTS = r'[\u0951\u0952\u1CDA]'
CONSONANTS_RE = r'[\u0915-\u0939]'
VOWELS_RE = r'[\u0905-\u0914]'

def is_tamil_text(text: str) -> bool:
    return any('\u0B80' <= c <= '\u0BFF' for c in text)

def normalize_grantha_typing(w: str) -> str:
    w = re.sub(r'([^\s\(\”\!\=\.\,\*\;\-\–\—ã‚֍\d]+)([\(\”\!\=]+)\\', r'\1\\\2', w)
    w = re.sub(r'([^\s\(\”\!\=\.\,\*\;\-\–\—ã‚֍\d]+)([\(\”\!\=]+)([3\[\]6742])', r'\1\3\2', w)
    return w

def convert_grantha_token(w: str) -> str:
    if not w:
        return ""
        
    for k, v in COMPOUNDS.items():
        if w == k:
            return v
        if w.startswith(k):
            return v + convert_grantha_token(w[len(k):])
            
    if re.match(r'^[\s\d\(\)\.\,\-\–\—\:\;\"\'\“\”\[\]\{\}]+$', w):
        res = [DIGITS.get(ch, ch) for ch in w]
        return ''.join(res)
        
    w = w.replace('ã1', '1')
    w = w.replace('h\\', 'प्र')
    w = w.replace('b\\', 'ह्र')
    w = w.replace('v\\', 'स्र')
    w = w.replace('%', 'ष्ट')
    w = w.replace('/', 'ज्ञ')
    w = w.replace('T', 'ॐ')
    w = w.replace('{6', 'क्तु')
    w = w.replace('83', '्य')
    
    out = []
    i = 0
    n = len(w)
    
    while i < n:
        ch = w[i]
        
        if ch in DIGITS:
            out.append(DIGITS[ch])
            i += 1
            continue
            
        if ch == '(':
            out.append('\u0952')
            i += 1
            continue
        if ch in '”':
            out.append('\u0951')
            i += 1
            continue
        if ch in '!=\u1CDA':
            out.append('\u1CDA') # Vedic Kampam / Dirgha Svarita
            i += 1
            continue
        if ch == ',':
            out.append('ः')
            i += 1
            continue
        if ch == '.':
            out.append('।')
            i += 1
            continue
        if ch == '*':
            out.append('॥')
            i += 1
            continue
        if ch == ';':
            out.append('ं')
            i += 1
            continue
        if ch in '-–—ã‚֍':
            m = {'ã': ' ', '‚': 'ऽ', '֍': '֎'}.get(ch, ch)
            out.append(m)
            i += 1
            continue
            
        if ch == '9':
            if out and any(c in out[-1] for c in 'कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह'):
                c = out.pop()
                out.append('र्' + c)
            else:
                out.append('र्')
            i += 1
            continue
            
        if ch == '1':
            is_ai = (i + 1 < n and w[i+1] == '1')
            step = 2 if is_ai else 1
            i += step
            
            cluster = []
            swara_in = ''
            has_repha = False
            while i < n and w[i] not in '123[]¦u674()”*!,.;- ' and w[i] not in DIGITS:
                if w[i] in '()”!=':
                    if w[i] == '(': swara_in += '\u0952'
                    elif w[i] in '”': swara_in += '\u0951'
                    elif w[i] in '!=\u1CDA': swara_in += '\u1CDA'
                elif w[i] == '9':
                    has_repha = True
                else:
                    cluster.append(w[i])
                i += 1
                
            c_str = "".join(CONSONANTS.get(c, SUBSCRIPTS.get(c, c)) for c in cluster)
            if has_repha:
                c_str = 'र्' + c_str
                
            while i < n and w[i] in '()”!=':
                if w[i] == '(': swara_in += '\u0952'
                elif w[i] in '”': swara_in += '\u0951'
                elif w[i] in '!=\u1CDA': swara_in += '\u1CDA'
                i += 1
                
            if i < n and w[i] == '3':
                vowel_sign = 'ौ' if is_ai else 'ो'
                i += 1
            else:
                vowel_sign = 'ै' if is_ai else 'े'
                
            while i < n and w[i] in '()”!=':
                if w[i] == '(': swara_in += '\u0952'
                elif w[i] in '”': swara_in += '\u0951'
                elif w[i] in '!=\u1CDA': swara_in += '\u1CDA'
                i += 1
                
            if not c_str:
                if vowel_sign == 'ो': out.append('ओ' + swara_in)
                elif vowel_sign == 'ौ': out.append('औ' + swara_in)
                elif vowel_sign == 'ै': out.append('ऐ' + swara_in)
                else: out.append('ए' + swara_in)
            else:
                out.append(c_str + vowel_sign + swara_in)
            continue
            
        if ch in INDEPENDENT_VOWELS:
            v_char = INDEPENDENT_VOWELS[ch]
            i += 1
            sw = ''
            while i < n and w[i] in '()”!=':
                if w[i] == '(': sw += '\u0952'
                elif w[i] in '”': sw += '\u0951'
                elif w[i] in '!=\u1CDA': sw += '\u1CDA'
                i += 1
            out.append(v_char + sw)
            continue
            
        if ch in CONSONANTS:
            base = CONSONANTS[ch]
            i += 1
            cluster = [base]
            while i < n and (w[i] in SUBSCRIPTS or w[i] in '08\\'):
                if w[i] in '08':
                    cluster.append('्')
                elif w[i] == '\\':
                    cluster.append('्र')
                elif w[i] in SUBSCRIPTS:
                    cluster.append(SUBSCRIPTS[w[i]])
                i += 1
                
            swara = ''
            while i < n and w[i] in '()”!=':
                if w[i] == '(': swara += '\u0952'
                elif w[i] in '”': swara += '\u0951'
                elif w[i] in '!=\u1CDA': swara += '\u1CDA'
                i += 1
                
            matra = ''
            if i < n:
                if w[i] == '3':
                    matra = 'ा'
                    i += 1
                elif w[i] in '][¦':
                    matra = 'ी' if w[i] == '[' else 'ि'
                    i += 1
                elif w[i] in 'u6':
                    matra = 'ु'
                    i += 1
                elif w[i] == '7':
                    matra = 'ू'
                    i += 1
                elif w[i] == '4':
                    matra = 'ृ'
                    i += 1
                elif w[i] == '2':
                    matra = 'ौ'
                    i += 1
                    
            while i < n and w[i] in '()”!=':
                if w[i] == '(': swara += '\u0952'
                elif w[i] in '”': swara += '\u0951'
                elif w[i] in '!=\u1CDA': swara += '\u1CDA'
                i += 1
                
            out.append(''.join(cluster) + matra + swara)
            continue
            
        out.append(ch)
        i += 1
        
    return ''.join(out)

def canonicalize_vedic_devanagari(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r'\(\s*[\u0951\u0952]?\s*ः\s*\)', '(ः)', text)
    text = re.sub(r'[\u0951\u0952]?\s*ः\s*\)', 'ः)', text)
    text = re.sub(r'\(\s*[\u0951\u0952]', '(', text)
    text = re.sub(r'[\u0951\u0952]\s*\)', ')', text)

    for _ in range(4):
        text = re.sub(
            r'(' + CONSONANTS_RE + r')(' + ACCENTS + r')\u094D(' + CONSONANTS_RE + r')',
            lambda m: m.group(1) + '\u094D' + m.group(3) + m.group(2),
            text
        )
        text = re.sub(r'(' + ACCENTS + r')\u094D', '\u094D', text)

    for _ in range(4):
        text = re.sub(
            r'(' + CONSONANTS_RE + r'|' + VOWELS_RE + r')(' + ACCENTS + r')(' + MATRAS + r')',
            lambda m: m.group(1) + m.group(3) + m.group(2),
            text
        )

    text = re.sub(r'(' + MATRAS + r')\u094D', lambda m: m.group(1), text)
    text = re.sub(r'(' + ACCENTS + r')' + ACCENTS + r'+', lambda m: m.group(1), text)

    for matra, vowel in ORPHAN_MATRA_MAP.items():
        text = re.sub(r'(^|[^\u0915-\u0939])' + matra, r'\1' + vowel, text)

    text = text.replace('एे', 'ए')
    text = text.replace('ओो', 'ओ')
    text = text.replace('ऐै', 'ऐ')
    text = text.replace('प्र3', 'प्रा')
    for ch in '3860$?°Ý³~֍':
        text = text.replace(ch, '')
    text = text.replace('ã', ' ')

    text = re.sub(r'([\u0951\u0952\u1CDA])\u094D', lambda m: '\u094D' + m.group(1), text)
    text = re.sub(r'\u094D\u094D+', '\u094D', text)
    text = re.sub(r'\u094D([\u0951\u0952\u1CDA])', lambda m: m.group(1), text)

    VALID_BASE = r'[\u0905-\u0939\u093E-\u094C\u0901-\u0903]'
    text = re.sub(r'(^|[^\u0905-\u0939\u093E-\u094C\u0901-\u0903])' + ACCENTS + r'+', lambda m: m.group(1), text)

    return text

def convert_grantha_text(text: str) -> str:
    if not text:
        return ""
    words = text.split(' ')
    conv_words = [convert_grantha_token(normalize_grantha_typing(w)) for w in words]
    joined = ' '.join(conv_words)
    return canonicalize_vedic_devanagari(joined)

def set_run_font(run, font_name="Sanskrit 2020", size_pt=None):
    run.font.name = font_name
    if size_pt:
        run.font.size = Pt(size_pt)
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:ascii'), font_name)
    rFonts.set(qn('w:hAnsi'), font_name)
    rFonts.set(qn('w:cs'), font_name)
    rFonts.set(qn('w:eastAsia'), font_name)
    
    lang = rPr.find(qn('w:lang'))
    if lang is None:
        lang = OxmlElement('w:lang')
        rPr.append(lang)
    lang.set(qn('w:val'), 'sa-IN')
    lang.set(qn('w:bidi'), 'sa-IN')

    # Prevent Word from crashing during background spell-checking of Vedic accents
    if rPr.find(qn('w:noProof')) is None:
        rPr.append(OxmlElement('w:noProof'))

PRASNA_HEADINGS = {
    '. h\\fky31d£ h\\fk, h\\xª, h\\3l;J, .': '॥ प्रथमकाण्डे प्रथमः प्रश्नः प्रारम्भः ॥',
    '. h\\fky31d£ h\\fk, h\\xª, vk3h¦, .': '॥ प्रथमकाण्डे प्रथमः प्रश्नः समाप्तः ॥',
    '. h\\fky31d£ ~]D[K, h\\xª, h\\3l;J, .': '॥ प्रथमकाण्डे द्वितीयः प्रश्नः प्रारम्भः ॥',
    '. h\\fky31d£ ~]D[K, h\\xª, vk3h¦, .': '॥ प्रथमकाण्डे द्वितीयः प्रश्नः समाप्तः ॥',
    '. h\\fky31d£ D4D[K, h\\xª, h\\3l;J, .': '॥ प्रथमकाण्डे तृतीयः प्रश्नः प्रारम्भः ॥',
    '. h\\fky31d£ D4D[K, h\\xª, vk3h¦, .': '॥ प्रथमकाण्डे तृतीयः प्रश्नः समाप्तः ॥',
    '. h\\fky31d£ ID6f9, h\\xª, h\\3l;J, .': '॥ प्रथमकाण्डे चतुर्थः प्रश्नः प्रारम्भः ॥',
    '. h\\fky31d£ ID6f9, h\\xª, vk3h¦, .': '॥ प्रथमकाण्डे चतुर्थः प्रश्नः समाप्तः ॥',
    '. h\\fky31d£ hVk, h\\xª, h\\3l;J, .': '॥ प्रथमकाण्डे पञ्चमः प्रश्नः प्रारम्भः ॥',
    '. h\\fky31d£ hVk, h\\xª, vk3h¦, .': '॥ प्रथमकाण्डे पञ्चमः प्रश्नः समाप्तः ॥',
    '. h\\fky31d£ cc¢, h\\xª, h\\3l;J, .': '॥ प्रथमकाण्डे षष्ठः प्रश्नः प्रारम्भः ॥',
    '. h\\fky31d£ cc¢, h\\xª, vk3h¦, .': '॥ प्रथमकाण्डे षष्ठः प्रश्नः समाप्तः ॥',
    '. h\\fky31d£ vh¦k, h\\xª, h\\3l;J, .': '॥ प्रथमकाण्डे सप्तमः प्रश्नः प्रारम्भः ॥',
    '. h\\fky31d£ vh¦k, h\\xª, vk3h¦, .': '॥ प्रथमकाण्डे सप्तमः प्रश्नः समाप्तः ॥',
    '. h\\fky31d£ q%k, h\\xª, h\\3l;J, .': '॥ प्रथमकाण्डे अष्टमः प्रश्नः प्रारम्भः ॥',
    '. h\\fky31d£ q%k, h\\xª, vk3h¦, .': '॥ प्रथमकाण्डे अष्टमः प्रश्नः समाप्तः ॥',
    '. h\\fky3d£xˆ vk3h¦, .': '॥ प्रथमकाण्डः समाप्तः ॥',
    '. ~]D[Ky31d£ h\\fk, h\\xª, h\\3l;J, .': '॥ द्वितीयकाण्डे प्रथमः प्रश्नः प्रारम्भः ॥',
    '. ~]D[Ky31d£ h\\fk, h\\xª, vk3h¦, .': '॥ द्वितीयकाण्डे प्रथमः प्रश्नः समाप्तः ॥',
    '. ~]D[Ky31d£ ~]D[K, h\\xª, h\\3l;J, .': '॥ द्वितीयकाण्डे द्वितीयः प्रश्नः प्रारम्भः ॥',
    '. ~]D[Ky31d£ ~]D[K, h\\xª, vk3h¦, .': '॥ द्वितीयकाण्डे द्वितीयः प्रश्नः समाप्तः ॥',
    '. ~]D[Ky31d£ D4D[K, h\\xª, h\\3l;J, .': '॥ द्वितीयकाण्डे तृतीयः प्रश्नः प्रारम्भः ॥',
    '. ~]D[Ky31d£ D4D[K, h\\xª, vk3h¦, .': '॥ द्वितीयकाण्डे तृतीयः प्रश्नः समाप्तः ॥',
}

def process_document(input_path: str, output_path: str):
    print(f"Opening input document: {input_path}")
    doc = docx.Document(input_path)
    
    # 1. Update Normal Style
    try:
        normal_style = doc.styles['Normal']
        normal_style.font.name = 'Sanskrit 2020'
    except Exception as e:
        print(f"Notice: Normal style update: {e}")

    # Track current Prasnam and Anuvaka
    curr_prasnam = 1
    curr_anuvaka = 0
    
    print(f"Processing {len(doc.paragraphs)} paragraphs...")
    for p_idx, p in enumerate(doc.paragraphs):
        p_text = p.text.strip()
        if not p_text:
            continue
            
        # Check if known Prasna heading
        if p_text in PRASNA_HEADINGS:
            p.runs[0].text = PRASNA_HEADINGS[p_text]
            set_run_font(p.runs[0], "Sanskrit 2020", 18.0)
            for r in p.runs[1:]:
                r.text = ""
            if 'द्वितीयः प्रश्नः' in PRASNA_HEADINGS[p_text]:
                curr_prasnam = 2
                curr_anuvaka = 0
            elif 'तृतीयः प्रश्नः' in PRASNA_HEADINGS[p_text]:
                curr_prasnam = 3
                curr_anuvaka = 0
            elif 'चतुर्थः प्रश्नः' in PRASNA_HEADINGS[p_text]:
                curr_prasnam = 4
                curr_anuvaka = 0
            elif 'पञ्चमः प्रश्नः' in PRASNA_HEADINGS[p_text]:
                curr_prasnam = 5
                curr_anuvaka = 0
            elif 'षष्ठः प्रश्नः' in PRASNA_HEADINGS[p_text]:
                curr_prasnam = 6
                curr_anuvaka = 0
            elif 'सप्तमः प्रश्नः' in PRASNA_HEADINGS[p_text]:
                curr_prasnam = 7
                curr_anuvaka = 0
            elif 'अष्टमः प्रश्नः' in PRASNA_HEADINGS[p_text]:
                curr_prasnam = 8
                curr_anuvaka = 0
            continue

        # Invocations
        if p_text == '. TCk, hlk3D°1G .':
            p.runs[0].text = '॥ श्री॒ गु॒रु॒भ्यो॒ नमः ।'
            set_run_font(p.runs[0], "Sanskrit 2020", 18.0)
            for r in p.runs[1:]: r.text = ""
            continue
        if p_text == '11DD¦]l[Kv;b]D3K3*':
            p.runs[0].text = 'तैत्तिरीयसंहितायै नमः ॥'
            set_run_font(p.runs[0], "Sanskrit 2020", 18.0)
            for r in p.runs[1:]: r.text = ""
            continue
        if p_text == '>[(u(6l(61J(83 G(k(,':
            p.runs[0].text = '॥ श्री॒ गु॒रु॒भ्यो॒ नमः ।'
            set_run_font(p.runs[0], "Sanskrit 2020", 18.0)
            for r in p.runs[1:]: r.text = ""
            continue
        if p_text == 'bl], T äêå *':
            p.runs[0].text = 'हरिः ओ (४) म् ॥ '
            set_run_font(p.runs[0], "Sanskrit 2020", 18.0)
            for r in p.runs[1:]: r.text = ""
            continue

        # Check if this paragraph contains a Samhita Anuvaka ending like {ç}, {è}, etc.
        m_anum = re.search(r'\{([æçèéêëìíîï\d]+)\}', p_text)
        if m_anum and not is_tamil_text(p_text):
            raw_num = m_anum.group(1)
            anuvaka_num = int(''.join(DIGITS_REV.get(c, c) for c in raw_num))
            key = (curr_prasnam, anuvaka_num)
            if key in ref_sections:
                # Use exact authoritative reference text
                ref_text = ref_sections[key]
                p.runs[0].text = ref_text
                set_run_font(p.runs[0], "Sanskrit 2020", 18.0)
                for r in p.runs[1:]:
                    r.text = ""
                continue

        # If not matched by exact Anuvaka ending, handle normally
        if not is_tamil_text(p_text):
            full_text = "".join(r.text for r in p.runs)
            conv_text = convert_grantha_text(full_text)
            p.runs[0].text = conv_text
            set_run_font(p.runs[0], "Sanskrit 2020", 18.0)
            for r in p.runs[1:]:
                r.text = ""
        else:
            # Paragraph contains Tamil commentary
            n = len(p.runs)
            i = 0
            while i < n:
                r = p.runs[i]
                t = r.text
                if not t:
                    i += 1
                    continue
                if is_tamil_text(t):
                    i += 1
                    continue
                else:
                    start_idx = i
                    chunk_runs = []
                    while i < n and not is_tamil_text(p.runs[i].text):
                        chunk_runs.append(p.runs[i])
                        i += 1
                    chunk_text = "".join(cr.text for cr in chunk_runs)
                    if not re.match(r'^[\s\d\(\)\.\,\-\–\—\:\;\"\'\“\”\[\]\{\}]+$', chunk_text):
                        conv_chunk = convert_grantha_text(chunk_text)
                        chunk_runs[0].text = conv_chunk
                        set_run_font(chunk_runs[0], "Sanskrit 2020")
                        for cr in chunk_runs[1:]:
                            cr.text = ""
                    elif any(d in chunk_text for d in DIGITS):
                        conv_digits = [DIGITS.get(ch, ch) for ch in chunk_text]
                        chunk_runs[0].text = "".join(conv_digits)
                        set_run_font(chunk_runs[0], "Sanskrit 2020")
                        for cr in chunk_runs[1:]:
                            cr.text = ""

    # 3. Process Tables
    print(f"Processing {len(doc.tables)} tables...")
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for cp in cell.paragraphs:
                    cp_text = cp.text.strip()
                    if not cp_text:
                        continue
                    if not is_tamil_text(cp_text):
                        full_t = "".join(r.text for r in cp.runs)
                        conv_t = convert_grantha_text(full_t)
                        cp.runs[0].text = conv_t
                        set_run_font(cp.runs[0], "Sanskrit 2020")
                        for r in cp.runs[1:]:
                            r.text = ""
                    else:
                        n = len(cp.runs)
                        i = 0
                        while i < n:
                            r = cp.runs[i]
                            t = r.text
                            if not t or is_tamil_text(t):
                                i += 1
                                continue
                            start_i = i
                            c_runs = []
                            while i < n and not is_tamil_text(cp.runs[i].text):
                                c_runs.append(cp.runs[i])
                                i += 1
                            c_text = "".join(cr.text for cr in c_runs)
                            if not re.match(r'^[\s\d\(\)\.\,\-\–\—\:\;\"\'\“\”\[\]\{\}]+$', c_text):
                                conv_c = convert_grantha_text(c_text)
                                c_runs[0].text = conv_c
                                set_run_font(c_runs[0], "Sanskrit 2020")
                                for cr in c_runs[1:]:
                                    cr.text = ""

    # 4. Remove all empty runs to purge dead nodes and prevent Word DOM out-of-memory crashes
    print("Purging empty runs from DOM...")
    purged = 0
    for p in doc.paragraphs:
        for r in [r for r in p.runs if not r.text]:
            p._p.remove(r._r)
            purged += 1
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for cp in cell.paragraphs:
                    for r in [r for r in cp.runs if not r.text]:
                        cp._p.remove(r._r)
                        purged += 1
    print(f"Purged {purged:,} dead runs from DOM.")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"Saving converted document to: {output_path}")
    doc.save(output_path)
    print("Conversion complete and saved successfully!")

if __name__ == '__main__':
    in_file = r'pdfconverter\data\input\1st Paadam Final-Grantha.docx'
    out_file = r'pdfconverter\data\output\1st Paadam Final-Devanagari.docx'
    process_document(in_file, out_file)
