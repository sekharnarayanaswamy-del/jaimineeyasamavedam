import io, re
t = io.open('_s_docx.txt', encoding='utf-8').read()
out = io.open('_cons.txt','w',encoding='utf-8')

# Extract only lang=def text
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
def_text = '\n'.join(def_text)

# Find all tokens ending with various consonants + halant indicators
# In Baraha, a consonant at end-of-word means halant (ardhakshara)
# A consonant followed by a vowel joins with the matra
# Let's enumerate which "letter sequences" appear right before q, #, $, M, H, ., -, or | (word/clause boundaries)

# Also: pull out 2-letter and 3-letter sequences that look like consonant clusters
# (consonant letter followed by consonant letter, no vowel between)
# Strategy: scan for context like ~g, ~j (explicit), double consonants (kk, tt, pp...), clusters (rt, rp, kt...)

# Find any sequences of 2+ consonant letters
cons = "bcdfgjkmprstvBGnNzSHTKPlywR"
vowel = "aiueoAIUEO"

# 2-char clusters
bigrams = Counter = {}
for i in range(len(def_text)-1):
    if def_text[i] in cons and def_text[i+1] in cons:
        bg = def_text[i:i+2]
        bigrams[bg] = bigrams.get(bg,0)+1

out.write("=== 2-char consonant clusters (top 40) ===\n")
for bg, n in sorted(bigrams.items(), key=lambda x: -x[1])[:40]:
    out.write(f"  {bg!r}: {n}\n")

# 3-char clusters
trigrams = {}
for i in range(len(def_text)-2):
    if all(c in cons for c in def_text[i:i+3]):
        tg = def_text[i:i+3]
        trigrams[tg] = trigrams.get(tg,0)+1
out.write("\n=== 3-char consonant clusters (top 30) ===\n")
for tg, n in sorted(trigrams.items(), key=lambda x: -x[1])[:30]:
    out.write(f"  {tg!r}: {n}\n")

# Find tokens ending in a single consonant letter (suspected halant/ardhakshara at word end)
end_cons = {}
for tok in re.findall(r'[A-Za-z~().&$#\-]+', def_text):
    if tok and tok[-1] in cons:
        end_cons[tok[-1]] = end_cons.get(tok[-1],0)+1
out.write("\n=== Token terminal consonant letter ===\n")
for c, n in sorted(end_cons.items(), key=lambda x: -x[1]):
    out.write(f"  {c!r}: {n}\n")

# Look at capital-letter handling: which cap letters appear as word-start
out.write("\n=== First letters of tokens (top 30) ===\n")
first = {}
for tok in re.findall(r'[A-Za-z~().&$#\-]+', def_text):
    if tok:
        first[tok[0]] = first.get(tok[0],0)+1
for c, n in sorted(first.items(), key=lambda x: -x[1])[:30]:
    out.write(f"  {c!r}: {n}\n")

# Look for words containing both u and U to find length-marker usage
out.write("\n=== Sample tokens containing both u/U (length contrasts) ===\n")
mixed = [t for t in re.findall(r'[A-Za-z~().&$#\-]+', def_text) if 'u' in t and 'U' in t]
for tok in sorted(set(mixed))[:30]:
    out.write(f"  {tok!r}\n")

# Tokens with lowercase e or o (short vowels - rare per author's note)
out.write("\n=== Sample tokens with lowercase 'e' (short) ===\n")
for tok in sorted(set(t for t in re.findall(r'[A-Za-z~().&$#\-]+', def_text) if re.search(r'(?<![AaEeIiOoUu])e(?![a-zA-Z])|(?<![AaEeIiOoUu])e(?=[b-df-hj-np-tv-z])', t)))[:20]:
    out.write(f"  {tok!r}\n")
out.write("\n=== Sample tokens with lowercase 'o' (short) ===\n")
for tok in sorted(set(t for t in re.findall(r'[A-Za-z~().&$#\-]+', def_text) if 'o' in t))[:30]:
    out.write(f"  {tok!r}\n")

# LL case
out.write("\n=== tokens with LL ===\n")
for tok in sorted(set(t for t in re.findall(r'[A-Za-z~().&$#\-]+', def_text) if 'LL' in t)):
    out.write(f"  {tok!r}\n")

# Check for any standalone punctuation that we need to handle: । ॥ standard, plus danda in source
out.write("\n=== count of | and || ===\n")
out.write(f"  single |: {def_text.count('|')}\n")
out.write(f"  ||: {def_text.count('||')}\n")

# Find any tokens with $ followed by letters (dirgha svarita placement)
out.write("\n=== tokens with $ (dirgha svarita) - sample ===\n")
usd = [tok for tok in re.findall(r'[A-Za-z~().&$#\-]+', def_text) if '$' in tok]
for tok in sorted(set(usd))[:30]:
    out.write(f"  {tok!r}\n")

out.close()
print("done")