import io, re
t = io.open('_s_docx.txt', encoding='utf-8').read()
in_def = False
def_text = []
for ln in t.split('\n'):
    if '<lang=eng>' in ln:
        before = ln.split('<lang=eng>')[0]
        if before.strip(): def_text.append(before)
        in_def = False
    elif '<lang=def>' in ln:
        in_def = True
        after = ln.split('<lang=def>',1)[1]
        if after.strip(): def_text.append(after)
    elif in_def:
        def_text.append(ln)
dt = '\n'.join(def_text)

out = io.open('_asp.txt','w',encoding='utf-8')

toks = re.findall(r'[A-Za-z~().&$#\-]+', dt)

# Find aspirate patterns
patterns = {
    'th (lowercase t + h)': r'th',
    'dh (lowercase d + h)': r'dh',
    'Th (capital T + h)': r'Th',
    'Dh (capital D + h)': r'Dh',
    'kh': r'kh',
    'gh': r'gh',
    'jh': r'jh',
    'ph (lowercase p + h)': r'ph',
    'bh': r'bh',
    'ch': r'ch',
    'Gh': r'Gh',
    'Bh': r'Bh',
}
for name, pat in patterns.items():
    hits = sorted(set(tok for tok in toks if re.search(pat, tok)))
    count_in_text = len(re.findall(pat, dt))
    out.write(f"=== {name}: {len(hits)} distinct tokens, {count_in_text} total ===\n")
    for tok in hits[:10]:
        out.write(f"  {tok!r}\n")
    out.write("\n")

out.close()
print("done")