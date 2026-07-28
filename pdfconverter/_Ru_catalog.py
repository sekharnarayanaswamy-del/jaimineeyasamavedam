import io, re
from collections import defaultdict
t = io.open('_s_docx.txt', encoding='utf-8').read()

lines = t.split('\n')

# Capture only the text INSIDE len=def modes for cataloging
def_segments = []
in_def = False
for ln in lines:
    if '<lang=eng>' in ln:
        before = ln.split('<lang=eng>')[0]
        if before.strip(): def_segments.append(before)
        in_def = False
    elif '<lang=def>' in ln:
        in_def = True
        after = ln.split('<lang=def>',1)[1]
        if after.strip(): def_segments.append(after)
    elif in_def:
        def_segments.append(ln)
dt = '\n'.join(def_segments)

# Collect: word-initial Ru tokens (capital R + u at token-start)
# and word-initial RR/Ru-with-following-vowel variants.
specimens = defaultdict(list)
for tok in re.findall(r'[A-Za-z~().&$#\-]+', dt):
    # word-initial Ru[...]: capital R followed by u (vocalic candidate) plus rest
    m = re.match(r'(R[uU]|[Rr]u)([A-Za-z~().&$#\-]*)', tok)
    if m and tok.startswith('R'):
        # Only interested in capital R cases
        head = m.group(1) + (re.match(r'[AaEeIiOoUu]', m.group(2)[:1]).group(0) if m.group(2) and re.match(r'[AaEeIiOoUu]', m.group(2)[:1]) else '')
        # Key by first 6 chars or first vowel cluster for compactness
        key = tok[:8]
        specimens[key].append(tok)
    else:
        # Also collect tokens where R appears after a consonant in mid-token
        for mm in re.finditer(r'([bcdfgjkmnpstvy zSHTBGNC])R[uU]([A-Za-z~().&$#\-]*)', tok):
            after = mm.group(2)[:6]
            key = tok[:12]
            specimens[key].append(tok)

# Build the user-facing catalog: distinct word-initial capital R tokens (case sensitive)
word_initial_R = sorted(set(tok for tok in re.findall(r'\bR[A-Za-z~().&$#\-]*', dt)))
# Filter to those that start with Ru/RR and have at least 4 chars
word_initial_Ru = sorted(set(tok for tok in word_initial_R if re.match(r'R[uU]', tok) and len(tok) >= 3))

# Also: distinct "vocalic R candidate" tokens — anywhere a capital R occurs mid-word after a consonant
mid_R = sorted(set(re.findall(r'[A-Za-z~().&$#\-]*[bcdfgjkmnpstvy zSHTBGNC]R[uU][A-Za-z~().&$#\-]*', dt)))

out = io.open('_Ru_catalog.txt','w',encoding='utf-8')
out.write(f"=== Word-initial `Ru*` tokens (distinct) — please confirm which are ऋ vs रु ===\n")
out.write(f"Total distinct: {len(word_initial_Ru)}\n\n")
for tok in word_initial_Ru:
    out.write(f"  {tok}\n")

out.write(f"\n=== Mid-word `consonant-Ru` tokens (distinct) — these become ृ by my rule ===\n")
out.write(f"Total distinct: {len(mid_R)}\n\n")
for tok in mid_R:
    out.write(f"  {tok}\n")

out.close()
print("done -- word-initial Ru distinct:", len(word_initial_Ru), ", mid-word Ru distinct:", len(mid_R))