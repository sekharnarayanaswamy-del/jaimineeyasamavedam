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

out = io.open('_R_case.txt','w',encoding='utf-8')

# R not followed by u
no_u = re.findall(r'R(?![uU])', dt)
out.write(f"=== R not followed by u: {len(no_u)} ===\n")
out.write(f"=== R followed by u: {len(re.findall(r'R[uU]', dt))} ===\n")

# Sample tokens with R not followed by u
toks = re.findall(r'[A-Za-z~().&$#\-]+', dt)
RnoU = sorted(set(tok for tok in toks if 'R' in tok and not re.search('R[uU]', tok)))
for tok in RnoU[:30]:
    out.write(f"  R-no-u: {tok!r}\n")

# Ru after consonant vs. Ru at word start
Ru_after_cons = re.findall(r'[bcdfgjkmnpstvy zSHTBGNC](?!h)R[uU]', dt)
out.write(f"\nRu after consonant (approx): {len(Ru_after_cons)}\n")
# Ru at word start (preceded by space/start)
Ru_start = re.findall(r'(?:^|\s)(R[uU][A-Za-z~().&$#\-]*)', dt)
out.write(f"Ru at word start: {len(Ru_start)}\n")
for tok in sorted(set(Ru_start))[:20]:
    out.write(f"  Ru-start: {tok!r}\n")

# Specifically check kR
kRnoU = sorted(set(tok for tok in toks if 'kR' in tok and not re.search('kR[uU]', tok)))
out.write(f"\n=== kR not followed by u ({len(kRnoU)} distinct) ===\n")
for tok in kRnoU[:15]:
    out.write(f"  {tok!r}\n")

# Check for mR without u
mRnoU = sorted(set(tok for tok in toks if 'mR' in tok and not re.search('mR[uU]', tok)))
out.write(f"\n=== mR not followed by u ({len(mRnoU)} distinct) ===\n")
for tok in mRnoU[:15]:
    out.write(f"  {tok!r}\n")

# Check L (vocalic L) usage
L_tokens = sorted(set(tok for tok in toks if 'L' in tok))
out.write(f"\n=== 'L' vowel tokens ({len(L_tokens)} distinct) ===\n")
for tok in L_tokens[:15]:
    out.write(f"  {tok!r}\n")

# Check for any patterns like the (gm)# accent after gomukha
out.write("\n=== Patterns around (gm) ===\n")
for m in re.finditer(r'\(gm\)', dt):
    start = m.start()
    out.write(f"  context: '{dt[start:start+15]}'\n")
    break  # just show first one

out.close()
print("ok")