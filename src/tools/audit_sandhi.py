#!/usr/bin/env python3
"""
Sanskrit Sandhi Auditor for Jaimineeya Samaveda Pipeline.

Audits Paninian Sandhi rules across:
1. Arsheyam (Subsection headers)
2. Rik Verses (rik_text)
3. Rik Metadata (rik_metadata)
4. Samam Chants (corrected-mantra_sets / mantra_sets)
5. Saman Metadata (saman_metadata)

Generates an interactive HTML audit report, Markdown summary, and JSON dataset.
"""

import json
import re
import base64
import argparse
from pathlib import Path
from collections import defaultdict, Counter

VOICED_CONS = 'गघङजझञडढणदधनबभमयर्लवह'
VOICED_STOPS = 'गघजझडढदधबभ'
VOWELS = 'अआइईउऊऋएऐओऔ'
MATRAS = 'ािीुूृेैोौ'

def clean_swaras_for_sandhi(text: str) -> str:
    """Removes swara numbers in parentheses, Vedic accents, and dandas for clean Sandhi checking."""
    if not text:
        return ""
    # Remove parentheses swara markers like (1), (2), (ति), (ता), etc.
    s = re.sub(r'\([^\)]+\)', '', text)
    # Remove standalone Vedic accents (Svarita, Anudatta, Kampa combining marks)
    s = re.sub(r'[\u1cd0-\u1cf9\u0951\u0952]', '', s)
    return s

def audit_subsection(sub_key: str, sub: dict, parva: str, kandah: str) -> list:
    """Audits a single subsection across all 5 text dimensions."""
    findings = []
    
    h = sub.get('header', {}).get('header', '')
    rm = sub.get('rik_metadata', '')
    sm = sub.get('saman_metadata', '')
    rt = sub.get('rik_text', '')
    cm_list = [m.get('corrected-mantra', '') for m in sub.get('corrected-mantra_sets', sub.get('mantra_sets', []))]
    
    # -------------------------------------------------------------
    # 1. ARSHEYAM (Subsection Header)
    # -------------------------------------------------------------
    if h:
        clean_h = h.strip('॥| ')
        
        # Rule 1: Anusvara before vowel
        for m in re.finditer(r'(\S*[\u0902]\s*[' + VOWELS + r']\S*)', clean_h):
            matched = m.group(1)
            suggested = re.sub(r'([\u0902])(\s*)([' + VOWELS + '])', r'म् \3', matched)
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Arsheyam Header',
                'rule_name': 'अचि अनुस्वार-दोषः (Anusvara before Vowel)',
                'sutra': 'मोऽनुस्वारः (८.३.२३)',
                'severity': 'High',
                'suspect': matched,
                'suggested': suggested,
                'explanation': 'Before a vowel, final nasal MUST be full makara (म्), never anusvara (ं).',
                'context': h
            })
            
        # Rule 3: Voiceless stop before voiced stop (Jashtva)
        for m in re.finditer(r'(\S*(?:[तकपचट]\u094d)\s*[' + VOICED_STOPS + r']\S*)', clean_h):
            matched = m.group(1)
            # Suggest voiced equivalent only immediately before voiced stop
            repl_map = {'त्': 'द्', 'क्': 'ग्', 'प्': 'ब्', 'च्': 'ज्', 'ट्': 'ड्'}
            sug = re.sub(r'([तकपचट]\u094d)(\s*[' + VOICED_STOPS + '])', lambda match: repl_map.get(match.group(1), match.group(1)) + match.group(2), matched)
            if 'वार्ग्जभ' in sug:
                sug = sug.replace('वार्ग्जभ', 'वार्ग्जम्भ')
            elif 'वार्क्जभ' in matched:
                sug = matched.replace('वार्क्जभ', 'वार्ग्जम्भ')
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Arsheyam Header',
                'rule_name': 'जश्त्वाभावः (Voiceless Stop before Voiced Stop)',
                'sutra': 'झलां जशोऽन्ते (८.२.३९) / झलां जश् झशि (८.४.५३)',
                'severity': 'High',
                'suspect': matched,
                'suggested': sug,
                'explanation': 'Voiceless stop before a voiced stop must assimilate to its voiced unaspirated stop (e.g. त् -> द्, क् -> ग्).',
                'context': h
            })
            
        # Rule 4: Dental nasal before palatal (Schutva / Parasavarna)
        for m in re.finditer(r'(\S*न्\s*[चछजझ]\S*)', clean_h):
            matched = m.group(1)
            sug = matched.replace('न्च', 'ञ्च').replace('न्ज', 'ञ्ज').replace('न् च', 'ञ्च').replace('न् ज', 'ञ्ज')
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Arsheyam Header',
                'rule_name': 'श्चुत्वाभावः / परसवर्णः (Dental Nasal before Palatal)',
                'sutra': 'स्तोः श्चुना श्चुः (८.४.४०) & अनुस्वारस्य ययि परसवर्णः (८.४.५८)',
                'severity': 'High',
                'suspect': matched,
                'suggested': sug,
                'explanation': 'Dental nasal (न्) before a palatal consonant (च, ज) must assimilate to palatal nasal (ञ्).',
                'context': h
            })
            
        # Rule 5: Visarga of aH before voiced consonant (Hashi ca)
        for m in re.finditer(r'([^\u093e\u093f\u0940\u0941\u0942\u0943\u0944\u0947\u0948\u094b\u094c\s]ः\s*[' + VOICED_CONS + r']\S*)', clean_h):
            matched = m.group(1)
            sug = re.sub(r'([क-ह])ः\s*([' + VOICED_CONS + '])', r'\1ो \2', matched)
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Arsheyam Header',
                'rule_name': 'हशि चाभावः (Visarga of aH before Voiced Consonant)',
                'sutra': 'हशि च (६.१.११४)',
                'severity': 'High',
                'suspect': matched,
                'suggested': sug,
                'explanation': 'A visarga preceded by short a before any voiced consonant (हश्) must change to o (e.g. त्रयः देवानाम् -> त्रयो देवानाम्).',
                'context': h
            })
            
        # Rule 11: Smushed words after pragrihya dual dve
        for m in re.finditer(r'(\S*द्वे[क-हअ-औ]\S*)', clean_h):
            matched = m.group(1)
            sug = matched.replace('द्वे', 'द्वे ')
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Arsheyam Header',
                'rule_name': 'प्रगृह्य-असंयुक्त-पददोषः (Smushed Word after Pragrihya द्वे)',
                'sutra': 'ईदूदेद् द्विवचनं प्रगृह्यम् (१.१.११)',
                'severity': 'Medium',
                'suspect': matched,
                'suggested': sug,
                'explanation': 'Feminine/neuter dual द्वे is pragrihya (no sandhi with vowel); words must be separated by space rather than jammed together.',
                'context': h
            })
            
        # Rule 11b: Smushed words after numeral titles
        for m in re.finditer(r'(\S*(?:त्रीणि|चत्वारि|द्वौ)[क-हअ-औ]\S*)', clean_h):
            matched = m.group(1)
            sug = re.sub(r'(त्रीणि|चत्वारि|द्वौ)([क-हअ-औ])', r'\1 \2', matched)
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Arsheyam Header',
                'rule_name': 'शीर्षक-संख्या-असंयुक्तदोषः (Smushed Numeral Title)',
                'sutra': 'शीर्षक-पदच्छेद-नियमः (Header Word Separation)',
                'severity': 'Medium',
                'suspect': matched,
                'suggested': sug,
                'explanation': 'Numeral title words (त्रीणि, चत्वारि) must be separated by space from following words.',
                'context': h
            })
            
        # Rule 12: Corrupted double matras
        for m in re.finditer(r'(\S*[\u093e\u0947\u094b][\u0948\u094c]\S*)', clean_h):
            matched = m.group(1)
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Arsheyam Header',
                'rule_name': 'द्विमात्र-दोषः (Corrupted Double Vowel Matra)',
                'sutra': 'अक्षर-दोष-निवारणम् (Typographical Glitch)',
                'severity': 'High',
                'suspect': matched,
                'suggested': matched.replace('ाै', 'ौ'),
                'explanation': 'Corrupted double vowel matra sequence (e.g. aa + au) from OCR or typing glitch.',
                'context': h
            })

    # -------------------------------------------------------------
    # 2. RIK METADATA (Rishi, Devata, Chandas)
    # -------------------------------------------------------------
    if rm:
        clean_rm = re.sub(r'\([^\)]+\)', '', rm).strip('॥| ')
        
        # Patronymic corruption: शय्युबार्हस्पत्यः
        if 'शय्युबार्हस्पत्यः' in rm:
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Rik Metadata',
                'rule_name': 'लुप्तरेफ-दोषः (Dropped Repha in Patronymic)',
                'sutra': 'ससजुषो रुः (८.२.६६) / रोऽसुपि',
                'severity': 'High',
                'suspect': 'शय्युबार्हस्पत्यः',
                'suggested': 'शय्युर्बार्हस्पत्यः',
                'explanation': 'The Rishi is शय्युः (Śayyu). Visarga of uH before voiced b MUST become repha (र्) in sandhi, or be separated by space.',
                'context': rm
            })
            
        # Patronymic corruption: भागर्वः
        if 'भागर्वः' in rm:
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Rik Metadata',
                'rule_name': 'गोत्रनाम-अशुद्धिः (Misspelled Gotra Patronymic)',
                'sutra': 'नाम-शुद्धि-नियमः (Proper Noun Orthography)',
                'severity': 'High',
                'suspect': 'भागर्वः',
                'suggested': 'भार्गवः',
                'explanation': 'Typographical corruption for भार्गवः (Bhārgava) with misplaced repha and spurious lengthening.',
                'context': rm
            })
            
        # Corrupted double matra
        for m in re.finditer(r'(\S*[\u093e\u0947\u094b][\u0948\u094c]\S*)', rm):
            matched = m.group(1)
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Rik Metadata',
                'rule_name': 'द्विमात्र-दोषः (Corrupted Double Vowel Matra)',
                'sutra': 'अक्षर-दोष-निवारणम् (Typographical Glitch)',
                'severity': 'High',
                'suspect': matched,
                'suggested': matched.replace('ाै', 'ौ'),
                'explanation': 'Corrupted double vowel matra sequence (e.g. ाै in सुकक्षत्रुतकाै).',
                'context': rm
            })

    # -------------------------------------------------------------
    # 3. SAMAN METADATA (Arsheya line for Samam)
    # -------------------------------------------------------------
    if sm:
        clean_sm = re.sub(r'\([^\)]+\)', '', sm).strip('॥| ')
        
        # Rule 1: Anusvara before vowel
        for m in re.finditer(r'(\S*[\u0902]\s*[' + VOWELS + r']\S*)', clean_sm):
            matched = m.group(1)
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Saman Metadata',
                'rule_name': 'अचि अनुस्वार-दोषः (Anusvara before Vowel)',
                'sutra': 'मोऽनुस्वारः (८.३.२३)',
                'severity': 'High',
                'suspect': matched,
                'suggested': re.sub(r'([\u0902])(\s*)([' + VOWELS + '])', r'म् \3', matched),
                'explanation': 'Before a vowel, final nasal MUST be full makara (म्), never anusvara (ं).',
                'context': sm
            })
            
        # Schutva: वाजजित् जगती
        for m in re.finditer(r'(\S*(?:[तद]\u094d)\s*[चछजझश]\S*)', clean_sm):
            matched = m.group(1)
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Saman Metadata',
                'rule_name': 'श्चुत्वाभावः (Dental Stop before Palatal)',
                'sutra': 'स्तोः श्चुना श्चुः (८.४.४०)',
                'severity': 'High',
                'suspect': matched,
                'suggested': matched.replace('त् ज', 'ज्ज').replace('त्ज', 'ज्ज'),
                'explanation': 'Dental stop (त्) before palatal (ज) must assimilate to palatal stop (ज्, e.g. वाजजिज्जगती).',
                'context': sm
            })
            
        # Rule 5: aH before voiced consonant in Saman metadata
        for m in re.finditer(r'([^\u093e\u093f\u0940\u0941\u0942\u0943\u0944\u0947\u0948\u094b\u094c\s]ः\s+[' + VOICED_CONS + r']\S*)', clean_sm):
            matched = m.group(1)
            sug = re.sub(r'([क-ह])ः\s+([' + VOICED_CONS + '])', r'\1ो \2', matched)
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Saman Metadata',
                'rule_name': 'हशि चाभावः (Visarga of aH before Voiced Consonant)',
                'sutra': 'हशि च (६.१.११४)',
                'severity': 'Medium',
                'suspect': matched,
                'suggested': sug,
                'explanation': 'In sandhi, visarga of aH before voiced consonant becomes o (e.g. वत्सः गायत्र्यग्निः -> वत्सो गायत्र्यग्निः).',
                'context': sm
            })
            
        # Rule 6: non-a/aa visarga before voiced consonant in Saman metadata
        for m in re.finditer(r'([िीुूेैोौ]ः\s+[' + VOICED_CONS + r']\S*)', clean_sm):
            matched = m.group(1)
            sug = re.sub(r'([िीुूेैोौ])ः\s+([क-ह])', r'\1र्\2', matched)
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Saman Metadata',
                'rule_name': 'रुत्वाभावः (Non-a Visarga before Voiced Consonant)',
                'sutra': 'ससजुषो रुः (८.२.६६)',
                'severity': 'Medium',
                'suspect': matched,
                'suggested': sug,
                'explanation': 'Visarga after i, u, o before voiced consonant must become repha (e.g. द्वयोः मृगयुः -> द्वयोर्मृगयुः).',
                'context': sm
            })
            
        # Rule 7: aaH before voiced consonant/vowel in Saman metadata
        for m in re.finditer(r'(ाः\s+[' + VOICED_CONS + VOWELS + r']\S*)', clean_sm):
            matched = m.group(1)
            sug = re.sub(r'ाः\s+', 'ा ', matched)
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Saman Metadata',
                'rule_name': 'विसर्गलोपाभावः (Visarga of aaH before Voiced Sound)',
                'sutra': 'हलि सर्वेषाम् (८.३.२२) / भोभगोअघोअपूर्वस्य... (८.३.१७)',
                'severity': 'Medium',
                'suspect': matched,
                'suggested': sug,
                'explanation': 'Visarga after long aa drops before all voiced consonants and vowels (e.g. विश्वमनाः गायत्र्यग्निः -> विश्वमना गायत्र्यग्निः).',
                'context': sm
            })
            
        # Rule 13: Inconsistent Devata-Chandas compound hiatus
        for m in re.finditer(r'(गायत्री\s+इन्द्र\S*)', clean_sm):
            matched = m.group(1)
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Saman Metadata',
                'rule_name': 'देवताच्छन्दः-दीर्घसन्ध्यभावः (Devata-Chandas Hiatus)',
                'sutra': 'अकः सवर्णे दीर्घः (६.१.१०१)',
                'severity': 'Medium',
                'suspect': matched,
                'suggested': matched.replace('गायत्री इन्द्र', 'गायत्रीन्द्र'),
                'explanation': 'Savarna deergha sandhi between गायत्री and इन्द्र should yield गायत्रीन्द्र (as applied elsewhere in the corpus).',
                'context': sm
            })

    # -------------------------------------------------------------
    # 4. RIK TEXT (Vedic Verses)
    # -------------------------------------------------------------
    if rt:
        clean_rt = clean_swaras_for_sandhi(rt)
        
        # Rule 1: Anusvara before vowel
        for m in re.finditer(r'(\S*[\u0902]\s*[' + VOWELS + r']\S*)', clean_rt):
            matched = m.group(1)
            sug = re.sub(r'([\u0902])(\s*)([' + VOWELS + '])', r'म् \3', matched)
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Rik Text',
                'rule_name': 'अचि अनुस्वार-दोषः (Anusvara before Vowel in Rik)',
                'sutra': 'मोऽनुस्वारः (८.३.२३)',
                'severity': 'High',
                'suspect': matched,
                'suggested': sug,
                'explanation': 'In Sanskrit grammar, an anusvara (ं) cannot occur before a vowel; it must be makara (म्, e.g. माहं आसि -> माहम् आसि).',
                'context': rt[:80] + '...'
            })
            
        # Rule 2: Anusvara before danda
        for m in re.finditer(r'(\S*[\u0902]\s*[।॥])', clean_rt):
            matched = m.group(1)
            sug = re.sub(r'([\u0902])(\s*)([।॥])', r'म् \2\3', matched)
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Rik Text',
                'rule_name': 'पादान्ते अनुस्वार-दोषः (Anusvara before Danda in Rik)',
                'sutra': 'वाऽवसाने (८.४.५९) / Samavedic Paadanta Norm',
                'severity': 'Medium',
                'suspect': matched,
                'suggested': sug,
                'explanation': 'Standardized Samavedic sandhi before paadanta dandas requires makara (म् ।), not anusvara (ं ।).',
                'context': rt[:80] + '...'
            })
            
        # Rule 3: Voiceless stop before voiced stop across word boundary
        for m in re.finditer(r'(\S+(?:[तकपचट]\u094d)\s+[' + VOICED_STOPS + r']\S*)', clean_rt):
            matched = m.group(1)
            sug = matched.replace('त् ', 'द् ').replace('प् ', 'ब् ').replace('क् ', 'ग् ')
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Rik Text',
                'rule_name': 'जश्त्वाभावः (Voiceless Stop before Voiced Stop in Rik)',
                'sutra': 'झलां जशोऽन्ते (८.२.३९)',
                'severity': 'High',
                'suspect': matched,
                'suggested': sug,
                'explanation': 'Voiceless stop across word boundary before a voiced stop must be voiced (e.g. यत्गवे -> यद्गवे, इत् भूः -> इद् भूः).',
                'context': rt[:80] + '...'
            })
            
        # Rule 4: Schutva in Rik (e.g. दिविसत्शुक्र, हंस् च)
        for m in re.finditer(r'(\S*(?:[तदस्]\u094d)\s*[चछजझश]\S*)', clean_rt):
            matched = m.group(1)
            if any(k in matched for k in ['श्च', 'च्छ', 'ज्ज']):
                continue
            sug = matched.replace('त्श', 'च्छ').replace('त् शुक्र', 'च्छुक्र').replace('स् च', 'श्च').replace('स्च', 'श्च')
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Rik Text',
                'rule_name': 'श्चुत्वाभावः (Dental before Palatal in Rik)',
                'sutra': 'स्तोः श्चुना श्चुः (८.४.४०)',
                'severity': 'High',
                'suspect': matched,
                'suggested': sug,
                'explanation': 'Dental stop (त्) or sibilant (स्) before a palatal (च, श) must assimilate to palatal (e.g. हंस् च -> हंश्च, दिविसत्शुक्र -> दिविसच्छुक्र).',
                'context': rt[:80] + '...'
            })
            
        # Rule 4b: Dental nasal before palatal in Rik (e.g. मृन्जसे -> मृञ्जसे)
        for m in re.finditer(r'(\S*न्\s*[चछजझ]\S*)', clean_rt):
            matched = m.group(1)
            sug = matched.replace('न्ज', 'ञ्ज').replace('न्च', 'ञ्च')
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Rik Text',
                'rule_name': 'परसवर्ण-श्चुत्वाभावः (Dental Nasal before Palatal in Rik)',
                'sutra': 'अनुस्वारस्य ययि परसवर्णः (८.४.५८)',
                'severity': 'High',
                'suspect': matched,
                'suggested': sug,
                'explanation': 'Dental nasal (न्) before palatal (ज, च) must assimilate to palatal nasal (ञ्, e.g. मृन्जसे -> मृञ्जसे, सिन्चाध्वम् -> सिञ्चाध्वम्).',
                'context': rt[:80] + '...'
            })
            
        # Rule 8: Unassimilated visarga before ca/cha in Rik
        for m in re.finditer(r'(\S*ः\s*[चछ]\S*)', clean_rt):
            matched = m.group(1)
            sug = re.sub(r'ः\s*च', 'श्च', matched)
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Rik Text',
                'rule_name': 'विसर्गस्य शकारः (Visarga before Palatal in Rik)',
                'sutra': 'विसर्जनीयस्य सः (८.३.३४) + स्तोः श्चुना श्चुः (८.४.४०)',
                'severity': 'High',
                'suspect': matched,
                'suggested': sug,
                'explanation': 'Visarga before ca/cha must assimilate to sh (श्, e.g. यामैः चित्रा -> यामैश्चित्रा).',
                'context': rt[:80] + '...'
            })

    # -------------------------------------------------------------
    # 5. SAMAM CHANT TEXT (corrected-mantra)
    # -------------------------------------------------------------
    for cm in cm_list:
        if not cm:
            continue
        clean_cm = clean_swaras_for_sandhi(cm)
        
        # Rule 1: Anusvara before vowel
        for m in re.finditer(r'(\S*[\u0902]\s*[' + VOWELS + r']\S*)', clean_cm):
            matched = m.group(1)
            sug = re.sub(r'([\u0902])(\s*)([' + VOWELS + '])', r'म् \3', matched)
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Samam Chant',
                'rule_name': 'अचि अनुस्वार-दोषः (Anusvara before Vowel in Samam)',
                'sutra': 'मोऽनुस्वारः (८.३.२३)',
                'severity': 'High',
                'suspect': matched,
                'suggested': sug,
                'explanation': 'Anusvara before vowel should be makara (म्, e.g. रुद्रंआ -> रुद्रमा, आयं अग्नि -> अयम् अग्नि).',
                'context': cm[:80] + '...'
            })
            
        # Rule 2: Anusvara before danda
        for m in re.finditer(r'(\S*[\u0902]\s*[।॥])', clean_cm):
            matched = m.group(1)
            sug = re.sub(r'([\u0902])(\s*)([।॥])', r'म् \2\3', matched)
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Samam Chant',
                'rule_name': 'पादान्ते अनुस्वार-दोषः (Anusvara before Danda in Samam)',
                'sutra': 'वाऽवसाने (८.४.५९) / Samavedic Paadanta Norm',
                'severity': 'Medium',
                'suspect': matched,
                'suggested': sug,
                'explanation': 'Paadanta nasal before danda standardized to makara (म् ।) in Samavedic orthography.',
                'context': cm[:80] + '...'
            })

        # Rule 3: Parasavarna - Dental stop (त, थ, द, ध) -> न्
        for m in re.finditer(r'(\S*[\u0902]\s*([तथदध])\S*)', clean_cm):
            matched = m.group(1)
            sug = re.sub(r'([\u0902])(\s*)([तथदध])', r'न्\3', matched)
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Samam Chant',
                'rule_name': 'परसवर्णः (Anusvara before Dental in Samam)',
                'sutra': 'अनुस्वारस्य ययि परसवर्णः (८.४.५८)',
                'severity': 'High',
                'suspect': matched,
                'suggested': sug,
                'explanation': 'Anusvara before dental stop (त, थ, द, ध) assimilates to dental nasal (न्, e.g. त्वां त्वा -> त्वान्त्वा).',
                'context': cm[:80] + '...'
            })

        # Rule 4: Parasavarna - Palatal stop (च, छ, ज, झ) -> ञ्
        for m in re.finditer(r'(\S*[\u0902]\s*([चछजझ])\S*)', clean_cm):
            matched = m.group(1)
            sug = re.sub(r'([\u0902])(\s*)([चछजझ])', r'ञ्\3', matched)
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Samam Chant',
                'rule_name': 'परसवर्णः (Anusvara before Palatal in Samam)',
                'sutra': 'अनुस्वारस्य ययि परसवर्णः (८.४.५८)',
                'severity': 'High',
                'suspect': matched,
                'suggested': sug,
                'explanation': 'Anusvara before palatal stop (च, छ, ज, झ) assimilates to palatal nasal (ञ्, e.g. किंच -> किञ्च).',
                'context': cm[:80] + '...'
            })

        # Rule 5: Parasavarna - Velar stop (क, ख, ग, घ) -> ङ्
        for m in re.finditer(r'(\S*[\u0902]\s*([कखगघ])\S*)', clean_cm):
            matched = m.group(1)
            sug = re.sub(r'([\u0902])(\s*)([कखगघ])', r'ङ्\3', matched)
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Samam Chant',
                'rule_name': 'परसवर्णः (Anusvara before Velar in Samam)',
                'sutra': 'अनुस्वारस्य ययि परसवर्णः (८.४.५८)',
                'severity': 'High',
                'suspect': matched,
                'suggested': sug,
                'explanation': 'Anusvara before velar stop (क, ख, ग, घ) assimilates to velar nasal (ङ्, e.g. संगमे -> सङ्गमे).',
                'context': cm[:80] + '...'
            })

        # Rule 6: Purvarupa Sandhi (एङ्ः पदान्तादति - e/o before a)
        for m in re.finditer(r'(\S*[ेो]\s+अ[क-ह]\S*)', clean_cm):
            matched = m.group(1)
            sug = re.sub(r'([ेो])\s+अ', r'\1ऽ', matched)
            findings.append({
                'sub_key': sub_key,
                'parva': parva,
                'kandah': kandah,
                'field': 'Samam Chant',
                'rule_name': 'पूर्वरूप-सन्ध्यभावः (Purvarupa e/o before a in Samam)',
                'sutra': 'एङ्ः पदान्तादति (६.१.१०९)',
                'severity': 'Medium',
                'suspect': matched,
                'suggested': sug,
                'explanation': 'Padanta e/o followed by short a elides the a with avagraha (e.g. त्वान्त्वन्नो अग्ने -> त्वान्त्वन्नोऽग्ने).',
                'context': cm[:80] + '...'
            })

    return findings

def build_txt_line_index(txt_path: Path) -> dict:
    """Builds a map of (sub_key, field) -> line number in Samhita_Devanagari_Unicode.txt"""
    if not txt_path or not txt_path.exists():
        return {}
    lines = txt_path.read_text(encoding='utf-8').splitlines()
    line_index = {}
    for idx, line in enumerate(lines, 1):
        if '# Start of Rik Metadata --' in line:
            sub = line.split('--')[1].split('##')[0].strip()
            line_index[(sub, 'Rik Metadata')] = idx + 1
        elif '# Start of Rik Text --' in line:
            sub = line.split('--')[1].split('##')[0].strip()
            line_index[(sub, 'Rik Text')] = idx + 1
        elif '# Start of SubSection Title --' in line:
            sub = line.split('--')[1].split('##')[0].strip()
            line_index[(sub, 'Arsheyam Header')] = idx + 1
            line_index[(sub, 'Saman Metadata')] = idx + 1
        elif '#Start of Mantra Sets --' in line or '# Start of Mantra Sets --' in line:
            sub = line.split('--')[1].split('##')[0].strip()
            line_index[(sub, 'Samam Chant')] = idx + 1
    return line_index

def run_sandhi_audit_txt(txt_path: Path):
    """Directly parses and audits Samhita_Devanagari_Unicode.txt, assigning exact line numbers."""
    if not txt_path or not txt_path.exists():
        raise FileNotFoundError(f"Master text file not found at {txt_path}")
        
    lines = txt_path.read_text(encoding='utf-8').splitlines()
    subs = {}
    current_ss = 'पूर्वार्चिकम्'
    current_sec = 'आग्नेयकाण्डम्'
    current_sub = ''
    current_field = ''
    
    for idx, line in enumerate(lines, 1):
        raw = line.strip()
        if not raw:
            continue
        if raw.startswith('#'):
            if 'Start of SuperSection Title --' in raw:
                current_ss = raw.split('--')[1].split('##')[0].strip()
            elif 'Start of Section Title --' in raw:
                current_sec = raw.split('--')[1].split('##')[0].strip()
            elif 'Start of SubSection Title --' in raw:
                current_sub = raw.split('--')[1].split('##')[0].strip()
                current_field = 'header'
            elif 'Start of Rik Metadata --' in raw:
                current_sub = raw.split('--')[1].split('##')[0].strip()
                current_field = 'rik_metadata'
            elif 'Start of Rik Text --' in raw:
                current_sub = raw.split('--')[1].split('##')[0].strip()
                current_field = 'rik_text'
            elif 'Start of Mantra Sets --' in raw or '#Start of Mantra Sets --' in raw:
                current_sub = raw.split('--')[1].split('##')[0].strip()
                current_field = 'mantra_sets'
            elif 'Start of Saman Metadata --' in raw:
                current_sub = raw.split('--')[1].split('##')[0].strip()
                current_field = 'saman_metadata'
            elif 'End of ' in raw:
                current_field = ''
            continue

        if current_sub:
            if current_sub not in subs:
                subs[current_sub] = {
                    'parva': current_ss,
                    'kandah': current_sec,
                    'header': '',
                    'rik_metadata': '',
                    'saman_metadata': '',
                    'rik_text': '',
                    'mantra_sets': [],
                    'line_map': {}
                }
            if current_field == 'header':
                subs[current_sub]['header'] = raw
                subs[current_sub]['line_map']['Arsheyam Header'] = idx
            elif current_field == 'rik_metadata':
                subs[current_sub]['rik_metadata'] = raw
                subs[current_sub]['line_map']['Rik Metadata'] = idx
            elif current_field == 'saman_metadata':
                subs[current_sub]['saman_metadata'] = raw
                subs[current_sub]['line_map']['Saman Metadata'] = idx
            elif current_field == 'rik_text':
                if subs[current_sub]['rik_text']:
                    subs[current_sub]['rik_text'] += ' ' + raw
                else:
                    subs[current_sub]['rik_text'] = raw
                    subs[current_sub]['line_map']['Rik Text'] = idx
            elif current_field == 'mantra_sets':
                subs[current_sub]['mantra_sets'].append({'corrected-mantra': raw, 'line': idx})

    all_findings = []
    for sub_key, sdata in subs.items():
        sub_dict = {
            'header': {'header': sdata['header']},
            'rik_metadata': sdata['rik_metadata'],
            'saman_metadata': sdata['saman_metadata'],
            'rik_text': sdata['rik_text'],
            'corrected-mantra_sets': sdata['mantra_sets']
        }
        sub_findings = audit_subsection(sub_key, sub_dict, sdata['parva'], sdata['kandah'])
        for f in sub_findings:
            if f['field'] == 'Samam Chant':
                found_line = None
                for m in sdata['mantra_sets']:
                    clean_m = clean_swaras_for_sandhi(m['corrected-mantra'])
                    if f['suspect'] in clean_m or f['suspect'] in m['corrected-mantra']:
                        f['line_number'] = m['line']
                        f['context'] = m['corrected-mantra']
                        found_line = m['line']
                        break
                if not found_line and sdata['mantra_sets']:
                    f['line_number'] = sdata['mantra_sets'][0]['line']
            elif f['field'] == 'Rik Text':
                f['line_number'] = sdata['line_map'].get('Rik Text', 0)
                f['context'] = sdata['rik_text']
            elif f['field'] == 'Rik Metadata':
                f['line_number'] = sdata['line_map'].get('Rik Metadata', 0)
                f['context'] = sdata['rik_metadata']
            elif f['field'] == 'Arsheyam Header':
                f['line_number'] = sdata['line_map'].get('Arsheyam Header', 0)
                f['context'] = sdata['header']
            elif f['field'] == 'Saman Metadata':
                f['line_number'] = sdata['line_map'].get('Saman Metadata', 0)
                f['context'] = sdata['saman_metadata']
            else:
                f['line_number'] = sdata['line_map'].get(f['field'], 0)
        all_findings.extend(sub_findings)

    for i, f in enumerate(all_findings, 1):
        f['id'] = i
    return len(subs), all_findings

def run_sandhi_audit(json_path: Path, txt_path: Path = None):
    """Loads AST and runs comprehensive Sandhi audit across all subsections, mapping to Unicode text lines."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    line_index = build_txt_line_index(txt_path) if txt_path else {}
    supersections = data.get('supersections', data.get('supersection', {}))
    
    total_subsections = 0
    all_findings = []
    
    for ss_key, ss in supersections.items():
        if ss_key == 'count':
            continue
        parva_title = ss.get('supersection_title', ss_key)
        for sec_key, sec in ss.get('sections', {}).items():
            if sec_key == 'count':
                continue
            kandah_title = sec.get('section_title', sec_key)
            for sub_key, sub in sec.get('subsections', {}).items():
                total_subsections += 1
                sub_findings = audit_subsection(sub_key, sub, parva_title, kandah_title)
                for f in sub_findings:
                    f['line_number'] = line_index.get((sub_key, f['field']), 0)
                all_findings.extend(sub_findings)
                
    for i, f in enumerate(all_findings, 1):
        f['id'] = i
    return total_subsections, all_findings

STANDALONE_APPLY_SCRIPT_TEMPLATE = '''#!/usr/bin/env python3
"""
Standalone Python Apply Script for Selected Sanskrit Sandhi Corrections (Swara-Aware).
Generated dynamically from Sandhi Audit Report HTML Portal.
"""

import json
import re
import difflib
import shutil
from pathlib import Path
from datetime import datetime

PATCH_ITEMS = __PATCH_ITEMS_JSON__

def swara_aware_replace(text: str, sus: str, sug: str):
    if not sus or not sug or not text:
        return text, False
    if sus in text:
        return text.replace(sus, sug, 1), True
    swara_unit = r'(?:\\([^\\)]+\\)|[\\u1cd0-\\u1cf9\\u0951\\u0952\\s])*'
    pattern_parts = []
    for ch in sus.strip():
        if ch in ' ।॥':
            pattern_parts.append(r'[\\s।॥]*')
        else:
            pattern_parts.append(re.escape(ch) + swara_unit)
    pattern = ''.join(pattern_parts)
    m = re.search(pattern, text)
    if not m:
        return text, False
    matched_span = m.group(0)
    matcher = difflib.SequenceMatcher(None, sus, sug)
    opcodes = matcher.get_opcodes()
    new_span = matched_span
    success = False
    for tag, i1, i2, j1, j2 in reversed(opcodes):
        if tag in ('replace', 'delete', 'insert'):
            old_chunk = sus[i1:i2]
            new_chunk = sug[j1:j2]
            if old_chunk in new_span:
                new_span = new_span.replace(old_chunk, new_chunk, 1)
                success = True
            elif 'ं' in old_chunk and 'म्' in new_chunk:
                sub_span, n = re.subn(
                    r'([\\u0902])(\\s*(?:\\([^\\)]+\\)|[\\u1cd0-\\u1cf9\\u0951\\u0952])*([\\s।॥अआइईउऊऋएऐओऔ]))',
                    r'म् \\2',
                    new_span,
                    count=1
                )
                if n > 0:
                    new_span = sub_span
                    success = True
            elif 'ः' in old_chunk:
                sub_span, n = re.subn(
                    r'([^\\u093e\\u093f\\u0940\\u0941\\u0942\\u0943\\u0944\\u0947\\u0948\\u094b\\u094c\\s])ः\\s*',
                    r'\\1ो ',
                    new_span,
                    count=1
                )
                if n > 0:
                    new_span = sub_span
                    success = True
    if success:
        return text[:m.start()] + new_span + text[m.end():], True
    return text, False

def get_subsection_line_range(lines: list, sub_key: str):
    tag = f'-- {sub_key} '
    start_idx = None
    last_tag_idx = None
    for i, line in enumerate(lines):
        if tag in line:
            if start_idx is None:
                start_idx = i
            last_tag_idx = i
    if start_idx is None:
        return None, None
    end_idx = len(lines)
    for j in range(last_tag_idx + 1, len(lines)):
        if '-- subsection_' in lines[j] and tag not in lines[j]:
            end_idx = j
            break
    return start_idx, end_idx

def apply_patch():
    ast_path = Path("data/corpora/samhita/02_ast/Samhita_ast.json")
    out_ast_path = Path("data/corpora/samhita/02_ast/Samhita_ast.json")
    txt_path = Path("data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt")
    txt_sync_path = Path("data/input/Samhita_Devanagari_Unicode.txt")
    
    print(f"[INFO] Preparing to apply {len(PATCH_ITEMS)} selected Sandhi corrections (Swara-Aware)...")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if ast_path.exists():
        bak = ast_path.with_suffix(f".json.{ts}.bak")
        shutil.copy2(ast_path, bak)
        print(f"[BACKUP] Created {bak.name}")
    if txt_path.exists():
        tbak = txt_path.with_suffix(f".txt.{ts}.bak")
        shutil.copy2(txt_path, tbak)
        print(f"[BACKUP] Created {tbak.name}")
        
    with open(ast_path, "r", encoding="utf-8") as f:
        ast_data = json.load(f)
        
    txt_lines = txt_path.read_text(encoding="utf-8").splitlines() if txt_path.exists() else []
    applied_ast = 0
    applied_txt = 0
    
    for item in PATCH_ITEMS:
        sub_key = item.get("sub_key") or item.get("subsection")
        field = item.get("field")
        sus = item.get("suspect") or item.get("suspect_segment")
        sug = item.get("suggested") or item.get("suggested_sandhi")
        
        # 1. AST Search & Replace
        ast_done = False
        for ss in ast_data.get("supersections", ast_data.get("supersection", {})).values():
            if not isinstance(ss, dict): continue
            for sec in ss.get("sections", {}).values():
                if not isinstance(sec, dict): continue
                if sub_key in sec.get("subsections", {}):
                    sub = sec["subsections"][sub_key]
                    if field == "Arsheyam Header" and "header" in sub:
                        new_h, ok = swara_aware_replace(sub["header"].get("header", ""), sus, sug)
                        if ok:
                            sub["header"]["header"] = new_h
                            ast_done = True
                    elif field == "Rik Metadata":
                        new_rm, ok = swara_aware_replace(sub.get("rik_metadata", ""), sus, sug)
                        if ok:
                            sub["rik_metadata"] = new_rm
                            ast_done = True
                    elif field == "Rik Text":
                        new_rt, ok = swara_aware_replace(sub.get("rik_text", ""), sus, sug)
                        if ok:
                            sub["rik_text"] = new_rt
                            ast_done = True
                    elif field == "Saman Metadata":
                        new_sm, ok = swara_aware_replace(sub.get("saman_metadata", ""), sus, sug)
                        if ok:
                            sub["saman_metadata"] = new_sm
                            ast_done = True
                    elif field == "Samam Chant":
                        for m in sub.get("corrected-mantra_sets", sub.get("mantra_sets", [])):
                            new_cm, ok_cm = swara_aware_replace(m.get("corrected-mantra", ""), sus, sug)
                            if ok_cm:
                                m["corrected-mantra"] = new_cm
                                ast_done = True
                            new_m, ok_m = swara_aware_replace(m.get("mantra", ""), sus, sug)
                            if ok_m:
                                m["mantra"] = new_m
                                ast_done = True
        if ast_done:
            applied_ast += 1
            
        # 2. Unicode Text Search & Replace (Scoped to subsection line range)
        if txt_lines:
            s_idx, e_idx = get_subsection_line_range(txt_lines, sub_key)
            if s_idx is not None:
                sub_block = "\\n".join(txt_lines[s_idx:e_idx])
                new_block, ok_txt = swara_aware_replace(sub_block, sus, sug)
                if ok_txt:
                    new_lines = new_block.splitlines()
                    txt_lines = txt_lines[:s_idx] + new_lines + txt_lines[e_idx:]
                    applied_txt += 1
                    
    with open(ast_path, "w", encoding="utf-8") as f:
        json.dump(ast_data, f, ensure_ascii=False, indent=2)
    if out_ast_path.parent.exists():
        with open(out_ast_path, "w", encoding="utf-8") as f:
            json.dump(ast_data, f, ensure_ascii=False, indent=2)
    if txt_lines:
        final_txt = "\\n".join(txt_lines) + "\\n"
        txt_path.write_text(final_txt, encoding="utf-8")
        if txt_sync_path.parent.exists():
            txt_sync_path.write_text(final_txt, encoding="utf-8")
            
    print(f"[SUCCESS] Applied {applied_ast} AST replacements and {applied_txt} Unicode text replacements (Swara-Aware).")

if __name__ == "__main__":
    apply_patch()
'''

def generate_html_report(total_subs: int, findings: list, output_path: Path):
    """Generates an interactive HTML audit report with inbox-zero auto-hide triage workflow."""
    
    by_field = Counter(f['field'] for f in findings)
    by_sev = Counter(f['severity'] for f in findings)
    high_count = by_sev.get('High', 0)
    med_count = by_sev.get('Medium', 0)
    
    findings_json = json.dumps(findings, ensure_ascii=False)
    
    template = """<!DOCTYPE html>
<html lang="sa">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>सामसंहिता संस्कृत-सन्धि-परीक्षण-वृत्तान्तः (Sandhi Audit & Selection Portal)</title>
<style>
  :root {
    --maroon: #800000;
    --dark-maroon: #4a0000;
    --gold: #b8860b;
    --gold-light: #fef3c7;
    --navy: #1a365d;
    --cream: #fdfbf7;
    --border: #e2d9cc;
    --high-red: #c53030;
    --high-bg: #fff5f5;
    --high-border: #feb2b2;
    --med-amber: #b45309;
    --med-bg: #fffbeb;
    --med-border: #fde68a;
    --green: #15803d;
    --green-bg: #f0fdf4;
    --green-border: #86efac;
    --blue: #2563eb;
    --blue-bg: #eff6ff;
    --gray-bg: #f8fafc;
    --gray-border: #e2e8f0;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans Devanagari", "AdishilaVedic", sans-serif;
    background: #f6f4ee;
    color: #2d3748;
    line-height: 1.5;
    padding: 20px;
  }
  .container {
    max-width: 1560px;
    margin: 0 auto;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    overflow: hidden;
    border: 1px solid var(--border);
  }
  
  /* Header */
  header {
    background: linear-gradient(135deg, var(--maroon) 0%, var(--dark-maroon) 100%);
    color: #fff;
    padding: 26px 36px;
    border-bottom: 4px solid var(--gold);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
  }
  .header-left h1 {
    font-size: 26px;
    letter-spacing: 0.5px;
    margin-bottom: 5px;
    font-weight: 700;
  }
  .header-left p {
    color: #fbd38d;
    font-size: 14.5px;
  }
  .header-badges {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
  .header-badge {
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25);
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 12px;
    color: #fff;
    font-weight: 500;
  }
  
  /* KPI Cards */
  .kpi-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 14px;
    padding: 18px 36px;
    background: #faf8f5;
    border-bottom: 1px solid var(--border);
  }
  .kpi-card {
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 16px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.02);
  }
  .kpi-card.alert-info { border-left: 4px solid var(--navy); }
  .kpi-card.alert-pending { border-left: 4px solid #ea580c; background: #fffaf0; }
  .kpi-card.alert-selected { border-left: 4px solid var(--green); background: #f0fdf4; }
  .kpi-card.alert-postponed { border-left: 4px solid #d97706; background: #fffdf5; }
  .kpi-card.alert-high { border-left: 4px solid var(--high-red); }
  .kpi-card.alert-med { border-left: 4px solid var(--med-amber); }
  
  .kpi-label {
    font-size: 11px;
    text-transform: uppercase;
    color: #718096;
    letter-spacing: 0.5px;
    margin-bottom: 2px;
    font-weight: 600;
  }
  .kpi-value {
    font-size: 24px;
    font-weight: 700;
    color: #1a202c;
  }
  .kpi-card.alert-pending .kpi-value { color: #ea580c; }
  .kpi-card.alert-selected .kpi-value { color: var(--green); }
  .kpi-card.alert-postponed .kpi-value { color: #d97706; }
  .kpi-subtext {
    font-size: 11px;
    color: #a0aec0;
  }
  
  /* VIEW MODE TABS BAR */
  .view-mode-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 36px;
    background: #f8fafc;
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
    gap: 14px;
  }
  .view-mode-tabs {
    display: inline-flex;
    background: #e2e8f0;
    padding: 4px;
    border-radius: 8px;
    gap: 4px;
  }
  .view-mode-tab {
    background: transparent;
    border: none;
    padding: 8px 18px;
    border-radius: 6px;
    font-size: 13.5px;
    font-weight: 600;
    color: #475569;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    transition: all 0.15s ease;
  }
  .view-mode-tab:hover {
    color: #0f172a;
    background: rgba(255,255,255,0.6);
  }
  .view-mode-tab.active {
    background: #ffffff;
    color: var(--maroon);
    box-shadow: 0 1px 4px rgba(0,0,0,0.1);
  }
  .view-mode-tab.active.tab-green {
    color: var(--green);
  }
  .view-mode-tab.tab-amber {
    color: #b45309;
  }
  .view-mode-tab.active.tab-amber {
    color: #b45309;
  }
  .tab-badge {
    background: #cbd5e1;
    color: #334155;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 12px;
  }
  .view-mode-tab.active .tab-badge {
    background: var(--maroon);
    color: #ffffff;
  }
  .view-mode-tab.active.tab-green .tab-badge {
    background: var(--green);
    color: #ffffff;
  }
  .view-mode-tab.active.tab-amber .tab-badge {
    background: #d97706;
    color: #ffffff;
  }
  
  /* Auto-hide toggle switch */
  .auto-hide-control {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 13px;
    font-weight: 600;
    color: #334155;
    background: #fff;
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid #cbd5e1;
  }
  .toggle-switch {
    position: relative;
    display: inline-block;
    width: 36px;
    height: 20px;
  }
  .toggle-switch input { opacity: 0; width: 0; height: 0; }
  .slider {
    position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
    background-color: #cbd5e1;
    transition: .2s;
    border-radius: 20px;
  }
  .slider:before {
    position: absolute; content: ""; height: 14px; width: 14px; left: 3px; bottom: 3px;
    background-color: white;
    transition: .2s;
    border-radius: 50%;
  }
  input:checked + .slider { background-color: var(--green); }
  input:checked + .slider:before { transform: translateX(16px); }

  /* STICKY ACTION TOOLBAR */
  .selection-toolbar {
    position: sticky;
    top: 0;
    z-index: 100;
    background: #ffffff;
    border-bottom: 2px solid var(--maroon);
    padding: 10px 36px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
  }
  .toolbar-left {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }
  .quick-select-btn {
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    color: #334155;
    padding: 5px 11px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
  .quick-select-btn:hover {
    background: #e2e8f0;
    color: #0f172a;
  }
  .quick-select-btn.active {
    background: var(--maroon);
    color: #fff;
    border-color: var(--maroon);
  }
  
  .toolbar-right {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }
  .action-btn {
    padding: 6px 13px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    border: none;
  }
  .btn-primary-green { background: #16a34a; color: #fff; }
  .btn-primary-green:hover { background: #15803d; }
  .btn-primary-maroon { background: var(--maroon); color: #fff; }
  .btn-primary-maroon:hover { background: var(--dark-maroon); }
  .btn-secondary { background: #f8fafc; border: 1px solid #cbd5e1; color: #334155; }
  .btn-secondary:hover { background: #f1f5f9; }
  
  /* Filter & Search Bar */
  .filter-bar {
    padding: 12px 36px;
    background: #faf8f5;
    border-bottom: 1px solid var(--border);
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    align-items: center;
    justify-content: space-between;
  }
  .search-box {
    flex: 1;
    min-width: 280px;
    max-width: 440px;
    position: relative;
  }
  .search-box input {
    width: 100%;
    padding: 7px 14px;
    border: 1px solid #cbd5e0;
    border-radius: 6px;
    font-size: 13px;
    outline: none;
    transition: border-color 0.2s;
  }
  .search-box input:focus {
    border-color: var(--maroon);
    box-shadow: 0 0 0 3px rgba(128,0,0,0.1);
  }
  .filter-pills {
    display: flex;
    gap: 5px;
    flex-wrap: wrap;
    align-items: center;
  }
  .filter-pill {
    background: #fff;
    border: 1px solid #cbd5e1;
    color: #475569;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11.5px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s;
  }
  .filter-pill:hover { background: #f1f5f9; }
  .filter-pill.active {
    background: var(--maroon);
    color: #fff;
    border-color: var(--maroon);
  }
  
  /* Rule-based Bulk Triage Section & Matrix */
  .rule-matrix-card {
    background: #ffffff;
    border-bottom: 1px solid var(--border);
    padding: 14px 36px;
    transition: all 0.2s ease;
  }
  .rule-matrix-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    user-select: none;
    padding: 4px 0;
  }
  .rule-matrix-title {
    font-size: 13.5px;
    font-weight: 700;
    color: var(--maroon);
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .rule-matrix-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 12px;
    font-size: 12px;
  }
  .rule-matrix-table th {
    background: #f8fafc;
    padding: 7px 10px;
    border-bottom: 2px solid #cbd5e1;
    color: #475569;
    font-weight: 600;
  }
  .rule-matrix-table td {
    padding: 8px 10px;
    border-bottom: 1px solid #e2e8f0;
    vertical-align: middle;
  }
  .rule-matrix-table tr:hover {
    background: #fdfbf7;
  }
  .rule-count-pill {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 700;
  }
  .rule-pill-total { background: #e2e8f0; color: #334155; }
  .rule-pill-pending { background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }
  .rule-pill-selected { background: #f0fdf4; color: #166534; border: 1px solid #86efac; }
  .rule-pill-postponed { background: #fffdf5; color: #b45309; border: 1px solid #fde68a; }
  
  .btn-rule-action {
    padding: 4px 9px;
    border-radius: 5px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    border: 1px solid transparent;
    transition: all 0.15s;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
  }
  .btn-rule-select {
    background: #f0fdf4;
    border-color: #86efac;
    color: #166534;
  }
  .btn-rule-select:hover {
    background: #dcfce7;
  }
  .btn-rule-postpone {
    background: #fffbeb;
    border-color: #fde68a;
    color: #b45309;
  }
  .btn-rule-postpone:hover {
    background: #fef3c7;
    border-color: #fcd34d;
  }
  .btn-rule-reset {
    background: #f1f5f9;
    border-color: #cbd5e1;
    color: #475569;
  }
  .btn-rule-reset:hover {
    background: #e2e8f0;
  }
  .btn-rule-filter {
    background: #eff6ff;
    border-color: #bfdbfe;
    color: #1d4ed8;
  }
  .btn-rule-filter:hover {
    background: #dbeafe;
  }
  .btn-rule-action:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }
  
  /* Table View */
  .table-wrapper {
    overflow-x: auto;
    max-height: 700px;
    position: relative;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    text-align: left;
  }
  thead th {
    position: sticky;
    top: 0;
    background: #f1f5f9;
    color: #1e293b;
    font-weight: 600;
    padding: 10px 12px;
    border-bottom: 2px solid #cbd5e1;
    z-index: 10;
    white-space: nowrap;
  }
  tbody tr {
    border-bottom: 1px solid #e2e8f0;
    transition: background-color 0.15s;
  }
  tbody tr:hover { background: #f8fafc; }
  
  /* Selected Row Highlight */
  tbody tr.row-selected {
    background-color: #f0fdf4 !important;
    border-left: 4px solid var(--green) !important;
  }
  tbody tr.row-selected:hover {
    background-color: #dcfce7 !important;
  }
  
  /* Disappearing Row Animation for Auto-hide */
  tbody tr.row-disappearing {
    transition: all 0.22s ease-out;
    opacity: 0;
    transform: translateX(30px);
    background-color: #dcfce7 !important;
  }
  
  tbody td {
    padding: 10px 12px;
    vertical-align: top;
  }
  
  /* Checkboxes */
  input[type="checkbox"].row-checkbox {
    width: 17px;
    height: 17px;
    cursor: pointer;
    accent-color: var(--green);
  }
  input[type="checkbox"]#selectAllHeader {
    width: 17px;
    height: 17px;
    cursor: pointer;
    accent-color: var(--maroon);
  }
  
  /* Action Button inside row */
  .btn-row-action {
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    color: #334155;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
  }
  .btn-row-action:hover {
    background: #e2e8f0;
  }
  .btn-row-select {
    background: #f0fdf4;
    border-color: #86efac;
    color: var(--green);
  }
  .btn-row-select:hover {
    background: #dcfce7;
  }
  .btn-row-return {
    background: #fff7ed;
    border-color: #fed7aa;
    color: #c2410c;
  }
  .btn-row-return:hover {
    background: #ffedd5;
  }
  .btn-row-postpone {
    background: #fffbeb;
    border-color: #fde68a;
    color: #b45309;
  }
  .btn-row-postpone:hover {
    background: #fef3c7;
    border-color: #fcd34d;
  }
  .row-postponed {
    background-color: #fffdf5 !important;
  }
  
  /* Badges & Tags */
  .badge {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    white-space: nowrap;
  }
  .badge-high { background: var(--high-bg); color: var(--high-red); border: 1px solid var(--high-border); }
  .badge-med { background: var(--med-bg); color: var(--med-amber); border: 1px solid var(--med-border); }
  .badge-field { background: #e2e8f0; color: #334155; font-family: monospace; font-size: 11.5px; }
  
  .suspect-tag {
    display: inline-block;
    background: var(--high-bg);
    border: 1px solid var(--high-border);
    color: var(--high-red);
    padding: 2px 7px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 13.5px;
    word-break: break-all;
  }
  .suggested-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--green-bg);
    border: 1px solid var(--green-border);
    color: var(--green);
    padding: 2px 7px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 13.5px;
    word-break: break-all;
  }
  .customized-badge {
    font-size: 9px;
    background: var(--gold);
    color: #fff;
    padding: 1px 4px;
    border-radius: 3px;
    text-transform: uppercase;
  }
  .btn-edit-sug {
    background: transparent;
    border: none;
    cursor: pointer;
    font-size: 12px;
    opacity: 0.6;
    transition: opacity 0.15s;
  }
  .btn-edit-sug:hover { opacity: 1; }
  
  .btn-copy-chip {
    background: transparent;
    border: none;
    cursor: pointer;
    font-size: 11px;
    opacity: 0.55;
    margin-left: 3px;
    padding: 1px 3px;
    border-radius: 3px;
    transition: all 0.15s;
    vertical-align: middle;
  }
  .btn-copy-chip:hover {
    opacity: 1;
    background: rgba(0, 0, 0, 0.08);
  }
  
  .sutra-tag {
    font-size: 11px;
    color: #475569;
    background: #f1f5f9;
    padding: 1px 5px;
    border-radius: 4px;
    display: inline-block;
    margin-top: 3px;
  }
  .context-text {
    font-size: 12px;
    color: #475569;
    max-width: 320px;
    word-break: break-word;
  }
  .context-text mark {
    background: #fef08a;
    padding: 1px 2px;
    border-radius: 2px;
    font-weight: 700;
    color: #854d0e;
  }
  
  /* Empty State */
  .empty-state {
    text-align: center;
    padding: 60px 24px;
    color: #64748b;
  }
  .empty-state-icon {
    font-size: 42px;
    margin-bottom: 12px;
  }
  .empty-state-title {
    font-size: 18px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 6px;
  }
  .empty-state-desc {
    font-size: 13px;
    max-width: 480px;
    margin: 0 auto 16px auto;
  }
  
  /* Modal Dialog */
  .modal-overlay {
    display: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(4px);
    z-index: 999;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }
  .modal-overlay.open { display: flex; }
  .modal-container {
    background: #fff;
    border-radius: 12px;
    width: 100%;
    max-width: 1080px;
    max-height: 88vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 10px 40px rgba(0,0,0,0.25);
    overflow: hidden;
  }
  .modal-header {
    background: linear-gradient(135deg, var(--maroon) 0%, var(--dark-maroon) 100%);
    color: #fff;
    padding: 16px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 3px solid var(--gold);
  }
  .modal-header h3 { font-size: 18px; font-weight: 700; }
  .btn-close-modal {
    background: transparent;
    border: none;
    color: #fff;
    font-size: 20px;
    cursor: pointer;
    line-height: 1;
    opacity: 0.8;
  }
  .btn-close-modal:hover { opacity: 1; }
  .modal-body {
    padding: 20px 24px;
    overflow-y: auto;
    flex: 1;
  }
  .modal-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12.5px;
  }
  .modal-table th {
    background: #f1f5f9;
    padding: 8px 10px;
    border-bottom: 2px solid #cbd5e1;
    text-align: left;
  }
  .modal-table td {
    padding: 8px 10px;
    border-bottom: 1px solid #e2e8f0;
    vertical-align: middle;
  }
  .modal-edit-input {
    width: 100%;
    padding: 5px 8px;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    font-size: 13px;
    font-family: inherit;
    font-weight: 600;
    color: var(--green);
  }
  .modal-edit-input:focus {
    border-color: var(--green);
    outline: none;
    box-shadow: 0 0 0 2px rgba(22, 163, 74, 0.15);
  }
  .btn-remove-row {
    background: #fee2e2;
    border: 1px solid #fecaca;
    color: #dc2626;
    border-radius: 4px;
    padding: 3px 8px;
    cursor: pointer;
    font-size: 11px;
    font-weight: 600;
  }
  .btn-remove-row:hover { background: #fca5a5; }
  .modal-footer {
    padding: 14px 24px;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
  }
  
  /* Floating Action Dock */
  .floating-dock {
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: #1e293b;
    color: #fff;
    padding: 8px 16px;
    border-radius: 30px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.25);
    display: flex;
    align-items: center;
    gap: 10px;
    z-index: 90;
    transform: translateY(120px);
    transition: transform 0.25s ease;
  }
  .floating-dock.show { transform: translateY(0); }
  .dock-btn {
    background: var(--green);
    color: #fff;
    border: none;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
  }
  
  /* Toast Notification */
  .toast {
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%) translateY(100px);
    background: #0f172a;
    color: #fff;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    box-shadow: 0 4px 16px rgba(0,0,0,0.2);
    z-index: 1000;
    transition: transform 0.25s ease;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .toast.show { transform: translateX(-50%) translateY(0); }
  .toast-undo-btn {
    background: #3b82f6;
    border: none;
    color: #fff;
    padding: 3px 9px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 11.5px;
    font-weight: 700;
    margin-left: 6px;
  }
  .toast-undo-btn:hover { background: #2563eb; }
  
  footer {
    padding: 16px 36px;
    background: #f8fafc;
    color: #64748b;
    font-size: 12px;
    text-align: center;
    border-top: 1px solid var(--border);
  }
</style>
</head>
<body>

<div class="container">
  <header>
    <div class="header-left">
      <h1>॥ सामसंहिता संस्कृत-सन्धि-परीक्षण-वृत्तान्तः ॥</h1>
      <p>Interactive Sanskrit Sandhi Audit & Implementation Portal (Samhita Rik + Sāmam + Ārṣeyam)</p>
    </div>
    <div class="header-badges">
      <span class="header-badge">Pipeline v3.60</span>
      <span class="header-badge">722 Subsections</span>
      <span class="header-badge">AST Synchronized</span>
    </div>
  </header>
  
  <!-- KPI Metrics -->
  <div class="kpi-row">
    <div class="kpi-card alert-info">
      <div class="kpi-label">Subsections Audited</div>
      <div class="kpi-value">__TOTAL_SUBS__</div>
      <div class="kpi-subtext">Total Samhita Subsections</div>
    </div>
    <div class="kpi-card alert-pending">
      <div class="kpi-label">Pending Review</div>
      <div class="kpi-value" id="kpiPendingCount">__FINDINGS_COUNT__</div>
      <div class="kpi-subtext">Remaining to Review</div>
    </div>
    <div class="kpi-card alert-selected">
      <div class="kpi-label">Selected to Implement</div>
      <div class="kpi-value" id="kpiSelectedCount">0</div>
      <div class="kpi-subtext">Ready for Auto-Patching</div>
    </div>
    <div class="kpi-card alert-postponed">
      <div class="kpi-label">Postponed</div>
      <div class="kpi-value" id="kpiPostponedCount">0</div>
      <div class="kpi-subtext">Deferred for Review</div>
    </div>
    <div class="kpi-card alert-high">
      <div class="kpi-label">High Severity Cases</div>
      <div class="kpi-value">__HIGH_COUNT__</div>
      <div class="kpi-subtext">Grammatical Deviations</div>
    </div>
    <div class="kpi-card alert-med">
      <div class="kpi-label">Medium Severity Cases</div>
      <div class="kpi-value">__MED_COUNT__</div>
      <div class="kpi-subtext">Spacing & Anukramani Norms</div>
    </div>
  </div>

  <!-- VIEW MODE SEGMENTED BAR -->
  <div class="view-mode-bar">
    <div class="view-mode-tabs">
      <button class="view-mode-tab active" data-view="pending" id="tabPending">
        📥 Pending Review <span class="tab-badge" id="tabPendingCount">__FINDINGS_COUNT__</span>
      </button>
      <button class="view-mode-tab tab-green" data-view="selected" id="tabSelected">
        ✅ Selected to Implement <span class="tab-badge" id="tabSelectedCount">0</span>
      </button>
      <button class="view-mode-tab tab-amber" data-view="postponed" id="tabPostponed">
        ⏸️ Postponed <span class="tab-badge" id="tabPostponedCount">0</span>
      </button>
      <button class="view-mode-tab" data-view="all" id="tabAll">
        📋 All Cases <span class="tab-badge" id="tabAllCount">__FINDINGS_COUNT__</span>
      </button>
    </div>
    
    <div class="auto-hide-control">
      <label class="toggle-switch">
        <input type="checkbox" id="autoHideCheckbox" checked>
        <span class="slider"></span>
      </label>
      <span class="toggle-label" title="When enabled, selected items immediately slide off the Pending list">
        Auto-hide selected from view
      </span>
    </div>
  </div>

  <!-- STICKY ACTION & SELECTION TOOLBAR -->
  <div class="selection-toolbar">
    <div class="toolbar-left" id="toolbarLeft">
      <!-- Dynamic contextual buttons depending on view mode -->
    </div>
    
    <div class="toolbar-right">
      <button class="action-btn btn-primary-green" id="btnDownloadPatch" title="Download selected changes as JSON patch file">
        ⬇️ Download Patch JSON
      </button>
      <button class="action-btn btn-primary-maroon" id="btnDownloadScript" title="Download standalone python apply script">
        ⚡ Download Apply Script (.py)
      </button>
      <button class="action-btn btn-secondary" id="btnReviewModal" title="Review and edit selected changes">
        🔍 Review (<span id="btnReviewCount">0</span>)
      </button>
      <button class="action-btn btn-secondary" id="btnCopyJson" title="Copy patch JSON to clipboard">
        📋 Copy JSON
      </button>
      <button class="action-btn btn-secondary" id="btnPasteJson" title="Paste / import patch JSON to select items">
        📥 Paste JSON
      </button>
      <button class="action-btn btn-secondary" id="btnResetStorage" title="Clear saved selections in browser">
        ↺ Reset
      </button>
    </div>
  </div>

  <!-- Filter & Search Bar -->
  <div class="filter-bar">
    <div class="search-box">
      <input type="text" id="searchInput" placeholder="Search by subsection ID, text, rule, or context...">
    </div>
    
    <div style="display: flex; align-items: center; gap: 6px;">
      <span style="font-size: 12px; font-weight: 600; color: #64748b; white-space: nowrap;">Sandhi Rule:</span>
      <select id="ruleSelect" style="padding: 5px 10px; border-radius: 6px; border: 1px solid #cbd5e1; font-size: 12px; max-width: 360px; background: #fff; font-family: inherit; font-weight: 500; color: #1e293b; cursor: pointer;">
        <option value="all">All Sandhi Rules (__FINDINGS_COUNT__)</option>
      </select>
    </div>

    <!-- Active Rule Bulk Triage Strip (visible when a specific rule is active) -->
    <div id="ruleBulkActions" style="display: none; align-items: center; gap: 6px; background: #fdf6eb; padding: 4px 10px; border-radius: 6px; border: 1px solid #fed7aa;">
      <span style="font-size: 11.5px; font-weight: 700; color: #9a3412;">Rule Bulk Action:</span>
      <button class="btn-rule-action btn-rule-select" id="btnSelectActiveRule" onclick="selectCurrentRule()" title="Select all remaining cases of this rule to implement">
        ✅ Select All (<span id="ruleSelectCount">0</span>)
      </button>
      <button class="btn-rule-action btn-rule-postpone" id="btnPostponeActiveRule" onclick="postponeCurrentRule()" title="Postpone all remaining cases of this rule">
        ⏸️ Postpone All (<span id="rulePostponeCount">0</span>)
      </button>
      <button class="btn-rule-action btn-rule-reset" onclick="returnCurrentRuleToPending()" title="Return all cases of this rule to Pending">
        ↩️ Reset Rule
      </button>
    </div>
    
    <div class="filter-pills">
      <span style="font-size: 12px; font-weight: 600; color: #64748b; margin-right: 4px;">Field:</span>
      <button class="filter-pill active" data-filter="field" data-val="all">All</button>
      <button class="filter-pill" data-filter="field" data-val="Arsheyam Header">Ārṣeyam (__HEADER_COUNT__)</button>
      <button class="filter-pill" data-filter="field" data-val="Rik Text">Rik Text (__RIK_COUNT__)</button>
      <button class="filter-pill" data-filter="field" data-val="Samam Chant">Sāmam Chant (__SAMAM_COUNT__)</button>
      <button class="filter-pill" data-filter="field" data-val="Saman Metadata">Sāman Meta (__SMETA_COUNT__)</button>
      <button class="filter-pill" data-filter="field" data-val="Rik Metadata">Rik Meta (__RMETA_COUNT__)</button>
    </div>

    <div class="filter-pills">
      <span style="font-size: 12px; font-weight: 600; color: #64748b; margin-right: 4px;">Severity:</span>
      <button class="filter-pill active" data-filter="sev" data-val="all">All</button>
      <button class="filter-pill" data-filter="sev" data-val="High">High (__HIGH_COUNT__)</button>
      <button class="filter-pill" data-filter="sev" data-val="Medium">Medium (__MED_COUNT__)</button>
    </div>
    
    <div style="font-size: 12.5px; color: #64748b; font-weight: 500;" id="visibleResultsCount">
      Showing cases
    </div>
  </div>

  <!-- COLLAPSIBLE RULE-BASED TRIAGE MATRIX -->
  <div class="rule-matrix-card">
    <div class="rule-matrix-header" onclick="toggleRuleMatrix()">
      <div class="rule-matrix-title">
        <span id="matrixToggleIcon">▼</span>
        <span>⚖️ Rule-Based Bulk Triage Matrix (<span id="totalRulesCount">0</span> detected Paninian rules)</span>
      </div>
      <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 11.5px; color: #64748b;">
          Bulk select for patching or postpone entire rule lists in one click
        </span>
        <button class="btn-rule-action btn-rule-reset" style="padding: 2px 7px;" onclick="event.stopPropagation(); toggleRuleMatrix();">
          <span id="matrixToggleText">Hide</span>
        </button>
      </div>
    </div>
    <div id="ruleMatrixBody" style="display: block;">
      <table class="rule-matrix-table">
        <thead>
          <tr>
            <th style="width: 290px;">Paninian Rule Name</th>
            <th style="width: 230px;">Sutra / Authority</th>
            <th style="width: 65px; text-align: center;">Total</th>
            <th style="width: 75px; text-align: center;">Pending</th>
            <th style="width: 75px; text-align: center;">Selected</th>
            <th style="width: 75px; text-align: center;">Postponed</th>
            <th style="text-align: center;">Quick Bulk Action</th>
          </tr>
        </thead>
        <tbody id="ruleMatrixTableBody">
          <!-- Populated dynamically -->
        </tbody>
      </table>
    </div>
  </div>

  <!-- Interactive Table View -->
  <div class="table-wrapper">
    <table id="auditTable">
      <thead>
        <tr>
          <th style="width: 38px; text-align: center;">
            <input type="checkbox" id="selectAllHeader" title="Select / deselect all visible rows">
          </th>
          <th style="width: 38px;">#</th>
          <th style="width: 120px;">Subsection</th>
          <th style="width: 110px;">Field</th>
          <th style="width: 170px;">Suspect Segment</th>
          <th style="width: 220px;">Paninian Rule & Sutra</th>
          <th style="width: 210px;">Suggested Sandhi</th>
          <th style="width: 75px;">Severity</th>
          <th>Context & Explanation</th>
          <th style="width: 90px; text-align: center;">Action</th>
        </tr>
      </thead>
      <tbody id="tableBody">
        <!-- Rendered dynamically by JavaScript -->
      </tbody>
    </table>
    <div id="emptyStateContainer"></div>
  </div>
  
  <footer>
    Jaimineeya Samaveda Samhita — Sanskrit Sandhi Rule Audit & Selection System (Triage Mode)
  </footer>
</div>

<!-- REVIEW & CUSTOMIZE MODAL -->
<div class="modal-overlay" id="reviewModal">
  <div class="modal-container">
    <div class="modal-header">
      <h3>Review Selected Sandhi Changes (<span id="modalSelectedCount">0</span>)</h3>
      <button class="btn-close-modal" id="btnCloseModal">✕</button>
    </div>
    <div class="modal-body">
      <p style="font-size: 13px; color: #64748b; margin-bottom: 12px;">
        You can customize the suggested replacement directly in the editable text fields below before downloading or applying.
      </p>
      <table class="modal-table">
        <thead>
          <tr>
            <th style="width: 30px;">#</th>
            <th style="width: 110px;">Subsection</th>
            <th style="width: 100px;">Field</th>
            <th style="width: 160px;">Suspect (Original)</th>
            <th style="width: 220px;">Suggested Replacement (Editable)</th>
            <th>Context</th>
            <th style="width: 60px; text-align: center;">Remove</th>
          </tr>
        </thead>
        <tbody id="modalTableBody">
          <!-- Populated dynamically -->
        </tbody>
      </table>
    </div>
    <div class="modal-footer">
      <div style="font-size: 12px; color: #64748b;">
        CLI command: <code>python scripts/apply_sandhi_patch.py --patch sandhi_selected_patch.json</code>
      </div>
      <div style="display: flex; gap: 8px;">
        <button class="action-btn btn-primary-green" id="btnModalDownloadPatch">⬇️ Download Patch JSON</button>
        <button class="action-btn btn-primary-maroon" id="btnModalDownloadScript">⚡ Download Python Script</button>
        <button class="action-btn btn-secondary" id="btnModalCopyJson">📋 Copy JSON</button>
        <button class="action-btn btn-secondary" id="btnModalPasteJson">📥 Paste JSON</button>
        <button class="action-btn btn-secondary" id="btnModalClose">Close</button>
      </div>
    </div>
  </div>
</div>

<!-- FLOATING ACTION DOCK -->
<div class="floating-dock" id="floatingDock">
  <span id="dockSelectedCount">0</span> selected
  <button class="dock-btn" id="dockBtnReview">🔍 Review</button>
  <button class="dock-btn" id="dockBtnDownload" style="background: #2563eb;">⬇️ Download</button>
</div>

<!-- TOAST NOTIFICATION -->
<div class="toast" id="toastMessage">
  <span id="toastIcon">ℹ️</span>
  <span id="toastText">Action completed</span>
  <button class="toast-undo-btn" id="btnToastUndo" style="display:none;" onclick="undoLastAction()">Undo</button>
</div>

<script>
  // Complete Embedded Findings Dataset
  const FINDINGS = __FINDINGS_JSON__;
  
  // State
  let selectedIds = new Set();
  let postponedIds = new Set();
  let customReplacements = {};
  let activeViewMode = 'pending'; // 'pending', 'selected', 'postponed', or 'all'
  let autoHideEnabled = true;
  let activeField = 'all';
  let activeSev = 'all';
  let activeRule = 'all';
  let isMatrixCollapsed = false;
  let lastAction = null; // { type: 'select'|'deselect'|'postpone'|'unpostpone', id: number }
  
  // LocalStorage Persistence Keys
  const STORAGE_KEY_SELECTIONS = 'samhita_sandhi_selected_ids';
  const STORAGE_KEY_POSTPONED = 'samhita_sandhi_postponed_ids';
  const STORAGE_KEY_CUSTOM = 'samhita_sandhi_custom_replacements';
  const STORAGE_KEY_VIEW = 'samhita_sandhi_view_mode';
  const STORAGE_KEY_AUTOHIDE = 'samhita_sandhi_autohide';
  const STORAGE_KEY_RULE = 'samhita_sandhi_active_rule';
  const STORAGE_KEY_MATRIX_COLLAPSED = 'samhita_sandhi_matrix_collapsed';
  
  function initStorage() {
    try {
      const savedSel = localStorage.getItem(STORAGE_KEY_SELECTIONS);
      if (savedSel) {
        selectedIds = new Set(JSON.parse(savedSel));
      }
      const savedPost = localStorage.getItem(STORAGE_KEY_POSTPONED);
      if (savedPost) {
        postponedIds = new Set(JSON.parse(savedPost));
      }
      const savedCustom = localStorage.getItem(STORAGE_KEY_CUSTOM);
      if (savedCustom) {
        customReplacements = JSON.parse(savedCustom);
      }
      const savedView = localStorage.getItem(STORAGE_KEY_VIEW);
      if (savedView && ['pending', 'selected', 'postponed', 'all'].includes(savedView)) {
        activeViewMode = savedView;
      }
      const savedAutoHide = localStorage.getItem(STORAGE_KEY_AUTOHIDE);
      if (savedAutoHide !== null) {
        autoHideEnabled = (savedAutoHide === 'true');
      }
      const savedRule = localStorage.getItem(STORAGE_KEY_RULE);
      if (savedRule) {
        activeRule = savedRule;
      }
      const savedMatrixCollapsed = localStorage.getItem(STORAGE_KEY_MATRIX_COLLAPSED);
      if (savedMatrixCollapsed === 'true') {
        isMatrixCollapsed = true;
      }
    } catch(e) {
      console.warn('LocalStorage error:', e);
    }
  }
  
  function saveStorage() {
    try {
      localStorage.setItem(STORAGE_KEY_SELECTIONS, JSON.stringify(Array.from(selectedIds)));
      localStorage.setItem(STORAGE_KEY_POSTPONED, JSON.stringify(Array.from(postponedIds)));
      localStorage.setItem(STORAGE_KEY_CUSTOM, JSON.stringify(customReplacements));
      localStorage.setItem(STORAGE_KEY_VIEW, activeViewMode);
      localStorage.setItem(STORAGE_KEY_AUTOHIDE, autoHideEnabled.toString());
      localStorage.setItem(STORAGE_KEY_RULE, activeRule);
      localStorage.setItem(STORAGE_KEY_MATRIX_COLLAPSED, isMatrixCollapsed.toString());
    } catch(e) {
      console.warn('LocalStorage write error:', e);
    }
  }
  
  let toastTimer = null;
  function showToast(text, icon = 'ℹ️', showUndo = false) {
    const toast = document.getElementById('toastMessage');
    const undoBtn = document.getElementById('btnToastUndo');
    document.getElementById('toastText').innerText = text;
    document.getElementById('toastIcon').innerText = icon;
    
    if (showUndo) {
      undoBtn.style.display = 'inline-block';
    } else {
      undoBtn.style.display = 'none';
    }
    
    toast.classList.add('show');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 3500);
  }
  
  function undoLastAction() {
    if (!lastAction) return;
    if (lastAction.type === 'select') {
      selectedIds.delete(lastAction.id);
      showToast(`Undone: #${lastAction.id} restored to Pending`, '↩️');
    } else if (lastAction.type === 'deselect') {
      selectedIds.add(lastAction.id);
      showToast(`Undone: #${lastAction.id} restored to Selected`, '↩️');
    } else if (lastAction.type === 'postpone') {
      postponedIds.delete(lastAction.id);
      showToast(`Undone: #${lastAction.id} restored to Pending`, '↩️');
    } else if (lastAction.type === 'unpostpone') {
      postponedIds.add(lastAction.id);
      showToast(`Undone: #${lastAction.id} restored to Postponed`, '↩️');
    }
    lastAction = null;
    saveStorage();
    renderTable();
    updateStats();
  }
  
  function getEffectiveSuggested(f) {
    return customReplacements[f.id] !== undefined ? customReplacements[f.id] : f.suggested;
  }
  
  // Rule Matrix and Bulk Triage
  function toggleRuleMatrix() {
    isMatrixCollapsed = !isMatrixCollapsed;
    const body = document.getElementById('ruleMatrixBody');
    const icon = document.getElementById('matrixToggleIcon');
    const txt = document.getElementById('matrixToggleText');
    if (isMatrixCollapsed) {
      body.style.display = 'none';
      icon.innerText = '▶';
      txt.innerText = 'Show';
    } else {
      body.style.display = 'block';
      icon.innerText = '▼';
      txt.innerText = 'Hide';
    }
    saveStorage();
  }

  function getRuleStats() {
    const rulesMap = {};
    FINDINGS.forEach(f => {
      const r = f.rule_name;
      if (!rulesMap[r]) {
        rulesMap[r] = {
          name: r,
          sutra: f.sutra,
          severity: f.severity,
          total: 0,
          pending: 0,
          selected: 0,
          postponed: 0
        };
      }
      rulesMap[r].total++;
      if (selectedIds.has(f.id)) {
        rulesMap[r].selected++;
      } else if (postponedIds.has(f.id)) {
        rulesMap[r].postponed++;
      } else {
        rulesMap[r].pending++;
      }
    });
    return Object.values(rulesMap).sort((a, b) => b.total - a.total);
  }

  function populateRuleDropdownAndMatrix() {
    const rules = getRuleStats();
    const countEl = document.getElementById('totalRulesCount');
    if (countEl) countEl.innerText = rules.length;
    
    // 1. Populate Dropdown
    const select = document.getElementById('ruleSelect');
    if (select) {
      let selHtml = `<option value="all">All Sandhi Rules (${FINDINGS.length})</option>`;
      rules.forEach(r => {
        const isSel = (r.name === activeRule) ? 'selected' : '';
        selHtml += `<option value="${r.name.replace(/"/g, '&quot;')}" ${isSel}>${r.name} (${r.total}) — ${r.pending} pending</option>`;
      });
      select.innerHTML = selHtml;
    }
    
    // 2. Populate Matrix Table
    const tbody = document.getElementById('ruleMatrixTableBody');
    if (tbody) {
      let matHtml = '';
      rules.forEach(r => {
        const rEsc = r.name.replace(/'/g, "\\'");
        const isActive = (r.name === activeRule);
        matHtml += `
          <tr style="${isActive ? 'background: #fef9c3 !important;' : ''}">
            <td>
              <strong>${r.name}</strong>
            </td>
            <td><span class="sutra-tag">${r.sutra}</span></td>
            <td style="text-align: center;"><span class="rule-count-pill rule-pill-total">${r.total}</span></td>
            <td style="text-align: center;"><span class="rule-count-pill rule-pill-pending">${r.pending}</span></td>
            <td style="text-align: center;"><span class="rule-count-pill rule-pill-selected">${r.selected}</span></td>
            <td style="text-align: center;"><span class="rule-count-pill rule-pill-postponed">${r.postponed}</span></td>
            <td style="text-align: center;">
              <div style="display: inline-flex; gap: 4px; align-items: center;">
                <button class="btn-rule-action btn-rule-filter" onclick="filterByRule('${rEsc}')" title="Filter view to this rule">
                  ${isActive ? '✓ Filtering' : '🔍 Filter'}
                </button>
                <button class="btn-rule-action btn-rule-select" onclick="selectRuleMatches('${rEsc}')" ${r.pending === 0 ? 'disabled' : ''} title="Select all pending cases of this rule to implement">
                  ✅ Select All (${r.pending})
                </button>
                <button class="btn-rule-action btn-rule-postpone" onclick="postponeRuleMatches('${rEsc}')" ${r.pending === 0 ? 'disabled' : ''} title="Postpone all pending cases of this rule for later review">
                  ⏸️ Postpone All (${r.pending})
                </button>
                <button class="btn-rule-action btn-rule-reset" onclick="returnRuleMatchesToPending('${rEsc}')" ${(r.selected === 0 && r.postponed === 0) ? 'disabled' : ''} title="Return all cases of this rule to Pending">
                  ↩️ Reset
                </button>
              </div>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = matHtml;
    }
    
    updateActiveRuleBar();
  }

  function updateActiveRuleBar() {
    const strip = document.getElementById('ruleBulkActions');
    if (!strip) return;
    if (activeRule === 'all') {
      strip.style.display = 'none';
      return;
    }
    const matching = FINDINGS.filter(f => f.rule_name === activeRule);
    const pendingCount = matching.filter(f => !selectedIds.has(f.id) && !postponedIds.has(f.id)).length;
    const selEl = document.getElementById('ruleSelectCount');
    const postEl = document.getElementById('rulePostponeCount');
    if (selEl) selEl.innerText = pendingCount;
    if (postEl) postEl.innerText = pendingCount;
    strip.style.display = 'inline-flex';
  }

  function filterByRule(ruleName) {
    if (activeRule === ruleName) {
      activeRule = 'all'; // toggle back
    } else {
      activeRule = ruleName;
    }
    const select = document.getElementById('ruleSelect');
    if (select) select.value = activeRule;
    saveStorage();
    renderTable();
    populateRuleDropdownAndMatrix();
  }

  function selectCurrentRule() {
    if (activeRule === 'all') return;
    selectRuleMatches(activeRule);
  }

  function postponeCurrentRule() {
    if (activeRule === 'all') return;
    postponeRuleMatches(activeRule);
  }

  function returnCurrentRuleToPending() {
    if (activeRule === 'all') return;
    returnRuleMatchesToPending(activeRule);
  }

  function selectRuleMatches(ruleName) {
    const matches = FINDINGS.filter(f => f.rule_name === ruleName && !selectedIds.has(f.id));
    matches.forEach(f => {
      selectedIds.add(f.id);
      postponedIds.delete(f.id);
    });
    saveStorage();
    renderTable();
    updateStats();
    populateRuleDropdownAndMatrix();
    showToast(`Selected ${matches.length} cases for "${ruleName}" to implement`, '✅');
  }

  function postponeRuleMatches(ruleName) {
    const matches = FINDINGS.filter(f => f.rule_name === ruleName && !postponedIds.has(f.id));
    matches.forEach(f => {
      postponedIds.add(f.id);
      selectedIds.delete(f.id);
    });
    saveStorage();
    renderTable();
    updateStats();
    populateRuleDropdownAndMatrix();
    showToast(`Postponed ${matches.length} cases for "${ruleName}" for later review`, '⏸️');
  }

  function returnRuleMatchesToPending(ruleName) {
    const matches = FINDINGS.filter(f => f.rule_name === ruleName && (selectedIds.has(f.id) || postponedIds.has(f.id)));
    matches.forEach(f => {
      selectedIds.delete(f.id);
      postponedIds.delete(f.id);
    });
    saveStorage();
    renderTable();
    updateStats();
    populateRuleDropdownAndMatrix();
    showToast(`Returned ${matches.length} cases of "${ruleName}" to Pending`, '↩️');
  }
  
  function updateToolbarButtons() {
    const left = document.getElementById('toolbarLeft');
    let html = '';
    
    if (activeViewMode === 'pending') {
      const remainingHigh = FINDINGS.filter(f => !selectedIds.has(f.id) && !postponedIds.has(f.id) && f.severity === 'High').length;
      const remainingHeaders = FINDINGS.filter(f => !selectedIds.has(f.id) && !postponedIds.has(f.id) && f.field === 'Arsheyam Header').length;
      const remainingRik = FINDINGS.filter(f => !selectedIds.has(f.id) && !postponedIds.has(f.id) && f.field === 'Rik Text').length;
      
      let ruleButtons = '';
      if (activeRule !== 'all') {
        const ruleMatches = FINDINGS.filter(f => f.rule_name === activeRule);
        const rulePending = ruleMatches.filter(f => !selectedIds.has(f.id) && !postponedIds.has(f.id)).length;
        ruleButtons = `
          <button class="quick-select-btn" style="background:#f0fdf4; border-color:#86efac; color:#166534;" onclick="selectCurrentRule()" title="Select all pending cases of active rule for patching">✅ Select Rule (${rulePending})</button>
          <button class="quick-select-btn" style="background:#fffbeb; border-color:#fde68a; color:#b45309;" onclick="postponeCurrentRule()" title="Postpone all pending cases of active rule">⏸️ Postpone Rule (${rulePending})</button>
        `;
      }
      
      html = `
        <button class="quick-select-btn" id="btnSelectVisible" onclick="selectAllVisible()" title="Select all visible pending items">☑️ Select Visible</button>
        <button class="quick-select-btn" onclick="postponeAllVisible()" title="Postpone all visible pending items for later review">⏸️ Postpone Visible</button>
        ${ruleButtons}
        <button class="quick-select-btn" onclick="selectHighSeverity()" title="Select all remaining High severity cases">🔥 Select High (${remainingHigh})</button>
        <button class="quick-select-btn" onclick="selectField('Arsheyam Header')" title="Select all remaining Ārṣeyam headers">📜 Select Ārṣeyam (${remainingHeaders})</button>
        <button class="quick-select-btn" onclick="selectField('Rik Text')" title="Select all remaining Rik text cases">📖 Select Rik (${remainingRik})</button>
        <button class="quick-select-btn" onclick="clearAll()" title="Clear all selections & return to Pending">🗑️ Clear All</button>
      `;
    } else if (activeViewMode === 'selected') {
      html = `
        <button class="quick-select-btn" onclick="deselectAllVisible()" title="Move all visible selected items back to Pending">⬜ Return Visible to Pending</button>
        <button class="quick-select-btn" onclick="postponeSelectedVisible()" title="Move visible selected items to Postponed">⏸️ Postpone Visible</button>
        <button class="quick-select-btn" onclick="clearAllSelected()" title="Return all selected items to Pending">🗑️ Return All to Pending</button>
      `;
    } else if (activeViewMode === 'postponed') {
      html = `
        <button class="quick-select-btn" onclick="selectAllPostponedVisible()" title="Move visible postponed items to Selected to implement">✅ Select Visible</button>
        <button class="quick-select-btn" onclick="returnVisiblePostponedToPending()" title="Move visible postponed items back to Pending">⬜ Return Visible to Pending</button>
        <button class="quick-select-btn" onclick="returnAllPostponedToPending()" title="Move all postponed items back to Pending">↩️ Return All to Pending</button>
      `;
    } else { // 'all'
      html = `
        <button class="quick-select-btn" onclick="selectAllVisible()" title="Select all visible items">☑️ Select Visible</button>
        <button class="quick-select-btn" onclick="postponeAllVisible()" title="Postpone all visible items">⏸️ Postpone Visible</button>
        <button class="quick-select-btn" onclick="deselectAllVisible()" title="Deselect visible items to Pending">⬜ Return to Pending</button>
        <button class="quick-select-btn" onclick="clearAll()" title="Clear all selections and postponements">🗑️ Clear All</button>
      `;
    }
    
    left.innerHTML = html;
  }
  
  function renderTable() {
    const tbody = document.getElementById('tableBody');
    const emptyContainer = document.getElementById('emptyStateContainer');
    const query = document.getElementById('searchInput').value.toLowerCase().trim();
    let visibleCount = 0;
    
    let html = '';
    
    FINDINGS.forEach(f => {
      const isSelected = selectedIds.has(f.id);
      const isPostponed = postponedIds.has(f.id);
      
      // View Mode Filtering:
      if (activeViewMode === 'pending' && (isSelected || isPostponed)) return;
      if (activeViewMode === 'selected' && !isSelected) return;
      if (activeViewMode === 'postponed' && !isPostponed) return;
      
      // Category Filters:
      if (activeField !== 'all' && f.field !== activeField) return;
      if (activeSev !== 'all' && f.severity !== activeSev) return;
      if (activeRule !== 'all' && f.rule_name !== activeRule) return;
      
      // Query search:
      if (query) {
        const fullText = (f.sub_key + ' ' + f.parva + ' ' + f.kandah + ' ' + f.field + ' ' + f.suspect + ' ' + f.suggested + ' ' + f.rule_name + ' ' + f.sutra + ' ' + f.context + ' ' + f.explanation).toLowerCase();
        if (!fullText.includes(query)) return;
      }
      
      visibleCount++;
      const isCustom = customReplacements[f.id] !== undefined;
      const effectiveSug = getEffectiveSuggested(f);
      const sevClass = f.severity === 'High' ? 'badge-high' : 'badge-med';
      
      // Highlight suspect in context
      let ctx = f.context;
      const sus = f.suspect.trim();
      if (sus && ctx.includes(sus)) {
        ctx = ctx.replace(sus, `<mark>${sus}</mark>`);
      }
      
      // Action button based on current view
      let actionBtn = '';
      if (activeViewMode === 'pending') {
        actionBtn = `
          <div style="display: inline-flex; gap: 4px; align-items: center;">
            <button class="btn-row-action btn-row-select" onclick="event.stopPropagation(); toggleSelect(${f.id}, true, true);" title="Select this change to implement">✓ Select</button>
            <button class="btn-row-action btn-row-postpone" onclick="event.stopPropagation(); togglePostpone(${f.id}, true, true);" title="Postpone this case for later review">⏸️ Postpone</button>
          </div>
        `;
      } else if (activeViewMode === 'selected') {
        actionBtn = `
          <div style="display: inline-flex; gap: 4px; align-items: center;">
            <button class="btn-row-action btn-row-return" onclick="event.stopPropagation(); toggleSelect(${f.id}, false, true);" title="Return this item to Pending">✕ Return</button>
            <button class="btn-row-action btn-row-postpone" onclick="event.stopPropagation(); togglePostpone(${f.id}, true, true);" title="Move to Postponed">⏸️ Postpone</button>
          </div>
        `;
      } else if (activeViewMode === 'postponed') {
        actionBtn = `
          <div style="display: inline-flex; gap: 4px; align-items: center;">
            <button class="btn-row-action btn-row-return" onclick="event.stopPropagation(); togglePostpone(${f.id}, false, true);" title="Return this item to Pending">↩️ Pending</button>
            <button class="btn-row-action btn-row-select" onclick="event.stopPropagation(); toggleSelect(${f.id}, true, true);" title="Select this item to implement">✓ Select</button>
          </div>
        `;
      } else {
        let statusBadge = '';
        if (isSelected) {
          statusBadge = `<span class="badge" style="background:#dcfce7;color:#166534;font-size:10px;margin-bottom:2px;display:inline-block;">Selected</span>`;
        } else if (isPostponed) {
          statusBadge = `<span class="badge" style="background:#fef3c7;color:#92400e;font-size:10px;margin-bottom:2px;display:inline-block;">Postponed</span>`;
        } else {
          statusBadge = `<span class="badge" style="background:#f1f5f9;color:#475569;font-size:10px;margin-bottom:2px;display:inline-block;">Pending</span>`;
        }
        actionBtn = `
          <div style="display: inline-flex; flex-direction: column; align-items: center; gap: 3px;">
            ${statusBadge}
            <div style="display: inline-flex; gap: 3px;">
              ${!isSelected ? `<button class="btn-row-action btn-row-select" onclick="event.stopPropagation(); toggleSelect(${f.id}, true, false);" title="Select">✓</button>` : ''}
              ${!isPostponed ? `<button class="btn-row-action btn-row-postpone" onclick="event.stopPropagation(); togglePostpone(${f.id}, true, false);" title="Postpone">⏸️</button>` : ''}
              ${(isSelected || isPostponed) ? `<button class="btn-row-action btn-row-return" onclick="event.stopPropagation(); toggleSelect(${f.id}, false); togglePostpone(${f.id}, false);" title="Return to Pending">↩️</button>` : ''}
            </div>
          </div>
        `;
      }
      
      html += `
        <tr class="${isSelected ? 'row-selected' : (isPostponed ? 'row-postponed' : '')}" data-id="${f.id}">
          <td style="text-align: center; cursor: pointer;" onclick="toggleRowCheckbox(${f.id}, event);" title="Click to toggle selection">
            <input type="checkbox" class="row-checkbox" data-id="${f.id}" ${isSelected ? 'checked' : ''} onclick="event.stopPropagation();" onchange="toggleSelect(${f.id}, this.checked, false)">
          </td>
          <td style="user-select: text;">${f.id}</td>
          <td style="user-select: text;">
            <strong><code>${f.sub_key}</code></strong>
            ${f.line_number ? `<span style="display: inline-block; margin-left: 4px; padding: 1px 5px; background: #e0e7ff; color: #3730a3; border-radius: 4px; font-size: 11px; font-weight: 600;" title="Line ${f.line_number} in Samhita_Devanagari_Unicode.txt">L${f.line_number}</span>` : ''}<br>
            <span style="font-size: 11px; color: #64748b;">${f.parva} — ${f.kandah}</span>
          </td>
          <td><span class="badge badge-field">${f.field}</span></td>
          <td style="user-select: text;">
            <span class="suspect-tag">
              <span>${f.suspect}</span>
              <button class="btn-copy-chip" onclick="event.stopPropagation(); copyTextToClipboard('${f.suspect.replace(/'/g, "\\'")}', 'Copied suspect: ${f.suspect.replace(/'/g, "\\'")}', '📋');" title="Copy suspect text">📋</button>
            </span>
          </td>
          <td style="user-select: text;">
            <strong>${f.rule_name}</strong><br>
            <span class="sutra-tag">${f.sutra}</span>
          </td>
          <td style="user-select: text;">
            <span class="suggested-tag">
              <span id="sugText-${f.id}">${effectiveSug}</span>
              <button class="btn-copy-chip" onclick="event.stopPropagation(); copyTextToClipboard('${effectiveSug.replace(/'/g, "\\'")}', 'Copied suggested: ${effectiveSug.replace(/'/g, "\\'")}', '📋');" title="Copy suggested text">📋</button>
              ${isCustom ? '<span class="customized-badge">custom</span>' : ''}
              <button class="btn-edit-sug" onclick="promptEdit(${f.id}, event)" title="Edit suggested sandhi">✏️</button>
            </span>
          </td>
          <td><span class="badge ${sevClass}">${f.severity}</span></td>
          <td style="user-select: text;">
            <div class="context-text" style="user-select: text;">${ctx}</div>
            <div style="font-size: 11px; color: #64748b; margin-top: 3px; user-select: text;">${f.explanation}</div>
          </td>
          <td style="text-align: center;">
            ${actionBtn}
          </td>
        </tr>
      `;
    });
    
    tbody.innerHTML = html;
    
    // Empty state handling
    if (visibleCount === 0) {
      document.getElementById('auditTable').style.display = 'none';
      if (activeViewMode === 'pending') {
        const totalPending = FINDINGS.length - selectedIds.size - postponedIds.size;
        if (totalPending === 0) {
          emptyContainer.innerHTML = `
            <div class="empty-state">
              <div class="empty-state-icon">🎉</div>
              <div class="empty-state-title">All Cases Triaged!</div>
              <div class="empty-state-desc">All ${FINDINGS.length} cases have been triaged: <strong>${selectedIds.size}</strong> selected to implement, and <strong>${postponedIds.size}</strong> postponed for later review. Switch to <strong>"Selected to Implement"</strong> to review and download your patch script.</div>
              <div style="display:inline-flex; gap: 10px; margin-top: 14px;">
                <button class="action-btn btn-primary-green" onclick="setViewMode('selected')">Go to Selected (${selectedIds.size})</button>
                <button class="action-btn btn-primary-maroon" onclick="setViewMode('postponed')">Go to Postponed (${postponedIds.size})</button>
              </div>
            </div>
          `;
        } else {
          emptyContainer.innerHTML = `
            <div class="empty-state">
              <div class="empty-state-icon">🔍</div>
              <div class="empty-state-title">No Matching Pending Cases</div>
              <div class="empty-state-desc">No pending cases match your search or filter criteria.</div>
            </div>
          `;
        }
      } else if (activeViewMode === 'selected') {
        emptyContainer.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">📥</div>
            <div class="empty-state-title">No Changes Selected Yet</div>
            <div class="empty-state-desc">Select items from the <strong>"Pending Review"</strong> tab to stage them for implementation.</div>
            <button class="action-btn btn-primary-maroon" onclick="setViewMode('pending')">Go to Pending Review</button>
          </div>
        `;
      } else if (activeViewMode === 'postponed') {
        emptyContainer.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">⏸️</div>
            <div class="empty-state-title">No Postponed Cases</div>
            <div class="empty-state-desc">You have not postponed any cases. When reviewing cases in the <strong>"Pending Review"</strong> tab, click <strong>"⏸️ Postpone"</strong> to defer items you want to consult on or review later.</div>
            <button class="action-btn btn-primary-maroon" onclick="setViewMode('pending')">Go to Pending Review</button>
          </div>
        `;
      } else {
        emptyContainer.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">🔍</div>
            <div class="empty-state-title">No Results Found</div>
            <div class="empty-state-desc">Try clearing your search query or field filters.</div>
          </div>
        `;
      }
    } else {
      document.getElementById('auditTable').style.display = '';
      emptyContainer.innerHTML = '';
    }
    
    document.getElementById('visibleResultsCount').innerText = `Showing ${visibleCount} case${visibleCount === 1 ? '' : 's'}`;
    updateMasterHeaderCheckbox();
    updateToolbarButtons();
  }
  
  function updateStats() {
    const selCount = selectedIds.size;
    const postCount = postponedIds.size;
    const pendCount = FINDINGS.length - selCount - postCount;
    
    document.getElementById('kpiPendingCount').innerText = pendCount;
    document.getElementById('kpiSelectedCount').innerText = selCount;
    if (document.getElementById('kpiPostponedCount')) {
      document.getElementById('kpiPostponedCount').innerText = postCount;
    }
    
    document.getElementById('tabPendingCount').innerText = pendCount;
    document.getElementById('tabSelectedCount').innerText = selCount;
    if (document.getElementById('tabPostponedCount')) {
      document.getElementById('tabPostponedCount').innerText = postCount;
    }
    document.getElementById('tabAllCount').innerText = FINDINGS.length;
    
    document.getElementById('btnReviewCount').innerText = selCount;
    document.getElementById('dockSelectedCount').innerText = selCount;
    document.getElementById('modalSelectedCount').innerText = selCount;
    
    // Toggle floating dock visibility
    const dock = document.getElementById('floatingDock');
    if (window.scrollY > 250 && selCount > 0) {
      dock.classList.add('show');
    } else {
      dock.classList.remove('show');
    }
    
    saveStorage();
  }
  
  function updateMasterHeaderCheckbox() {
    const visibleCheckboxes = document.querySelectorAll('.row-checkbox');
    const headerCheckbox = document.getElementById('selectAllHeader');
    if (visibleCheckboxes.length === 0) {
      headerCheckbox.checked = false;
      headerCheckbox.indeterminate = false;
      return;
    }
    let checkedCount = 0;
    visibleCheckboxes.forEach(cb => { if (cb.checked) checkedCount++; });
    if (checkedCount === 0) {
      headerCheckbox.checked = false;
      headerCheckbox.indeterminate = false;
    } else if (checkedCount === visibleCheckboxes.length) {
      headerCheckbox.checked = true;
      headerCheckbox.indeterminate = false;
    } else {
      headerCheckbox.checked = false;
      headerCheckbox.indeterminate = true;
    }
  }
  
  function toggleSelect(id, checked, isDirectAction = false) {
    if (checked) {
      selectedIds.add(id);
      postponedIds.delete(id);
      lastAction = { type: 'select', id: id };
      
      // AUTO-HIDE BEHAVIOR: if in pending mode and auto-hide is enabled, animate off view
      if (activeViewMode === 'pending' && autoHideEnabled) {
        const row = document.querySelector(`tr[data-id="${id}"]`);
        if (row) {
          row.classList.add('row-disappearing');
          setTimeout(() => {
            renderTable();
            updateStats();
          }, 180);
        } else {
          renderTable();
          updateStats();
        }
        showToast(`Selected #${id} (moved off view into Selected queue)`, '✅', true);
        return;
      }
    } else {
      selectedIds.delete(id);
      lastAction = { type: 'deselect', id: id };
      
      if (activeViewMode === 'selected') {
        const row = document.querySelector(`tr[data-id="${id}"]`);
        if (row) {
          row.classList.add('row-disappearing');
          setTimeout(() => {
            renderTable();
            updateStats();
          }, 180);
        } else {
          renderTable();
          updateStats();
        }
        showToast(`Returned #${id} to Pending queue`, '↩️', true);
        return;
      }
    }
    
    const row = document.querySelector(`tr[data-id="${id}"]`);
    if (row) {
      if (checked) row.classList.add('row-selected');
      else row.classList.remove('row-selected');
    }
    updateStats();
    updateMasterHeaderCheckbox();
  }

  function togglePostpone(id, postpone, isDirectAction = false) {
    if (postpone) {
      postponedIds.add(id);
      selectedIds.delete(id);
      lastAction = { type: 'postpone', id: id };
      
      if ((activeViewMode === 'pending' || activeViewMode === 'selected') && autoHideEnabled) {
        const row = document.querySelector(`tr[data-id="${id}"]`);
        if (row) {
          row.classList.add('row-disappearing');
          setTimeout(() => {
            renderTable();
            updateStats();
          }, 180);
        } else {
          renderTable();
          updateStats();
        }
        showToast(`Postponed #${id} (deferred for later review)`, '⏸️', true);
        return;
      }
    } else {
      postponedIds.delete(id);
      lastAction = { type: 'unpostpone', id: id };
      
      if (activeViewMode === 'postponed') {
        const row = document.querySelector(`tr[data-id="${id}"]`);
        if (row) {
          row.classList.add('row-disappearing');
          setTimeout(() => {
            renderTable();
            updateStats();
          }, 180);
        } else {
          renderTable();
          updateStats();
        }
        showToast(`Returned #${id} to Pending queue`, '↩️', true);
        return;
      }
    }
    
    renderTable();
    updateStats();
  }

  function postponeAllVisible() {
    const visibleRows = document.querySelectorAll('#tableBody tr');
    let count = 0;
    visibleRows.forEach(row => {
      const id = parseInt(row.getAttribute('data-id'), 10);
      if (id) {
        postponedIds.add(id);
        selectedIds.delete(id);
        count++;
      }
    });
    renderTable();
    updateStats();
    showToast(`Postponed ${count} visible items`, '⏸️');
  }

  function postponeSelectedVisible() {
    const visibleRows = document.querySelectorAll('#tableBody tr');
    let count = 0;
    visibleRows.forEach(row => {
      const id = parseInt(row.getAttribute('data-id'), 10);
      if (id && selectedIds.has(id)) {
        selectedIds.delete(id);
        postponedIds.add(id);
        count++;
      }
    });
    renderTable();
    updateStats();
    showToast(`Postponed ${count} selected items`, '⏸️');
  }

  function selectAllPostponedVisible() {
    const visibleRows = document.querySelectorAll('#tableBody tr');
    let count = 0;
    visibleRows.forEach(row => {
      const id = parseInt(row.getAttribute('data-id'), 10);
      if (id) {
        postponedIds.delete(id);
        selectedIds.add(id);
        count++;
      }
    });
    renderTable();
    updateStats();
    showToast(`Selected ${count} postponed items to implement`, '✅');
  }

  function returnAllPostponedToPending() {
    if (confirm('Return all postponed cases back to the Pending Review queue?')) {
      const count = postponedIds.size;
      postponedIds.clear();
      renderTable();
      updateStats();
      showToast(`Returned ${count} postponed cases to Pending`, '↩️');
    }
  }

  function returnVisiblePostponedToPending() {
    const visibleRows = document.querySelectorAll('#tableBody tr');
    let count = 0;
    visibleRows.forEach(row => {
      const id = parseInt(row.getAttribute('data-id'), 10);
      if (id && postponedIds.has(id)) {
        postponedIds.delete(id);
        count++;
      }
    });
    renderTable();
    updateStats();
    showToast(`Returned ${count} items to Pending`, '↩️');
  }

  function clearAllSelected() {
    if (confirm('Return all selected cases to Pending?')) {
      selectedIds.clear();
      renderTable();
      updateStats();
      showToast(`All selected cases returned to Pending`, '🗑️');
    }
  }
  
  function toggleRowCheckbox(id, event) {
    if (event && event.target && event.target.tagName === 'INPUT') return;
    const isCurrently = selectedIds.has(id);
    toggleSelect(id, !isCurrently, false);
  }
  
  function selectAllVisible() {
    const visibleCheckboxes = document.querySelectorAll('.row-checkbox');
    let count = 0;
    visibleCheckboxes.forEach(cb => {
      const id = parseInt(cb.getAttribute('data-id'), 10);
      selectedIds.add(id);
      postponedIds.delete(id);
      count++;
    });
    renderTable();
    updateStats();
    showToast(`Selected ${count} visible items`, '☑️');
  }
  
  function deselectAllVisible() {
    const visibleCheckboxes = document.querySelectorAll('.row-checkbox');
    let count = 0;
    visibleCheckboxes.forEach(cb => {
      const id = parseInt(cb.getAttribute('data-id'), 10);
      selectedIds.delete(id);
      count++;
    });
    renderTable();
    updateStats();
    showToast(`Deselected ${count} visible items`, '⬜');
  }
  
  function selectHighSeverity() {
    const pendingHigh = FINDINGS.filter(f => !selectedIds.has(f.id) && !postponedIds.has(f.id) && f.severity === 'High');
    pendingHigh.forEach(f => {
      selectedIds.add(f.id);
      postponedIds.delete(f.id);
    });
    renderTable();
    updateStats();
    showToast(`Selected and moved ${pendingHigh.length} High Severity cases`, '🔥');
  }
  
  function selectField(fieldName) {
    const pendingField = FINDINGS.filter(f => !selectedIds.has(f.id) && !postponedIds.has(f.id) && f.field === fieldName);
    pendingField.forEach(f => {
      selectedIds.add(f.id);
      postponedIds.delete(f.id);
    });
    renderTable();
    updateStats();
    showToast(`Selected and moved ${pendingField.length} ${fieldName} cases`, '📜');
  }
  
  function invertSelection() {
    document.querySelectorAll('.row-checkbox').forEach(cb => {
      const id = parseInt(cb.getAttribute('data-id'), 10);
      if (selectedIds.has(id)) {
        selectedIds.delete(id);
      } else {
        selectedIds.add(id);
        postponedIds.delete(id);
      }
    });
    renderTable();
    updateStats();
    showToast(`Inverted selection on visible items`, '🔄');
  }
  
  function clearAll() {
    if (confirm('Clear all selections and postponements, returning all cases to Pending?')) {
      selectedIds.clear();
      postponedIds.clear();
      renderTable();
      updateStats();
      showToast(`All cases returned to Pending`, '🗑️');
    }
  }
  
  function setViewMode(mode) {
    activeViewMode = mode;
    document.querySelectorAll('.view-mode-tab').forEach(t => {
      t.classList.toggle('active', t.getAttribute('data-view') === mode);
    });
    saveStorage();
    renderTable();
    window.scrollTo({ top: 120, behavior: 'smooth' });
  }
  
  function promptEdit(id, event) {
    event.stopPropagation();
    const f = FINDINGS.find(x => x.id === id);
    if (!f) return;
    const current = getEffectiveSuggested(f);
    const newSug = prompt(`Edit Suggested Sandhi for ${f.sub_key} (${f.suspect}):`, current);
    if (newSug !== null && newSug.trim() !== '') {
      customReplacements[id] = newSug.trim();
      selectedIds.add(id); // auto select on edit
      renderTable();
      updateStats();
      showToast(`Updated suggestion for #${id}`, '✏️');
    }
  }
  
  // Review Modal
  function openReviewModal() {
    const modal = document.getElementById('reviewModal');
    const tbody = document.getElementById('modalTableBody');
    
    if (selectedIds.size === 0) {
      alert('Please select at least one change to review and implement.');
      return;
    }
    
    const selFindings = FINDINGS.filter(f => selectedIds.has(f.id));
    let html = '';
    
    selFindings.forEach((f, idx) => {
      const eff = getEffectiveSuggested(f);
      html += `
        <tr data-modal-id="${f.id}">
          <td>${idx + 1}</td>
          <td><strong>${f.sub_key}</strong></td>
          <td><span class="badge badge-field">${f.field}</span></td>
          <td><span class="suspect-tag">${f.suspect}</span></td>
          <td>
            <input type="text" class="modal-edit-input" value="${eff.replace(/"/g, '&quot;')}" onchange="updateCustomFromModal(${f.id}, this.value)">
          </td>
          <td><span style="font-size: 11.5px; color: #64748b;">${f.rule_name}</span></td>
          <td style="text-align: center;">
            <button class="btn-remove-row" onclick="removeSelectedFromModal(${f.id})">✕</button>
          </td>
        </tr>
      `;
    });
    
    tbody.innerHTML = html;
    modal.classList.add('open');
  }
  
  function closeReviewModal() {
    document.getElementById('reviewModal').classList.remove('open');
  }
  
  function updateCustomFromModal(id, val) {
    if (val.trim()) {
      customReplacements[id] = val.trim();
      saveStorage();
      renderTable();
      showToast(`Saved edit for #${id}`, '💾');
    }
  }
  
  function removeSelectedFromModal(id) {
    selectedIds.delete(id);
    updateStats();
    renderTable();
    openReviewModal(); // Re-render modal table
    showToast(`Removed #${id} from selection`, '🗑️');
  }
  
  // Export Functions
  function buildPatchData() {
    const selFindings = FINDINGS.filter(f => selectedIds.has(f.id)).map(f => ({
      id: f.id,
      sub_key: f.sub_key,
      parva: f.parva,
      kandah: f.kandah,
      field: f.field,
      rule_name: f.rule_name,
      sutra: f.sutra,
      severity: f.severity,
      suspect: f.suspect,
      suggested: getEffectiveSuggested(f),
      context: f.context,
      explanation: f.explanation
    }));
    
    return {
      version: "3.71",
      generated_at: new Date().toISOString(),
      total_findings: FINDINGS.length,
      total_selected: selFindings.length,
      total_postponed: postponedIds.size,
      postponed_ids: Array.from(postponedIds),
      patch_items: selFindings
    };
  }
  
  function downloadPatchJson() {
    if (selectedIds.size === 0) {
      alert('Please select at least one change to export.');
      return;
    }
    const data = buildPatchData();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sandhi_selected_patch_${data.total_selected}_items.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast(`Downloaded patch JSON (${data.total_selected} items)`, '⬇️');
  }  const SCRIPT_TEMPLATE_B64 = "__SCRIPT_TEMPLATE_B64__";

  function downloadPythonScript() {
    if (selectedIds.size === 0) {
      alert('Please select at least one change to generate the script.');
      return;
    }
    const data = buildPatchData();
    const patchJsonStr = JSON.stringify(data.patch_items, null, 2);
    
    // Decode standalone python script template from base64 and inject patch json
    const rawTemplate = new TextDecoder().decode(Uint8Array.from(atob(SCRIPT_TEMPLATE_B64), c => c.charCodeAt(0)));
    const pyScript = rawTemplate.replace('__PATCH_ITEMS_JSON__', patchJsonStr);

    const blob = new Blob([pyScript], { type: 'text/x-python;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `apply_selected_sandhi_patch_${data.total_selected}.py`;
    a.click();
    URL.revokeObjectURL(url);
    showToast(`Downloaded apply script (${data.total_selected} items)`, '⚡');
  }


  function copyTextToClipboard(textToCopy, successMsg, icon = '📋') {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(textToCopy).then(() => {
        showToast(successMsg, icon);
      }).catch(() => {
        fallbackCopyText(textToCopy, successMsg, icon);
      });
    } else {
      fallbackCopyText(textToCopy, successMsg, icon);
    }
  }

  function fallbackCopyText(textToCopy, successMsg, icon = '📋') {
    try {
      const textArea = document.createElement('textarea');
      textArea.value = textToCopy;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      const successful = document.execCommand('copy');
      document.body.removeChild(textArea);
      if (successful) {
        showToast(successMsg, icon);
      } else {
        alert('Copy failed. Please manually select and copy the text.');
      }
    } catch (err) {
      console.error('Clipboard copy error:', err);
      alert('Copy failed. Please manually select and copy the text.');
    }
  }

  function copyPatchJson() {
    if (selectedIds.size === 0) {
      alert('Please select at least one change to copy.');
      return;
    }
    const data = buildPatchData();
    const jsonStr = JSON.stringify(data, null, 2);
    copyTextToClipboard(jsonStr, `Copied ${data.total_selected} items to clipboard as JSON`, '📋');
  }

  function pastePatchJson() {
    if (navigator.clipboard && navigator.clipboard.readText && window.isSecureContext) {
      navigator.clipboard.readText().then(text => {
        if (text && (text.trim().startsWith('{') || text.trim().startsWith('['))) {
          applyPastedJson(text.trim());
        } else {
          promptForJsonPaste();
        }
      }).catch(() => {
        promptForJsonPaste();
      });
    } else {
      promptForJsonPaste();
    }
  }

  function promptForJsonPaste() {
    const raw = prompt('Paste your patch JSON here (array of patch items or exported patch object):');
    if (raw && raw.trim()) {
      applyPastedJson(raw.trim());
    }
  }

  function applyPastedJson(jsonStr) {
    try {
      const parsed = JSON.parse(jsonStr.trim());
      if (parsed.postponed_ids && Array.isArray(parsed.postponed_ids)) {
        postponedIds = new Set(parsed.postponed_ids);
      }
      const items = Array.isArray(parsed) ? parsed : (parsed.patch_items || []);
      if (!items || items.length === 0) {
        alert('No patch items found in the pasted JSON.');
        return;
      }
      let matchedCount = 0;
      items.forEach(it => {
        let match = null;
        if (it.id) {
          match = FINDINGS.find(f => f.id === it.id);
        }
        if (!match) {
          const sub = it.sub_key || it.subsection;
          const sus = it.suspect || it.suspect_segment;
          const field = it.field;
          match = FINDINGS.find(f => f.sub_key === sub && f.suspect === sus && (!field || f.field === field));
        }
        if (match) {
          selectedIds.add(match.id);
          const sug = it.suggested || it.suggested_sandhi;
          if (sug && sug !== match.suggested) {
            customReplacements[match.id] = sug;
          }
          matchedCount++;
        }
      });
      saveStorage();
      renderTable();
      updateStats();
      showToast(`Imported and selected ${matchedCount} items from pasted JSON`, '📥');
    } catch (e) {
      alert('Failed to parse pasted JSON: ' + e.message);
    }
  }
  
  function resetStorage() {
    if (confirm('Clear all saved selections, postponed statuses, view preferences, and custom replacements?')) {
      localStorage.removeItem(STORAGE_KEY_SELECTIONS);
      localStorage.removeItem(STORAGE_KEY_POSTPONED);
      localStorage.removeItem(STORAGE_KEY_CUSTOM);
      localStorage.removeItem(STORAGE_KEY_VIEW);
      localStorage.removeItem(STORAGE_KEY_AUTOHIDE);
      localStorage.removeItem(STORAGE_KEY_RULE);
      localStorage.removeItem(STORAGE_KEY_MATRIX_COLLAPSED);
      selectedIds.clear();
      postponedIds.clear();
      customReplacements = {};
      activeViewMode = 'pending';
      activeRule = 'all';
      isMatrixCollapsed = false;
      autoHideEnabled = true;
      document.getElementById('autoHideCheckbox').checked = true;
      document.querySelectorAll('.view-mode-tab').forEach(t => {
        t.classList.toggle('active', t.getAttribute('data-view') === 'pending');
      });
      if (document.getElementById('ruleMatrixBody')) {
        document.getElementById('ruleMatrixBody').style.display = 'block';
        document.getElementById('matrixToggleIcon').innerText = '▼';
        document.getElementById('matrixToggleText').innerText = 'Hide';
      }
      populateRuleDropdownAndMatrix();
      renderTable();
      updateStats();
      showToast('Cleared all saved state', '↺');
    }
  }
  
  // Event Listeners
  document.getElementById('searchInput').addEventListener('input', renderTable);
  
  const ruleSelectEl = document.getElementById('ruleSelect');
  if (ruleSelectEl) {
    ruleSelectEl.addEventListener('change', function() {
      activeRule = this.value;
      saveStorage();
      renderTable();
      populateRuleDropdownAndMatrix();
    });
  }
  
  document.getElementById('selectAllHeader').addEventListener('change', function() {
    if (this.checked) selectAllVisible();
    else deselectAllVisible();
  });
  
  document.getElementById('autoHideCheckbox').addEventListener('change', function() {
    autoHideEnabled = this.checked;
    saveStorage();
    showToast(`Auto-hide on select is now ${autoHideEnabled ? 'ON' : 'OFF'}`, autoHideEnabled ? '👁️' : '🔒');
  });
  
  document.querySelectorAll('.view-mode-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      setViewMode(tab.getAttribute('data-view'));
    });
  });
  
  document.getElementById('btnDownloadPatch').addEventListener('click', downloadPatchJson);
  document.getElementById('btnDownloadScript').addEventListener('click', downloadPythonScript);
  document.getElementById('btnCopyJson').addEventListener('click', copyPatchJson);
  document.getElementById('btnPasteJson').addEventListener('click', pastePatchJson);
  document.getElementById('btnReviewModal').addEventListener('click', openReviewModal);
  document.getElementById('btnResetStorage').addEventListener('click', resetStorage);
  
  document.getElementById('btnCloseModal').addEventListener('click', closeReviewModal);
  document.getElementById('btnModalClose').addEventListener('click', closeReviewModal);
  document.getElementById('btnModalDownloadPatch').addEventListener('click', downloadPatchJson);
  document.getElementById('btnModalDownloadScript').addEventListener('click', downloadPythonScript);
  document.getElementById('btnModalCopyJson').addEventListener('click', copyPatchJson);
  document.getElementById('btnModalPasteJson').addEventListener('click', () => { pastePatchJson(); openReviewModal(); });
  
  document.getElementById('dockBtnReview').addEventListener('click', openReviewModal);
  document.getElementById('dockBtnDownload').addEventListener('click', downloadPatchJson);
  
  window.addEventListener('scroll', updateStats);
  
  // Filter pills
  document.querySelectorAll('.filter-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      const filterType = btn.getAttribute('data-filter');
      const val = btn.getAttribute('data-val');
      
      document.querySelectorAll(`.filter-pill[data-filter="${filterType}"]`).forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      
      if (filterType === 'field') activeField = val;
      else if (filterType === 'sev') activeSev = val;
      renderTable();
    });
  });
  
  // Keyboard shortcuts:
  // - Escape: Close review modal
  // - Ctrl+Z / Cmd+Z: Undo selection change (outside text inputs)
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeReviewModal();
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') {
      const activeEl = document.activeElement;
      if (activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA')) {
        return; // Allow native input undo
      }
      e.preventDefault();
      undoLastAction();
    }
  });

  // Initialization
  initStorage();
  if (isMatrixCollapsed && document.getElementById('ruleMatrixBody')) {
    document.getElementById('ruleMatrixBody').style.display = 'none';
    document.getElementById('matrixToggleIcon').innerText = '▶';
    document.getElementById('matrixToggleText').innerText = 'Show';
  }
  document.getElementById('autoHideCheckbox').checked = autoHideEnabled;
  document.querySelectorAll('.view-mode-tab').forEach(t => {
    t.classList.toggle('active', t.getAttribute('data-view') === activeViewMode);
  });
  populateRuleDropdownAndMatrix();
  renderTable();
  updateStats();
  if (selectedIds.size > 0 || postponedIds.size > 0) {
    showToast(`Restored ${selectedIds.size} selected, ${postponedIds.size} postponed (${FINDINGS.length - selectedIds.size - postponedIds.size} pending)`, '✓');
  }
</script>

</body>
</html>
"""

    # Replace placeholders
    html_out = template.replace('__TOTAL_SUBS__', str(total_subs))
    html_out = html_out.replace('__FINDINGS_COUNT__', str(len(findings)))
    html_out = html_out.replace('__HIGH_COUNT__', str(high_count))
    html_out = html_out.replace('__MED_COUNT__', str(med_count))
    html_out = html_out.replace('__HEADER_COUNT__', str(by_field.get('Arsheyam Header', 0)))
    html_out = html_out.replace('__RIK_COUNT__', str(by_field.get('Rik Text', 0)))
    html_out = html_out.replace('__SAMAM_COUNT__', str(by_field.get('Samam Chant', 0)))
    html_out = html_out.replace('__SMETA_COUNT__', str(by_field.get('Saman Metadata', 0)))
    html_out = html_out.replace('__RMETA_COUNT__', str(by_field.get('Rik Metadata', 0)))
    html_out = html_out.replace('__FINDINGS_JSON__', findings_json)
    b64_script_template = base64.b64encode(STANDALONE_APPLY_SCRIPT_TEMPLATE.encode('utf-8')).decode('ascii')
    html_out = html_out.replace('__SCRIPT_TEMPLATE_B64__', b64_script_template)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_out)
        
    print(f"[INFO] Wrote interactive HTML triage report to: {output_path}")


def generate_markdown_report(total_subs: int, findings: list, output_path: Path):
    """Generates a clean Markdown companion report."""
    by_field = Counter(f['field'] for f in findings)
    by_sev = Counter(f['severity'] for f in findings)
    by_rule = Counter(f['rule_name'] for f in findings)
    
    lines = [
        "# ॥ सामसंहिता संस्कृत-सन्धि-परीक्षण-वृत्तान्तः ॥",
        "## Sanskrit Sandhi Rule Audit Report (Samhita Rik + Sāmam + Ārṣeyam)",
        "",
        f"- **Total Subsections Audited**: {total_subs}",
        f"- **Total Suspect Cases Flagged**: {len(findings)}",
        f"- **High Severity Cases**: {by_sev.get('High', 0)}",
        f"- **Medium Severity Cases**: {by_sev.get('Medium', 0)}",
        "",
        "### Breakdown by Text Dimension",
        "| Field | Flagged Cases | Description |",
        "| :--- | :---: | :--- |",
        f"| **Arsheyam Header** | {by_field.get('Arsheyam Header', 0)} | Subsection titles (॥...॥) with sandhi / spacing issues |",
        f"| **Rik Text** | {by_field.get('Rik Text', 0)} | Vedic Rik verse text with anusvara/stop issues |",
        f"| **Samam Chant** | {by_field.get('Samam Chant', 0)} | Samam chant words with anusvara before vowels/dandas |",
        f"| **Saman Metadata** | {by_field.get('Saman Metadata', 0)} | Arsheya attribution lines for Samam |",
        f"| **Rik Metadata** | {by_field.get('Rik Metadata', 0)} | Arsheya attribution lines for Rik (Rishi, Devata, Chandas) |",
        "",
        "### Breakdown by Paninian Sandhi Rule",
        "| Sandhi Rule | Sutra | Count | Severity |",
        "| :--- | :--- | :---: | :---: |"
    ]
    
    for r, count in sorted(by_rule.items(), key=lambda x: -x[1]):
        sample = next(f for f in findings if f['rule_name'] == r)
        lines.append(f"| **{r}** | `{sample['sutra']}` | {count} | {sample['severity']} |")
        
    lines.append("")
    lines.append("### Detailed Suspect Cases (High Severity Selection)")
    lines.append("")
    lines.append("| # | Line in Text | Subsection | Field | Suspect Segment | Suggested Sandhi | Rule | Context |")
    lines.append("| :---: | :---: | :--- | :--- | :--- | :--- | :--- | :--- |")
    
    for i, f in enumerate(findings, 1):
        clean_ctx = f['context'].replace('\n', ' ')
        if len(clean_ctx) > 60:
            clean_ctx = clean_ctx[:60] + "..."
        line_ref = f"[L{f['line_number']}](file:///C:/Users/sekha/OneDrive/Documents/GitHub/jaimineeyasamavedam/data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt#L{f['line_number']})" if f.get('line_number') else "-"
        lines.append(f"| {i} | {line_ref} | `{f['sub_key']}` | {f['field']} | `{f['suspect']}` | **`{f['suggested']}`** | {f['rule_name']} | {clean_ctx} |")
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
        
    print(f"[INFO] Wrote Markdown report to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Audit Sanskrit Sandhi rules in Jaimineeya Samaveda Samhita.")
    parser.add_argument('--input', '-i', default='data/corpora/samhita/02_ast/Samhita_ast.json',
                        help='Input AST JSON path')
    parser.add_argument('--txt', '-t', default='data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt',
                        help='Input Devanagari Unicode master text path')
    parser.add_argument('--html', default='data/corpora/samhita/06_reports/SANDHI_AUDIT_REPORT.html',
                        help='Output HTML report path')
    parser.add_argument('--md', default='data/corpora/samhita/06_reports/SANDHI_AUDIT_REPORT.md',
                        help='Output Markdown report path')
    parser.add_argument('--json-out', default='data/corpora/samhita/06_reports/sandhi_audit_findings.json',
                        help='Output JSON dataset path')
    args = parser.parse_args()
    
    txt_path = Path(args.txt)
    if txt_path.exists():
        print(f"[INFO] Auditing Sanskrit Sandhi rules DIRECTLY on master text: {txt_path}")
        total_subs, findings = run_sandhi_audit_txt(txt_path)
    else:
        in_path = Path(args.input)
        if not in_path.exists():
            alt_path = Path('data/corpora/samhita/02_ast/Samhita_ast.json')
            if alt_path.exists():
                in_path = alt_path
            else:
                raise FileNotFoundError(f"Input file not found at {in_path} or {alt_path}")
        print(f"[INFO] Auditing Sanskrit Sandhi rules from AST: {in_path}")
        total_subs, findings = run_sandhi_audit(in_path, txt_path=txt_path)
        
    print(f"[INFO] Audited {total_subs} subsections. Found {len(findings)} suspect Sandhi cases.")
    
    # Save JSON findings
    json_out = Path(args.json_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    with open(json_out, 'w', encoding='utf-8') as f:
        json.dump(findings, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Wrote JSON findings to: {json_out}")
    
    # Save HTML & Markdown reports
    generate_html_report(total_subs, findings, Path(args.html))
    generate_markdown_report(total_subs, findings, Path(args.md))
    
    print("[SUCCESS] Sanskrit Sandhi audit completed successfully.")

if __name__ == '__main__':
    main()
