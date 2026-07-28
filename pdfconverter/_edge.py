import io, re
t = io.open('_s_docx.txt', encoding='utf-8').read()
lines = t.split('\n')
out = io.open('_edge.txt','w',encoding='utf-8')

# Find lines with specific constructs
patterns = {
    'gg\\) followed by #': r'\(gg\)#',
    'gm\\) followed by #': r'\(gm\)#',
    'word ending in r followed by accent': r'r[q#$]',
    'two accents adjacent #q or q#': r'[q#$][q#$]',
    'accent followed by consonant cluster': r'[q#$][bcdfgjkmprstvBGnNzSHTK]',
    'capital word (English inside def?)': r'\b[A-Z]{5,}\b',
    'token with embedded &': r'\w&\w',
    'H after consonant not vowel': r'[^a-zA-Z]H',
    'comma+letters (,pavitraM)': r',[A-Za-z]',
    'word with quoted english': r'"[A-Za-z]',
    'GN or rare clusters': r'(?<![A-Za-z])([GYn][A-Z][A-Za-z]+)',
    '~ without following': r'~(?![gjM])',
}
for name, pat in patterns.items():
    hits = []
    for i, ln in enumerate(lines):
        for m in re.finditer(pat, ln):
            s = max(0, ln.find(m.group(0))-10)
            e = min(len(ln), ln.find(m.group(0))+30)
            hits.append(f"L{i+1}: ...{ln[s:e]}...")
    out.write(f"\n=== {name} ({len(hits)} hits) ===\n")
    for h in hits[:15]:
        out.write(f"  {h}\n")

# Show specific examples we care about
out.write("\n=== Lines containing 'cikI#r' ===\n")
for i, ln in enumerate(lines):
    if 'cikI#r' in ln:
        out.write(f"L{i+1}: {ln}\n")

out.write("\n=== Lines containing 'yatki~j' ===\n")
for i, ln in enumerate(lines):
    if 'yatki~j' in ln:
        out.write(f"L{i+1}: {ln}\n")

out.write("\n=== Lines containing '(RV' or '(TB' or '(TS' (citation refs) ===\n")
for i, ln in enumerate(lines):
    if re.search(r'\((RV|TB|TS|TA|T\.[AB])', ln):
        out.write(f"L{i+1}: {ln}\n")
        if i > 200:
            break

out.close()
print("done")