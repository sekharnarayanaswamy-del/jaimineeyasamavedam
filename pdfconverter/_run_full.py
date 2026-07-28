import importlib.util, io
spec = importlib.util.spec_from_file_location("bd", "src/tools/baraha_to_devanagari.py")
bd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bd)

with open('_s_docx.txt', 'r', encoding='utf-8') as f:
    txt = f.read()

out = bd.parse_baraha_document(txt)
io.open('_dev_full.txt','w',encoding='utf-8').write(out)
# Show specific lines we cared about
sample_lines = [33, 35, 69, 71, 95, 103, 167, 173, 199, 5477]
lines = out.split('\n')
with io.open('_dev_sample.txt','w',encoding='utf-8') as f:
    for n in sample_lines:
        if n-1 < len(lines):
            f.write(f"=== line {n} ===\n{lines[n-1]}\n\n")
print("done")