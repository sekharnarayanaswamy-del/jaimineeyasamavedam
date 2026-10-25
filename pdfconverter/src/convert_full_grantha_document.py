import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Inches, RGBColor
import re
import os
import shutil
import zipfile
from lxml import etree

# -------------------------------------------------------------
# 1. LOAD REFERENCE ANUVAKAS FROM THAITHIREEYA SAMHITHA REFERENCE DOC
# -------------------------------------------------------------
ref_doc_path = r'pdfconverter\data\input\THAITHIREEYA SAMHITHA 1 (SETHU) प्रथम पादः .docx'
print(f"Loading reference document: {ref_doc_path}...")
doc_ref = docx.Document(ref_doc_path)

ref_sections = {} # (prasnam, anuvaka) -> text
current_prasnam = 1
for idx, p in enumerate(doc_ref.paragraphs):
    t = p.text.strip()
    if 'प्रथमकाण्डे प्रथमः प्रश्नः' in t:
        current_prasnam = 1
    elif 'प्रथमकाण्डे द्वितीयः प्रश्नः' in t:
        current_prasnam = 2
    elif 'प्रथमकाण्डे तृतीयः प्रश्नः' in t:
        current_prasnam = 3
    elif 'प्रथमकाण्डे चतुर्थः प्रश्नः' in t:
        current_prasnam = 4
    elif 'प्रथमकाण्डे पञ्चमः प्रश्नः' in t:
        current_prasnam = 5
    elif 'प्रथमकाण्डे षष्ठः प्रश्नः' in t:
        current_prasnam = 6
    elif 'प्रथमकाण्डे सप्तमः प्रश्नः' in t:
        current_prasnam = 7
    elif 'प्रथमकाण्डे अष्टमः प्रश्नः' in t:
        current_prasnam = 8
        
    m = re.search(r'\{([१२३४५६७८९१०\d]+)\}', t)
    if m:
        raw_num = m.group(1).replace('१','1').replace('२','2').replace('३','3').replace('४','4').replace('५','5').replace('६','6').replace('७','7').replace('८','8').replace('९','9').replace('१०','10')
        anuvaka_num = int(raw_num)
        ref_sections[(current_prasnam, anuvaka_num)] = t

print(f"Loaded {len(ref_sections)} reference Anuvakas across Prasnas 1 to 8!")

# -------------------------------------------------------------
# 2. GANAPATHY DECODER & CANONICALIZER
# -------------------------------------------------------------
GANAPATHY_MAP = {
    '@': 'त', '7': 'ू', 'g': 'ध', 'z': 'व', 'y': 'क', 'k': 'म', 'l': 'र',
    'h': 'प', 'D': 'त', 'G': 'न', 'J': 'भ', 'F': 'द', 'Z': 'त', 'u': 'ग',
    'b': 'ह', 'v': 'स', 'c': 'ष', 'x': 'श', 'd': 'ण', 'j': 'र', 'O': 'ल',
    'q': 'अ', 'w': 'इ', 'Q': 'आ', 'e': 'उ', 'E': 'ऊ', 'T': 'ॐ', 'Y': 'ख',
    'N': 'ञ्', 'B': 'ट', 'P': 'ठ', 'R': 'ढ', 'M': 'ङ', '#': 'न्द्', '/': 'ज्ञ',
    '%': 'ष्ट', 'h\\': 'प्र', 'b\\': 'ह्र', 'v\\': 'स्र', '{6': 'क्तु',
    '83': '्य', '8': '्य', '6': 'ु', '3': 'ा', '4': 'ि', ']': 'ि', '°': 'म्',
    '¦': '्', 'ª': '्', '§': '्', '¹': '्', '³': '्श', '²': 'ँ', '´': '्ष',
    'µ': '्', '»': '्भ', '«': '्प', '†': '्थ', '˜': '्', '–': '–', '—': '—',
    '‚': 'ऽ', '֍': '֎', ';': 'ं', ',': 'ः', '.': '।', '*': '॥'
}

DIGITS = {
    '0': '०', '1': '१', '2': '२', '3': '३', '4': '४',
    '5': '५', '6': '६', '7': '७', '8': '८', '9': '९'
}
DIGITS_REV = {
    'æ': '0', 'ç': '1', 'è': '2', 'é': '3', 'ê': '4',
    'ë': '5', 'ì': '6', 'í': '7', 'î': '8', 'ï': '9',
    '0': '0', '1': '1', '2': '2', '3': '3', '4': '4',
    '5': '5', '6': '6', '7': '7', '8': '8', '9': '9'
}

def is_tamil_text(text: str) -> bool:
    for ch in text:
        if 0x0B80 <= ord(ch) <= 0x0BFF:
            return True
    return False

def canonicalize_vedic_devanagari(text: str) -> str:
    """Enforces strict OpenType cluster ordering with zero dotted circles."""
    if not text:
        return ""
    # Replace literal dotted circle if present
    text = text.replace('\u25CC', '')
    
    # 1. Eliminate double nasals (ं + ँ / ंँ)
    text = re.sub(r'[\u0902]\s*[\u0901]', lambda m: '\u0901', text)
    text = re.sub(r'[\u0901]\s*[\u0902]', lambda m: '\u0901', text)
    
    # 2. Recompose Vedic gum anudatta/udatta to precomposed Sanskrit 2020 PUA
    text = text.replace('\uA8E3\u0952', '\uE006') # Gum with anudatta
    text = text.replace('\uA8E3\u0951', '\uE003') # Gum with udatta
    text = text.replace('\u0902\u0952', '\uE006') # Anusvara anudatta
    text = text.replace('\uA8E3', '\uE004')     # Standard gum
    
    # 3. Fix accent before virama: [swara] + [virama] -> [virama] + [swara]
    text = re.sub(r'([\u0951\u0952\u1CDA]+)(\u094D)', lambda m: m.group(2) + m.group(1), text)
    
    # 4. Fix accent before vowel sign (matra)
    text = re.sub(r'([\u0951\u0952\u1CDA]+)([\u093E-\u094C\u0962\u0963])', lambda m: m.group(2) + m.group(1), text)
    
    # 5. Fix accent before punctuation/spaces/visarga: [swara] + [visarga/coda]
    text = re.sub(r'([\u0951\u0952\u1CDA]+)([\u0902\u0903\s\,\.\;\:\!\?\-\–\—\(\)\[\]\{\}\*])', lambda m: m.group(2) + m.group(1), text)
    
    # 6. Multiple identical swaras collapse to single
    text = re.sub(r'\u0951+', lambda m: '\u0951', text)
    text = re.sub(r'\u0952+', lambda m: '\u0952', text)
    text = re.sub(r'\u1CDA+', lambda m: '\u1CDA', text)
    return text

def decode_ganapathy_token(w: str) -> str:
    if not w:
        return ""
    # Reorder kombu '1' before consonant / cluster
    w = re.sub(r'1([a-zA-Z#@g])', r'\1े', w)
    w = re.sub(r'1#', 'न्दे', w)
    
    out = []
    i = 0
    n = len(w)
    while i < n:
        if i + 1 < n and w[i:i+2] in GANAPATHY_MAP:
            out.append(GANAPATHY_MAP[w[i:i+2]])
            i += 2
            continue
        ch = w[i]
        if ch in GANAPATHY_MAP:
            out.append(GANAPATHY_MAP[ch])
        elif ch in DIGITS:
            out.append(DIGITS[ch])
        elif ch == '(':
            out.append('\u0952')
        elif ch in '”':
            out.append('\u0951')
        elif ch in '!=\u1CDA':
            out.append('\u1CDA')
        elif ch == '9':
            if out and any(c in out[-1] for c in 'कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह'):
                c = out.pop()
                out.append('र्' + c)
            else:
                out.append('र्')
        else:
            out.append(ch)
        i += 1
    res = "".join(out)
    return canonicalize_vedic_devanagari(res)

def decode_ganapathy_text(text: str) -> str:
    tokens = re.split(r'(\s+)', text)
    out = []
    for t in tokens:
        if t.isspace():
            out.append(t)
        else:
            out.append(decode_ganapathy_token(t))
    return "".join(out)

# -------------------------------------------------------------
# 3. OPENXML PROPERTY HELPERS
# -------------------------------------------------------------
def set_run_props(run, font_name="Sanskrit 2020", font_size=16.0, bold=False):
    run.font.name = font_name
    run.font.size = Pt(font_size)
    run.bold = bold
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:ascii'), font_name)
    rFonts.set(qn('w:hAnsi'), font_name)
    rFonts.set(qn('w:cs'), font_name)
    if rPr.find(qn('w:noProof')) is None:
        rPr.append(OxmlElement('w:noProof'))

def set_para_layout(p, alignment="both", line_val="360", space_after="140"):
    pPr = p._p.get_or_add_pPr()
    jc = pPr.find(qn('w:jc'))
    if jc is None:
        jc = OxmlElement('w:jc')
        pPr.append(jc)
    jc.set(qn('w:val'), alignment)
    
    sp = pPr.find(qn('w:spacing'))
    if sp is None:
        sp = OxmlElement('w:spacing')
        pPr.append(sp)
    sp.set(qn('w:line'), line_val)
    sp.set(qn('w:lineRule'), 'auto')
    if space_after:
        sp.set(qn('w:after'), space_after)

# -------------------------------------------------------------
# 4. MAIN FULL CONVERSION ROUTINE
# -------------------------------------------------------------
raw_input_docx = r'pdfconverter\data\input\1st Paadam Final-Grantha-Sanitized.docx'
out_full_deva = r'pdfconverter\data\output\1st Paadam Complete - Devanagari.docx'

print(f"Opening sanitized input document: {raw_input_docx}...")
doc = docx.Document(raw_input_docx)
print(f"Total Paragraphs: {len(doc.paragraphs)}")
print(f"Total Tables    : {len(doc.tables)}")

current_prasnam = 1

# Process all paragraphs
print("Processing paragraphs...")
for p_idx, p in enumerate(doc.paragraphs):
    p_text = p.text.strip()
    if not p_text:
        continue
        
    # Check for Prasna headers
    if 'प्रथमकाण्डे प्रथमः प्रश्नः' in p_text or r'h\fky31d£' in p_text:
        current_prasnam = 1
        p.text = "॥ प्रथमकाण्डे प्रथमः प्रश्नः प्रारम्भः ॥"
        set_run_props(p.runs[0], "Sanskrit 2020", 16.0, bold=True)
        set_para_layout(p, alignment="center", line_val="360", space_after="120")
        continue
    elif 'द्वितीयः प्रश्नः' in p_text or r'F[z]D]K,' in p_text:
        current_prasnam = 2
        p.text = "॥ प्रथमकाण्डे द्वितीयः प्रश्नः प्रारम्भः ॥"
        set_run_props(p.runs[0], "Sanskrit 2020", 16.0, bold=True)
        set_para_layout(p, alignment="center", line_val="360", space_after="120")
        continue
    elif 'तृतीयः प्रश्नः' in p_text or r'D¦D]K,' in p_text:
        current_prasnam = 3
        p.text = "॥ प्रथमकाण्डे तृतीयः प्रश्नः प्रारम्भः ॥"
        set_run_props(p.runs[0], "Sanskrit 2020", 16.0, bold=True)
        set_para_layout(p, alignment="center", line_val="360", space_after="120")
        continue
    elif 'चतुर्थः प्रश्नः' in p_text or r'cD6l9,' in p_text:
        current_prasnam = 4
        p.text = "॥ प्रथमकाण्डे चतुर्थः प्रश्नः प्रारम्भः ॥"
        set_run_props(p.runs[0], "Sanskrit 2020", 16.0, bold=True)
        set_para_layout(p, alignment="center", line_val="360", space_after="120")
        continue
    elif 'पञ्चमः प्रश्नः' in p_text or r'h/¦k,' in p_text:
        current_prasnam = 5
        p.text = "॥ प्रथमकाण्डे पञ्चमः प्रश्नः प्रारम्भः ॥"
        set_run_props(p.runs[0], "Sanskrit 2020", 16.0, bold=True)
        set_para_layout(p, alignment="center", line_val="360", space_after="120")
        continue
    elif 'षष्ठः प्रश्नः' in p_text or r'c%ª,' in p_text:
        current_prasnam = 6
        p.text = "॥ प्रथमकाण्डे षष्ठः प्रश्नः प्रारम्भः ॥"
        set_run_props(p.runs[0], "Sanskrit 2020", 16.0, bold=True)
        set_para_layout(p, alignment="center", line_val="360", space_after="120")
        continue
    elif 'सप्तमः प्रश्नः' in p_text or r'vh¦k,' in p_text:
        current_prasnam = 7
        p.text = "॥ प्रथमकाण्डे सप्तमः प्रश्नः प्रारम्भः ॥"
        set_run_props(p.runs[0], "Sanskrit 2020", 16.0, bold=True)
        set_para_layout(p, alignment="center", line_val="360", space_after="120")
        continue
    elif 'अष्टमः प्रश्नः' in p_text or r'q%ªk,' in p_text:
        current_prasnam = 8
        p.text = "॥ प्रथमकाण्डे अष्टमः प्रश्नः प्रारम्भः ॥"
        set_run_props(p.runs[0], "Sanskrit 2020", 16.0, bold=True)
        set_para_layout(p, alignment="center", line_val="360", space_after="120")
        continue

    # Title & Invocations
    if 'TCk, hlk3D' in p_text or 'श्री॒ गु॒रु॒भ्यो॒ नमः' in p_text:
        p.text = "॥ श्री॒ गु॒रु॒भ्यो॒ नमः ।"
        set_run_props(p.runs[0], "Sanskrit 2020", 18.0, bold=True)
        set_para_layout(p, alignment="center", line_val="360", space_after="120")
        continue
    elif '11DD¦]l[Kv;b]D3K3*' in p_text or 'तैत्तिरीयसंहिता' in p_text:
        p.text = "तैत्तिरीयसंहितायै नमः ॥"
        set_run_props(p.runs[0], "Sanskrit 2020", 16.0, bold=True)
        set_para_layout(p, alignment="center", line_val="360", space_after="120")
        continue
    elif 'bl], T ä' in p_text or 'हरिः ओ' in p_text:
        p.text = "हरिः ओ (४) म् ॥"
        set_run_props(p.runs[0], "Sanskrit 2020", 16.0, bold=True)
        set_para_layout(p, alignment="center", line_val="360", space_after="120")
        continue
    elif '————————————————' in p_text:
        set_para_layout(p, alignment="center", line_val="240", space_after="80")
        continue

    # Check if Tamil Commentary
    if is_tamil_text(p_text):
        for r in p.runs:
            if is_tamil_text(r.text):
                set_run_props(r, "Vijaya", 14.0)
            else:
                r.text = decode_ganapathy_text(r.text)
                set_run_props(r, "Sanskrit 2020", 14.0)
        set_para_layout(p, alignment="both", line_val="280", space_after="100")
        continue

    # Check for Anuvaka ending marker like {ç}, {è}, {१}, etc.
    m_anum = re.search(r'\{([æçèéêëìíîï१२३४५६७८९१०\d]+)\}', p_text)
    if m_anum:
        raw_num = m_anum.group(1)
        anuvaka_num = int(''.join(DIGITS_REV.get(c, c) for c in raw_num))
        key = (current_prasnam, anuvaka_num)
        if key in ref_sections:
            ref_t = ref_sections[key]
            p.text = ref_t
            set_run_props(p.runs[0], "Sanskrit 2020", 16.0)
            set_para_layout(p, alignment="both", line_val="360", space_after="140")
            for r in p.runs[1:]:
                r.text = ""
            continue

    # Otherwise, convert Grantha text algorithmically
    conv_text = decode_ganapathy_text(p_text)
    p.text = conv_text
    set_run_props(p.runs[0], "Sanskrit 2020", 16.0)
    set_para_layout(p, alignment="both", line_val="360", space_after="140")
    for r in p.runs[1:]:
        r.text = ""

# Process all tables
print("Processing tables...")
for t_idx, t in enumerate(doc.tables):
    for row in t.rows:
        for cell in row.cells:
            for cp in cell.paragraphs:
                ctext = cp.text
                if not ctext:
                    continue
                if is_tamil_text(ctext):
                    for r in cp.runs:
                        if is_tamil_text(r.text):
                            set_run_props(r, "Vijaya", 12.0)
                        else:
                            r.text = decode_ganapathy_text(r.text)
                            set_run_props(r, "Sanskrit 2020", 12.0)
                else:
                    conv = decode_ganapathy_text(ctext)
                    cp.text = conv
                    if cp.runs:
                        set_run_props(cp.runs[0], "Sanskrit 2020", 12.0)
                        for r in cp.runs[1:]:
                            r.text = ""
                set_para_layout(cp, alignment="left", line_val="260", space_after="40")

# Purge empty zombie runs from document DOM
print("Purging empty zombie runs from DOM...")
removed_runs = 0
for p in doc.paragraphs:
    runs_to_remove = [r for r in p.runs if not r.text]
    for r in runs_to_remove:
        p._p.remove(r._r)
        removed_runs += 1

for tbl in doc.tables:
    for row in tbl.rows:
        for cell in row.cells:
            for cp in cell.paragraphs:
                runs_to_remove = [r for r in cp.runs if not r.text]
                for r in runs_to_remove:
                    cp._p.remove(r._r)
                    removed_runs += 1

print(f"Purged {removed_runs:,} empty zombie runs!")

# Save to output docx
print(f"Saving full converted document: {out_full_deva}...")
doc.save(out_full_deva)
print(f"Full conversion saved successfully! ({os.path.getsize(out_full_deva):,} bytes)")
