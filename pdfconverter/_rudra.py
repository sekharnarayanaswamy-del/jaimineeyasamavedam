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

out = io.open('_rudra.txt','w',encoding='utf-8')
for tok in re.findall(r'\b[rR]u[\w\-.]*', dt):
    if tok.lower().startswith('ru'):
        out.write(f"{tok!r}\n")
out.close()
print("done")