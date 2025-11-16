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
    parse_mantra_for_latex
)
# --- End new import ---
'''
Bug : Need to add the english prefix into the json tree
'''

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
            '''
            result=CreatePdf(templateFileName_tex,f"TS_{kandaInfo}_{prasnaInfo}","Compilation",prasna)
            
            if result != 0:
                exit_code=1
                print("stopping the process since there is an error at",kandaInfo,prasnaInfo)
                return
            '''
                       
def CreatePdf (templateFileName,name,DocfamilyName,data, current_os="Windows", pada_config={}):
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
    document = template.render(supersections=data, os=current_os, pada_config=pada_config)
    

    tmpdirname="."
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpfilename=f"{tmpdirname}/{TexFileName}"

        with open(tmpfilename,"w",encoding="utf-8") as f:
            f.write(document)
        #result = subprocess.Popen(["latexmk","-lualatex", "--interaction=nonstopmode","--silent",tmpfilename],cwd=tmpdirname)
        #result.wait()
        src_pdf_file=Path(f"{tmpdirname}/{PdfFileName}")
        dst_pdf_file=Path(f"{outputdir}/{PdfFileName}")
        src_log_file=Path(f"{tmpdirname}/{LogFileName}")
        dst_log_file=Path(f"{logdir}/{LogFileName}")
        #src_toc_file=Path(f"{tmpdirname}/{TocFileName}")
        #dst_toc_file=Path(f"{outputdir}/{TocFileName}")
        src_tex_file=Path(f"{tmpdirname}/{TexFileName}")
        dst_tex_file=Path(f"{outputdir}/{TexFileName}")
        
        #if result.returncode != 0:
        #    print('Exit-code not 0  check Code!',src_tex_file)
        #    exit_code=1
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
        #src_toc_file.rename(dst_toc_file)
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
        #result = subprocess.Popen(["latexmk","-lualatex", "--interaction=nonstopmode","--silent",tmpfilename],cwd=tmpdirname)
        #result.wait()
        #src_pdf_file=Path(f"{tmpdirname}/{PdfFileName}")
        #dst_pdf_file=Path(f"{outputdir}/{PdfFileName}")
        #src_log_file=Path(f"{tmpdirname}/{LogFileName}")
        #dst_log_file=Path(f"{logdir}/{LogFileName}")
        #src_toc_file=Path(f"{tmpdirname}/{TocFileName}")
        #dst_toc_file=Path(f"{outputdir}/{TocFileName}")
        src_text_file=Path(f"{tmpdirname}/{TextFileName}")
        dst_text_file=Path(f"{outputdir}/{TextFileName}")
        
        #if result.returncode != 0:
        #    print('Exit-code not 0  check Code!',src_tex_file)
        #    exit_code=1
        path = Path(src_text_file)
        if path.is_file():
            if dst_text_file.exists():
                dst_text_file.unlink()
            src_text_file.rename(dst_text_file)  
        #path = Path(src_pdf_file)
        #if path.is_file():      
        #    src_pdf_file.rename(dst_pdf_file)
        #path = Path(src_log_file)
        #if path.is_file():
        #    src_log_file.rename(dst_log_file)
        #src_toc_file.rename(dst_toc_file)
    return exit_code


'''
if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            escaped_key = escape_for_latex(key) if isinstance(key, str) else key
            new_data[escaped_key] = escape_for_latex(value)
        return new_data
'''
def escape_for_latex(data):
    if isinstance(data, dict):
        new_data = {}
        for key in data.keys():
            new_data[key] = escape_for_latex(data[key])
        return new_data
    elif isinstance(data, list):
        return [escape_for_latex(item) for item in data]
    elif isinstance(data, str):
        # Adapted from https://stackoverflow.com/q/16259923
        latex_special_chars = {
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\^{}",
            "\\": r"\textbackslash{}",
            "\n": "\\newline%\n",
            "-": r"{-}",
            "\xA0": "~",  # Non-breaking space
            "[": r"{[}",
            "]": r"{]}",
        }
        return "".join([latex_special_chars.get(c, c) for c in data])

    return data

# Refactored function to format mantra sets with dynamic pada limits
def format_mantra_sets(subsection, supersection_title, section_title, subsection_title, pada_config):
    
    #--- 1. Call the parsing function to get processed data ---
    all_mantra_rows, all_swara_rows = parse_mantra_for_latex(
        subsection, 
        supersection_title, 
        section_title, 
        subsection_title, 
        pada_config
    )
    
    formatted_sets = []
    all_tables = []
    
    # --- TABLE ASSEMBLY LOGIC START ---
    # What happens to this?     
    #if current_mantra_row:
        #all_mantra_rows.append(current_mantra_row)
        #all_swara_rows.append(current_swara_row)
      
    max_cols = 0
    if all_mantra_rows:
        max_cols = max(len(row) for row in all_mantra_rows)  
    
    if max_cols == 0:
        return "" 
        
    fixed_col_spec = "l" * max_cols 

    for mantra_chunk, swara_chunk in zip(all_mantra_rows, all_swara_rows):
        
        if len(mantra_chunk) > 0:
            
            padding_needed = max_cols - len(mantra_chunk)
            if padding_needed > 0:
                padding = ['{}'] * padding_needed
                mantra_chunk.extend(padding)
                swara_chunk.extend(padding)

            mantra_row_str = '&'.join(mantra_chunk)
            swara_row_str = '&'.join(swara_chunk)
            result_mantra = f'{mantra_row_str} \\\\[0.2ex] {swara_row_str}'
            
            tbl_start_string = f'\\begin{{tabular}}[t]{{{fixed_col_spec}}}'
            tbl_end_string = '\\end{tabular}'
            
            table_str = f'{tbl_start_string}{result_mantra}\\\\{tbl_end_string}'
            all_tables.append(table_str)
        
        tables_string = "\n\n".join(all_tables)
        
        #if mantra_number and all_tables:
        #    tables_string = tables_string + f'\\hfill \\textbf{{{mantra_number}}}'

    formatted_sets.append(tables_string)
    
    # --- TABLE ASSEMBLY LOGIC END ---

    # --- Issue Link Logic (Moved to end) ---
    #issue_body = (
       # f'Issue in: {supersection_title} - {subsection_title}.\n\n'
      #  f'Please enter the new swara in the same format (i.e.) mantra(swara)mantramantra(swara) and log a correction.'
    #)
    #issue_link = my_encodeURL(issue_url, "title", f"{supersection_title} - {subsection_title}", "body", issue_body)
    #latex_issue_link = issue_link

    #formatted_sets.append(f"\\href{{{latex_issue_link}}}{{Log an Issue}}")
    
    return "\n\n".join(formatted_sets)

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
    
        


#CreateGhanaFiles()

#CreateCompilation()

#CreateTxt()

#return exit_code

def main():
    # Example usage of the functions
    #ts_string = Path("TS_withPada.json").read_text(encoding="utf-8")
    #parseTree = json.loads(ts_string)

    ts_string_Grantha = Path("output_text/rewritten_final-Grantha.json").read_text(encoding="utf-8")
    data_Grantha = json.loads(ts_string_Grantha)

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
    
    invocation=''
    title=''
    #print("running xelatex with ",samhitaTemplateFile)
    #template_file = latex_jinja_env.get_template(templateFile_Grantha)
   
    #supersections = data_Grantha.get('supersection', {})
    
    #CreatePdf(template_file,f"Grantha","Grantha",supersections)

    
    
# Get the filename from command line argument
    if len(sys.argv) > 1:
       input_file = sys.argv[1]
    else:
    # Default fallback if no argument provided
        input_file = "corrections_003_out.json"
    
    ts_string_Devanagari = Path(input_file).read_text(encoding="utf-8")
   
    data_Devanagari = json.loads(ts_string_Devanagari)
    
    # Load the new pada config file
    try:
        pada_config_string = Path("pada_config.json").read_text(encoding="utf-8")
        pada_config = json.loads(pada_config_string)
    except Exception as e:
        print(f"Warning: Could not load pada_config.json. Using default. Error: {e}")
        pada_config = {} # Load an empty dict on failure
    
    # Ensure a DEFAULT key exists, otherwise set it to 4
    if "DEFAULT" not in pada_config:
        pada_config["DEFAULT"] = 4
    
    template_file = latex_jinja_env.get_template(templateFile_Devanagari)
    text_template_file = latex_jinja_env.get_template(text_templateFile_Devanagari)
    
    supersections = data_Devanagari.get('supersection', {})
    current_os = platform.system() # Gets "Windows", "Darwin" (Mac), or "Linux"
    CreatePdf(template_file,f"Devanagari","Devanagari",supersections, current_os=current_os, pada_config=pada_config)
    CreateTextFile(text_template_file,f"Devanagari","Devanagari",supersections)
    
    #ts_string_Tamil = Path("output_text/final-Tamil.json").read_text(encoding="utf-8")
    
    #data_Tamil = json.loads(ts_string_Tamil)
    #template_file = latex_jinja_env.get_template(templateFile_Tamil)
    
    #supersections = data_Tamil.get('supersection', {})
    #CreatePdf(template_file,f"Tamil","Tamil",supersections)
    
    #ts_string_Malayalam = Path("output_text/final-Malayalam.json").read_text(encoding="utf-8")
    
    #data_Malayalam = json.loads(ts_string_Malayalam)
    #template_file = latex_jinja_env.get_template(templateFile_Malayalam)
    
    #supersections = data_Malayalam.get('supersection', {})
    #CreatePdf(template_file,f"Malayalam","Malayalam",supersections)


if __name__ == "__main__":
    main()
    
   
