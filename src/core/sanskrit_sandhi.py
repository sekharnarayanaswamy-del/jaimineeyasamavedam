"""
Sanskrit External Paninian Sandhi Engine for Vedic Metadata (Rik & Samam).

Provides rule-based classical Paninian external Sandhi concatenation
for Vedic Rishi, Devata, and Chandas metadata.
"""

import re

VOICED_CONS = 'गघङजझञडढणदधनबभमयर्लवह'
VOICED_STOPS = 'गघजझडढदधबभ'
VOWELS = 'अआइईउऊऋएऐओऔ'

def apply_sandhi_pair(w1: str, w2: str) -> str:
    """Applies Paninian external Sandhi between word1 and word2."""
    w1 = w1.strip()
    w2 = w2.strip()
    if not w1:
        return w2
    if not w2:
        return w1
    
    # If w1 ends with a parenthetical remark, e.g. "कविः (कुत्सः)",
    # apply sandhi if possible or join with space.
    if w1.endswith(')'):
        return f"{w1} {w2}"
    if w2.startswith('('):
        return f"{w1} {w2}"

    first_char_w2 = w2[0]
    
    # -------------------------------------------------------------
    # CASE 1: Word 1 ends in Visarga (ः)
    # -------------------------------------------------------------
    if w1.endswith('ः'):
        stem = w1[:-1]
        
        # Check if stem ends in a matra
        has_matra = any(stem.endswith(m) for m in ['ा', 'ि', 'ी', 'ु', 'ू', 'ृ', 'ॄ', 'े', 'ै', 'ो', 'ौ'])
        
        # 1A: Ends in short a + visarga (अः)
        if not has_matra:
            # Rule: अः + अ -> ओऽ
            if w2.startswith('अ'):
                rest_w2 = w2[1:]
                return f"{stem}ोऽ{rest_w2}"
                
            # Rule: अः + any vowel other than अ -> drops visarga (lopa)
            elif first_char_w2 in VOWELS:
                return f"{stem} {w2}"
                
            # Rule: अः + voiced consonant -> ओ + space + w2
            elif first_char_w2 in VOICED_CONS:
                return f"{stem}ो {w2}"
                
            # Rule: अः + त / थ -> स् + w2
            elif first_char_w2 in ['त', 'थ']:
                return f"{stem}स्{w2}"
                
            # Rule: अः + च / छ -> श् + w2
            elif first_char_w2 in ['च', 'छ']:
                return f"{stem}श्{w2}"
                
            # Rule: अः + ट / ठ -> ष् + w2
            elif first_char_w2 in ['ट', 'ठ']:
                return f"{stem}ष्{w2}"
                
            # Rule: अः + क/ख/प/फ/sibilants -> remains visarga
            else:
                return f"{w1} {w2}"
                
        # 1B: Ends in long aa + visarga: आः (stem ends with 'ा')
        elif stem.endswith('ा'):
            # Rule: आः before any vowel or voiced consonant -> drops visarga
            if first_char_w2 in VOWELS or first_char_w2 in VOICED_CONS:
                return f"{stem} {w2}"
            # Before त/थ -> स्
            elif first_char_w2 in ['त', 'थ']:
                return f"{stem}स्{w2}"
            else:
                return f"{w1} {w2}"
                
        # 1C: Ends in non-a/aa vowel + visarga (e.g. इः, ईः, उः, ऊः, ओः)
        else:
            # Rule: Visarga becomes Repha (र्) before vowels and voiced consonants
            if first_char_w2 in VOWELS:
                vowel_matra_map = {
                    'अ': 'र', 'आ': 'रा', 'इ': 'रि', 'ई': 'री', 'उ': 'रु', 'ऊ': 'रू',
                    'ऋ': 'रृ', 'ए': 'रे', 'ऐ': 'रै', 'ओ': 'रो', 'औ': 'रौ'
                }
                v_replacement = vowel_matra_map.get(first_char_w2, 'र्' + first_char_w2)
                rest_w2 = w2[1:]
                return f"{stem}{v_replacement}{rest_w2}"
                
            elif first_char_w2 in VOICED_CONS:
                if first_char_w2 == 'र':
                    return f"{stem} {w2}"
                else:
                    return f"{stem}र्{w2}"
                    
            elif first_char_w2 in ['त', 'थ']:
                return f"{stem}स्{w2}"
            elif first_char_w2 in ['च', 'छ']:
                return f"{stem}श्{w2}"
            elif first_char_w2 in ['ट', 'ठ']:
                return f"{stem}ष्{w2}"
            else:
                return f"{w1} {w2}"

    # -------------------------------------------------------------
    # CASE 2: Word 1 ends in Vowel
    # -------------------------------------------------------------
    if w1.endswith('ी'):
        stem = w1[:-1]
        # Yan-sandhi before dissimilar vowel
        if w2.startswith('अ'):
            return f"{stem}्य{w2[1:]}"
        elif w2.startswith('आ'):
            return f"{stem}्या{w2[1:]}"
        elif w2.startswith('इ') or w2.startswith('ई'):
            return f"{stem}ी{w2[1:]}"
        elif w2.startswith('उ'):
            return f"{stem}्यु{w2[1:]}"
        else:
            return f"{w1} {w2}"
            
    # E.g. त्रिष्टुप् / ककुप् ending in 'प्'
    if w1.endswith('प्'):
        stem = w1[:-1]
        if first_char_w2 in VOWELS or first_char_w2 in VOICED_CONS:
            # Jashtva: प् -> ब्
            if first_char_w2 in VOWELS:
                v_map = {'अ': 'ब', 'आ': 'बा', 'इ': 'बि', 'ई': 'बी', 'उ': 'बु', 'ऊ': 'बू', 'ऋ': 'बृ', 'ए': 'बे', 'ऐ': 'बै', 'ओ': 'बो', 'औ': 'बौ'}
                return f"{stem}{v_map.get(first_char_w2, 'ब्' + first_char_w2)}{w2[1:]}"
            else:
                return f"{stem}ब्{w2}"
        elif first_char_w2 == 'स':
            # E.g. ककुप् + सोमः -> ककुप्सोमः
            return f"{stem}प्{w2}"

    # E.g. उष्णिक् ending in 'क्'
    if w1.endswith('क्'):
        stem = w1[:-1]
        if first_char_w2 in VOWELS or first_char_w2 in VOICED_CONS:
            # Jashtva: क् -> ग्
            if first_char_w2 in VOWELS:
                v_map = {'अ': 'ग', 'आ': 'गा', 'इ': 'गि', 'ई': 'गी', 'उ': 'गु', 'ऊ': 'गू', 'ऋ': 'गृ', 'ए': 'गे', 'ऐ': 'गै', 'ओ': 'गो', 'औ': 'गौ'}
                return f"{stem}{v_map.get(first_char_w2, 'ग्' + first_char_w2)}{w2[1:]}"
            else:
                return f"{stem}ग्{w2}"
                
    # E.g. विराट् ending in 'ट्'
    if w1.endswith('ट्'):
        stem = w1[:-1]
        if first_char_w2 in VOWELS or first_char_w2 in VOICED_CONS:
            # Jashtva: ट् -> ड्
            if first_char_w2 in VOWELS:
                v_map = {'अ': 'ड', 'आ': 'डा', 'इ': 'डि', 'ई': 'डी', 'उ': 'डु', 'ऊ': 'डू', 'ऋ': 'डृ', 'ए': 'डे', 'ऐ': 'डै', 'ओ': 'डो', 'औ': 'डौ'}
                return f"{stem}{v_map.get(first_char_w2, 'ड्' + first_char_w2)}{w2[1:]}"
            else:
                return f"{stem}ड्{w2}"

    return f"{w1} {w2}"

def combine_rishi_devata_chandas(parts: list) -> str:
    """Applies continuous Sandhi across [Rishi, Devata, Chandas] parts."""
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
        
    res = parts[0]
    for p in parts[1:]:
        res = apply_sandhi_pair(res, p)
    # Normalize multiple whitespace
    res = re.sub(r'\s+', ' ', res).strip()
    return res
