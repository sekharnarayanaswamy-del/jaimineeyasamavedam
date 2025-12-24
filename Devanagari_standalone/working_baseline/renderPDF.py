#from docx import Document
import platform
from pathlib import Path
import re

import sys
#from doc_utils import escape_for_latex
import jinja2
import subprocess
import tempfile
import os
import json
import urllib.parse
from requests.models import PreparedRequest
import grapheme

# --- New import for utility functions ---
from convert_txt_to_json_1 import (
    combine_halants, combine_ardhaksharas,
    my_encodeURL, my_format,
    replacecolon, normalize_and_trim,
    parse_mantra_for_latex, 
    sanitize_data_structure
)
# --- End new import ---

# ----------------------------------------------------
# 1. NEW UTILITY: Accent Replacements (UPDATED POSITIONS)
# ----------------------------------------------------
def replace_accents(text):
    r"""
    Replaces ASCII markers (1), (2), etc., with LaTeX commands.
    UPDATES:
    1. Adjusted \raisebox for Anudatta to -0.8ex (Significant drop).
    """
    if not text: return text
    
    replacements = [
        # Swarita (Vertical line above): Raised to 0.1ex
        ('(1)', r'\accentmark{12}{\raisebox{0.3ex}{\char"0951}}'),  
        
        # Anudatta (Horizontal line below): Lowered to -0.8ex to fix touching
        ('(2)', r'\accentmark{15}{\raisebox{0.25ex}{\char"1CD2}}'),  
        
        # Kampa (Curve): Raised to 0.1ex
        ('(3)', r'\accentmark{12}{\raisebox{0.3ex}{\char"1CF8}}'),  
        
        # Trikampa: Raised to 0.1ex
        ('(4)', r'\accentmark{12}{\raisebox{0.25ex}{\char"1CF9}}'),  
    ]
  
    for marker, replacement in replacements:
        text = text.replace(marker, replacement)
    
    return text

# ----------------------------------------------------
# 2. NEW UTILITY: Consecutive Accent Handler
# ----------------------------------------------------
def handle_consecutive_accents(text):
    r"""
    Inserts a small \kern to separate specific accent transitions 
    that are prone to visual overlap.
    """
    if not text: return text
    
    # CASE A: Anudatta (2) followed by Anudatta (2)
    pat_2_2 = r'(\(2\))(?=[^()]{1,5}\(2\))'
    text = re.sub(pat_2_2, r'\1\\kern0.15em', text)

    # CASE B: Swarita (1) followed by Anudatta (2)
    pat_1_2 = r'(\(1\))(?=[^()]{1,5}\(2\))'
    text = re.sub(pat_1_2, r'\1\\kern0.15em', text)

    # CASE C: Anudatta (2) followed by Kampa (3) or Trikampa (4)
    pat_2_3= r'(\(2\))(?=[^()]{1,5}\(3\))'
    text = re.sub(pat_2_3, r'\1\\kern0.15em', text)

    pat_2_4= r'(\(2\))(?=[^()]{1,5}\(4\))'
    text = re.sub(pat_2_4, r'\1\\kern0.15em', text)
    
    return text

# ----------------------------------------------------
# 3. NEW UTILITY: Remove Mantra Spaces (Samhita Mode)
# ----------------------------------------------------
def remove_mantra_spaces(text):
    """
    Removes all spaces within the text to create continuous Samhita text.
    Preserves Dandas.
    """
    if not text: return text
    
    text = text.replace(' ', '')
    text = text.replace('\t', '')
    
    return text

def format_dandas(text):
    """
    Adds spaces around danda symbols (| || । ॥) and cleans up extra spaces.
    Safe to use on strings that might be None.
    """
    if not text or not isinstance(text, str):
        return text

    # --- STEP 1: Normalize Double Dandas ---
    # Convert ASCII ||, spaced | |, Devanagari ।। (two singles), and OCR II to ॥
    # IMPORTANT: We must catch '।।' (two U+0964) before processing singles!
    text = re.sub(r'\|\|', '॥', text)       
    text = re.sub(r'\|\s*\|', '॥', text)    
    text = re.sub(r'।।', '॥', text)         
    text = re.sub(r'II', '॥', text)         

    # --- STEP 2: Normalize Single Danda ---
    # Convert remaining ASCII | to Devanagari ।
    text = text.replace('|', '।')

    # --- STEP 3: Apply Spacing Rules ---
    
    # Rule B: Double Danda (॥) -> Standard spaces
    text = text.replace('॥', r' ॥ ')

    # --- STEP 4: Cleanup ---
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # --- STEP 5: Prevent Line Breaks in Mantra Numbers ---
    danda_pattern = r'(?:\|\||॥)'      
    digits = r'[\d०-९]+'        
    pattern = rf'({danda_pattern})\s+({digits})\s+({danda_pattern})'
    text = re.sub(pattern, r'\\mbox{\1 \2 \3}', text)

    # Rule A: Single Danda (।) -> Add \enspace BEFORE it
    # \enspace is 0.5em, roughly the width of a digit, very visible.
    # We also keep a normal space after it.
    text = text.replace('।', r' । ')

    return text
    
def clean_stack_arg(text):
    r"""
    Aggressively removes LaTeX newlines, paragraphs, comments, and line breaks.
    """
    if not text:
        return ""
    text = re.sub(r'\\+newline', '', text)
    text = re.sub(r'\\par', '', text)
    text = text.replace('%', '').replace('\n', ' ').replace('\r', '')
    return text.strip()

def CreateCompilation():
    outputdir="outputs/md/Compilation"
    templateFileName_md="templates/PanchasatCompile_main.md"
    templateFileName_tex="templates/PanchasatCompile_main.tex"
    exit_code=0
    ts_string = Path("TS_withPadaGhanaJataiKrama.json").read_text(encoding="utf-8")
    parseTree = json.loads(ts_string)
    for kanda in parseTree['TS']['Kanda']:
        kandaInfo=kanda['id']
        for prasna in kanda['Prasna']:
            prasnaInfo=prasna['id']
            CreateMd(templateFileName_md,f"TS_{kandaInfo}_{prasnaInfo}","Compilation",prasna)
                       
def CreatePdf (templateFileName,name,DocfamilyName,data, current_os="Windows"):
    data=escape_for_latex(data)
    
    outputdir="output_text"
    logdir=f"{outputdir}/logs"
    exit_code=0
    
    TexFileName=f"{name}_{DocfamilyName}_Unicode.tex"
    PdfFileName=f"{name}_{DocfamilyName}_Unicode.pdf"
    TocFileName=f"{name}_{DocfamilyName}_Unicode.toc"
    LogFileName=f"{name}_{DocfamilyName}_Unicode.log"
    template = templateFileName
    outputdir = f"{outputdir}/pdf/{name}"
    Path(outputdir).mkdir(parents=True, exist_ok=True)
    Path(logdir).mkdir(parents=True, exist_ok=True)
    document = template.render(supersections=data, os=current_os)
    

    tmpdirname="."
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpfilename=f"{tmpdirname}/{TexFileName}"

        with open(tmpfilename,"w",encoding="utf-8") as f:
            f.write(document)
        
        # Uncomment to run latexmk
        # result = subprocess.Popen(["latexmk","-lualatex", "--interaction=nonstopmode","--silent",tmpfilename],cwd=tmpdirname)
        # result.wait()
        
        src_pdf_file=Path(f"{tmpdirname}/{PdfFileName}")
        dst_pdf_file=Path(f"{outputdir}/{PdfFileName}")
        src_log_file=Path(f"{tmpdirname}/{LogFileName}")
        dst_log_file=Path(f"{logdir}/{LogFileName}")
        src_tex_file=Path(f"{tmpdirname}/{TexFileName}")
        dst_tex_file=Path(f"{outputdir}/{TexFileName}")
        
        path = Path(src_tex_file)
        if path.is_file():
            if dst_tex_file.exists():
                dst_tex_file.unlink()
            src_tex_file.rename(dst_tex_file)  
        path = Path(src_pdf_file)
        if path.is_file():
            if dst_pdf_file.exists():
                dst_pdf_file.unlink()
            src_pdf_file.rename(dst_pdf_file)
        path = Path(src_log_file)
        if path.is_file():
            if dst_log_file.exists():
                dst_log_file.unlink()
            src_log_file.rename(dst_log_file)

    return exit_code

def CreateTextFile (templateFileName,name,DocfamilyName,data):
    data=escape_for_latex(data)
    
    outputdir="output_text"
    logdir=f"{outputdir}/logs"
    exit_code=0
    
    TexFileName=f"{name}_{DocfamilyName}_Unicode.tex"
    PdfFileName=f"{name}_{DocfamilyName}_Unicode.pdf"
    TextFileName=f"{name}_{DocfamilyName}_Unicode.txt"
    TocFileName=f"{name}_{DocfamilyName}_Unicode.toc"
    LogFileName=f"{name}_{DocfamilyName}_Unicode.log"
    template = templateFileName
    outputdir = f"{outputdir}/txt/{name}"
    Path(outputdir).mkdir(parents=True, exist_ok=True)
    Path(logdir).mkdir(parents=True, exist_ok=True)
    document = template.render(supersections=data)
    

    tmpdirname="."
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpfilename=f"{tmpdirname}/{TextFileName}"

        with open(tmpfilename,"w",encoding="utf-8") as f:
            f.write(document)
        
        src_text_file=Path(f"{tmpdirname}/{TextFileName}")
        dst_text_file=Path(f"{outputdir}/{TextFileName}")
        
        path = Path(src_text_file)
        if path.is_file():
            if dst_text_file.exists():
                dst_text_file.unlink()
            src_text_file.rename(dst_text_file)  

    return exit_code


def escape_for_latex(data):
    if isinstance(data, dict):
        new_data = {}
        for key in data.keys():
            new_data[key] = escape_for_latex(data[key])
        return new_data
    elif isinstance(data, list):
        return [escape_for_latex(item) for item in data]
    elif isinstance(data, str):
        latex_special_chars = {
            "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
            "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\^{}",
            "\\": r"\textbackslash{}", "\n": "\\newline%\n", "-": r"{-}",
            "\xA0": "~", "[": r"{[}", "]": r"{]}",
        }
        return "".join([latex_special_chars.get(c, c) for c in data])

    return data

def format_mantra_sets(subsection, supersection_title, section_title, subsection_title, footnote_dict={}):
    
    formatted_output = []
    
    # --- DATA EXTRACTION ---
    string_1 = subsection.get('rik_metadata', '')
    string_2 = subsection.get('rik_text', '')
    string_3 = subsection.get('saman_metadata', '')
    
    # Clean titles
    display_sub_title = re.sub(r'^([|॥]+)\s*', r'\1 ', subsection_title)
    index_title = re.sub(r'[|॥]', '', subsection_title).strip()

    # --- LAYOUT CONSTRUCTION ---
    
    # 1. Page Break / Indexing Logic
    formatted_output.append(r"\par\filbreak")              
    formatted_output.append(r"\phantomsection")
    if subsection_title:
        formatted_output.append(f"\\addcontentsline{{toc}}{{subsection}}{{{display_sub_title}}}")
        formatted_output.append(f"\\index{{{index_title}}}")

    # 2. String 1: Rik Metadata (Plain Centered)
    # COLOR: BLUE
    if string_1:
        s1 = format_dandas(string_1)
        formatted_output.append(f"{{\\centering \\textcolor{{DarkOrchid}}{{{s1}}} \\par}}")
        formatted_output.append(r"\vspace{0.6em}")

    # 3. String 2: Rik Text (With Vedic Accents, Upright)
    # COLOR: BLUE
    if string_2:
        # Step A: Remove Spaces (Samhita Mode)
        s2 = remove_mantra_spaces(string_2)
        # Step B: Handle Consecutive Accent Kerning
        s2 = handle_consecutive_accents(s2)
        # Step C: Replace Accents with LaTeX commands (with adjusted sizes)
        s2 = replace_accents(s2)
        # Step D: Format Dandas (Spaces and No-Break Numbers)
        s2 = format_dandas(s2)
        # Output: Upright (not italics)
        formatted_output.append(f"{{\\centering \\textcolor{{blue}}{{{s2}}} \\par}}")
        formatted_output.append(r"\vspace{0.8em}")

    # 4. Combined Header: || Subsection header || || samam_metadata ||
    header_part = display_sub_title.strip()
    header_part = f"\\textcolor{{ForestGreen}}{{{header_part}}}"  
    
    # COLOR: Samam Metadata -> BROWN
    meta_part = format_dandas(string_3).strip()
    if meta_part:
        meta_part = f"\\textcolor{{DarkOrchid}}{{{meta_part}}}"
    
    combined_header = ""
    if header_part and meta_part:
        combined_header = f"{header_part} \\quad {meta_part}"
    elif header_part:
        combined_header = header_part
    elif meta_part:
        combined_header = meta_part
        
    if combined_header:
         formatted_output.append(f"{{\\centering \\textbf{{{combined_header}}} \\par}}")

    formatted_output.append(r"\nopagebreak")                
    formatted_output.append(r"\vspace{0.5em}")
    formatted_output.append(r"\nopagebreak")

    # --- MANTRA CONTENT RENDERING ---
    all_mantra_rows, all_swara_rows = parse_mantra_for_latex(
        subsection, 
        supersection_title, 
        section_title, 
        subsection_title
    )
    
    paragraph_buffer = []
    
    footnotes_map = {}
    raw_footnotes = subsection.get('footnotes', []) 
    for note in raw_footnotes:
        if 'word' in note and 'content' in note:
            footnotes_map[note['word']] = note['content']

    for mantra_row, swara_row in zip(all_mantra_rows, all_swara_rows):
        
        is_verse_end = False
        if mantra_row:
            for token in reversed(mantra_row):
                if "SPACE_TOKEN" in token: continue
                if "॥" in token or "||" in token:
                    is_verse_end = True
                break 

        for i, (mantra_chunk, swara_chunk) in enumerate(zip(mantra_row, swara_row)):
            text_part = mantra_chunk.strip().replace(":", "ः")
            # Clean Stack Arguments
            text_part = clean_stack_arg(text_part)
            text_part = format_dandas(text_part)
            swara_part = swara_chunk.strip().replace('{}', '')
            swara_part = clean_stack_arg(swara_part)

            if "SPACE_TOKEN" in text_part:
                paragraph_buffer.append("")
                continue 

            extras = "" 
            clean_word = text_part.replace('{', '').replace('}', '').strip()
            
            if clean_word in footnote_dict:
                extras = f"\\footnote{{{footnote_dict[clean_word]}}}"
            elif clean_word in footnotes_map:
                extras = f"\\footnote{{{footnotes_map[clean_word]}}}"

            if swara_part:
                clean_swara = swara_part.replace('{', '').replace('}', '')
                if len(clean_swara) > 1:
                    stack = f"\\stackleft{{{text_part}}}{{{swara_part}}}\\hspace{{0.05em}}"
                else:
                    stack = f"\\stackcenter{{{text_part}}}{{{swara_part}}}"
            else:
                stack = text_part
            
                      
            token = stack + extras

            if token and token != '{}':
                paragraph_buffer.append(token)
                paragraph_buffer.append("\\allowbreak")

        if is_verse_end:
            full_paragraph = "".join(paragraph_buffer)
            formatted_output.append(f"{{\\noindent\\justifying\\sloppy {full_paragraph}}}")
            formatted_output.append(r"\par\vspace{0.5em}") 
            paragraph_buffer = [] 

    if paragraph_buffer:
        full_paragraph = "".join(paragraph_buffer)
        formatted_output.append(f"{{\\noindent\\justifying\\sloppy {full_paragraph}}}")
        formatted_output.append(r"\par\vspace{0.5em}")

    return "\n\n".join(formatted_output)

def format_mantra_sets_text(subsection,section_title,subsection_title):
    
    formatted_sets = []
    
    mantra_sets = subsection.get('mantra_sets', [])
    mantra_array = []
    for mantra_set in mantra_sets:
        mantra_words = mantra_set.get('mantra-words', [])
        mantra=""
        for w,word in enumerate(mantra_words):
            actual_word = word.get('word', 'WORD')
            
            mantra+=" " +actual_word
        mantra_array.append(mantra)
    
        
    corrected_mantra_sets = subsection.get('corrected-mantra_sets', [])
    corrected_mantra_array = []
    if corrected_mantra_sets is not None:
        for corrected in corrected_mantra_sets:
            corrected_mantra = corrected.get('corrected-mantra', '')
            if corrected_mantra:
                corrected_mantra_array.append(corrected_mantra)
                
    if len(corrected_mantra_array) != 0:
        mantra_array = corrected_mantra_array
    formatted_sets.append(f"\n#Start of Mantra Sets -- {subsection_title} ## DO NOT EDIT")
    for mantra in mantra_array:
        formatted_sets.append(mantra)
    formatted_sets.append(f"\n#End of Mantra Sets -- {subsection_title} ## DO NOT EDIT")
    return "\n".join(formatted_sets)

def main():
    if len(sys.argv) > 1:
       input_file = sys.argv[1]
    else:
        input_file = "corrections_003_out.json"
        
    template_dir="pdf_templates"
    text_template_dir="text_templates"
    
    templateFile_Grantha=f"{template_dir}/Grantha_main.template"
    templateFile_Devanagari=f"{template_dir}/Devanagari_main.template"
    templateFile_Tamil=f"{template_dir}/Tamil_main.template"
    templateFile_Malayalam=f"{template_dir}/Malayalam_main.template"
    
    text_templateFile_Devanagari=f"{text_template_dir}/Devanagari_main.template"

    outputdir="output_text"
    logdir="pdf_logs"
    
    latex_jinja_env = jinja2.Environment(
    block_start_string = r'\BLOCK{',
    block_end_string = '}',
    variable_start_string = r'\VAR{',
    variable_end_string = '}',
    comment_start_string = r'\#{',
    comment_end_string = '}',
    line_statement_prefix = '%-',
    line_comment_prefix = '%#',
    trim_blocks = True,
    lstrip_blocks=True,
    autoescape = False,
    loader = jinja2.FileSystemLoader(os.path.abspath('.')),
    extensions=['jinja2.ext.loopcontrols']
    )
    latex_jinja_env.filters["my_encodeURL"] = my_encodeURL
    latex_jinja_env.filters["escape_for_latex"] = escape_for_latex
    latex_jinja_env.filters["format_mantra_sets"] = format_mantra_sets
    latex_jinja_env.filters["format_mantra_sets_text"] = format_mantra_sets_text
    latex_jinja_env.filters["replacecolon"] = replacecolon
    
    # invocation=''
    # title=''
    # print("running xelatex with ",samhitaTemplateFile)
    # template_file = latex_jinja_env.get_template(templateFile_Grantha)
    # supersections = data_Grantha.get('supersection', {})
    # CreatePdf(template_file,f"Grantha","Grantha",supersections)

    
    template_file = latex_jinja_env.get_template(templateFile_Devanagari)
    text_template_file = latex_jinja_env.get_template(text_templateFile_Devanagari)
    
    ts_string_Devanagari = Path(input_file).read_text(encoding="utf-8")
    data_Devanagari = json.loads(ts_string_Devanagari)
    
    supersections = data_Devanagari.get('supersection', {})
    supersections = sanitize_data_structure(supersections)
    
    current_os = platform.system() 
    CreatePdf(template_file,f"Devanagari","Devanagari",supersections, current_os=current_os)
    CreateTextFile(text_template_file,f"Devanagari","Devanagari",supersections)
    
    # ts_string_Tamil = Path("output_text/final-Tamil.json").read_text(encoding="utf-8")
    # data_Tamil = json.loads(ts_string_Tamil)
    # template_file = latex_jinja_env.get_template(templateFile_Tamil)
    # supersections = data_Tamil.get('supersection', {})
    # CreatePdf(template_file,f"Tamil","Tamil",supersections)

    # ts_string_Malayalam = Path("output_text/final-Malayalam.json").read_text(encoding="utf-8")
    # data_Malayalam = json.loads(ts_string_Malayalam)
    # template_file = latex_jinja_env.get_template(templateFile_Malayalam)
    # supersections = data_Malayalam.get('supersection', {})
    # CreatePdf(template_file,f"Malayalam","Malayalam",supersections)

if __name__ == "__main__":
    main()