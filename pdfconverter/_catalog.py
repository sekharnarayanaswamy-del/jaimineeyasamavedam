import io, re
from collections import Counter

t = io.open('_s_docx.txt', encoding='utf-8').read()
lines = t.split('\n')

# Only analyze Sanskrit (lang=def) lines
in_def = False
def_lines = []
for ln in lines:
    if '<lang=eng>' in ln:
        in_def = False
        # everything after <lang=eng> on same line is English; but text before stays def
        before = ln.split('<lang=eng>')[0]
        if before.strip():
            def_lines.append(before)
    elif '<lang=def>' in ln:
        in_def = True
        after = ln.split('<lang=def>',1)[1]
        if after.strip():
            def_lines.append(after)
    elif in_def:
        def_lines.append(ln)

def_text = '\n'.join(def_lines)

out = io.open('_baraha_catalog.txt','w',encoding='utf-8')

# 1. All unique ASCII letters used
chars = Counter(c for c in def_text if c.isalpha())
out.write("=== Letter frequency (lowercased) ===\n")
for ch, n in sorted(chars.items(), key=lambda x: -x[1]):
    out.write(f"  {ch!r}: {n}\n")

# 2. Find tokens (words) - split on whitespace
tokens = re.findall(r'[A-Za-z~().&$#\-]+', def_text)
tok_counter = Counter(tokens)
out.write(f"\n=== Total tokens: {len(tokens)}, unique: {len(tok_counter)} ===\n")

# 3. Special multi-char prefixes/suffixes we want to verify
patterns = {
    'kSh': r'kSh',
    'ksh': r'ksh',
    'j~jA': r'j~jA',
    'GYA': r'GYA',
    'GY': r'GY',
    'dRu': r'dRu',
    'Dru': r'Dru',
    'tr': r'tr',
    'pra': r'pra',
    'praq': r'praq',
    '(gm)': r'\(gm\)',
    '(gM)': r'\(gM\)',
    ' ($&': r'\$&',
    '(rgm)': r'\(rgm\)',
    '*': r'\*',
    ' || ': r'\|\|',
    ' # at end of token': r'#(?=\s|$)',
    ' q at end of token': r'q(?=\s|$|$)',
    ' . in middle': r'\w\.\w',
    ' - in middle of token': r'[A-Za-z]-[A-Za-z]',
    ' rr/ll doubling': r'([rl])\1',
    ' ss doubling': r'ss',
    '~g': r'~g',
    '~j': r'~j',
    '~M': r'~M',
    ' standalone ~': r'~(?![gjM])',
    ' capital RR': r'RR',
    ' capital LL': r'LL',
    ' lowercase rr': r'rr',
    ' standalone &': r'&(?![a-zA-Z])',
    ' standalone apostrophe': r"'",
}
out.write("\n=== Pattern occurrences ===\n")
for name, pat in patterns.items():
    hits = re.findall(pat, def_text)
    out.write(f"  {name}: {len(hits)}\n")

# 4. Show tokens containing . (the virala hint)
out.write("\n=== Tokens containing '.' (virala) ===\n")
dot_tokens = sorted(set(t for t in tokens if '.' in t))
for t in dot_tokens[:60]:
    out.write(f"  {t!r}\n")

# 5. Show tokens containing '-' (intra-word hyphen)
out.write("\n=== Tokens containing '-' (intra-word) [first 60] ===\n")
hyphen_tokens = sorted(set(t for t in tokens if '-' in t))
for t in hyphen_tokens[:60]:
    out.write(f"  {t!r}\n")

# 6. Find any Devanagari inside def (shouldn't be any)
dev_in = re.findall(r'[\u0900-\u097F]', def_text)
out.write(f"\n=== Devanagari chars in def section: {len(dev_in)} ===\n")

# 7. Find all (xxx) bracketed tokens
out.write("\n=== All distinct '(xxx)' bracket expressions ===\n")
brackets = sorted(set(re.findall(r'\([^)]*\)', def_text)))
for b in brackets:
    out.write(f"  {b!r}\n")

# 8. Show example tokens with r followed by consonant (rt, rd, rp etc.) since rt/hartA is a concern
out.write("\n=== Sample tokens starting with 'rT' or 'rt' or 'rdh' (tr/repha cases) ===\n")
sample = [t for t in tokens if re.match(r'(r[tdp]|hart)', t)]
for t in sorted(set(sample))[:40]:
    out.write(f"  {t!r}\n")

out.close()
print("done, def_lines:", len(def_lines))