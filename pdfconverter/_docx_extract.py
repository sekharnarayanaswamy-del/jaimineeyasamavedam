import io
try:
    import mammoth
    with open('s.docx','rb') as f:
        result = mammoth.extract_raw_text(f)
        txt = result.value
    io.open('_s_docx.txt','w',encoding='utf-8').write(txt)
    print("mammoth ok, length:", len(txt))
except Exception as e:
    print("mammoth failed:", e)