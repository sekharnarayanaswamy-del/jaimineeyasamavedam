import re

def reformat(text, count):
    dev_count = count # mock string count
    if text.startswith('॥') and (text.endswith('॥') or text.endswith(')')):
        prefix = ""
        m1 = re.match(r'^॥\s*(.+?)\s*-\s*[०-९]+\s*॥$', text)
        m2 = re.match(r'^॥\s*(.+?)\s*॥\s*\([०-९]+\)$', text)
        if m1:
            inner = m1.group(1).strip()
        elif m2:
            inner = m2.group(1).strip()
        elif text.endswith('॥'):
            inner = text[1:-1].strip()
        else:
            inner = None
        
        if inner:
            return f"॥ {inner} ॥              ({dev_count})\n"
    return text + '\n'

print(reformat("॥ औरूक्षयेद्वे - २ ॥", "२"))
print(reformat("॥ औरूक्षयेद्वे ॥              (२)", "३"))
print(reformat("॥ औरूक्षयेद्वे ॥", "४"))
