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

'''
Bug : Need to add the english prefix into the json tree
'''
def combine_ardhaksharas(text):
    """
    Combine ardhaksharas (half consonants) with following characters to form complete units.
    For example: ग् + ना -> ग्ना as a single unit
    """
    grapheme_list = list(grapheme.graphemes(text))
    combined_list = []
    i = 0
    
    while i < len(grapheme_list):
        current_grapheme = grapheme_list[i]
        
        # Check if current grapheme ends with halant or common ardhakshara combinations
        if (current_grapheme.endswith('\u094D') or  # halant/virama character
            current_grapheme.endswith('र्') or  # र् (ra halant)
            current_grapheme.endswith('य्') or  # य् (ya halant) 
            current_grapheme.endswith('व्') or  # व् (va halant)
            current_grapheme.endswith('ल्')):   # ल् (la halant)
            # Combine with next grapheme if it exists
            if i + 1 < len(grapheme_list):
                combined_grapheme = current_grapheme + grapheme_list[i + 1]
                combined_list.append(combined_grapheme)
                i += 2  # Skip the next grapheme as it's already combined
            else:
                combined_list.append(current_grapheme)
                i += 1
        else:
            combined_list.append(current_grapheme)
            i += 1
    
    return combined_list

def my_encodeURL(url,param1,value1,param2,value2):
    #x=urllib.parse.quote(URL)
    #print("URL is ",url, "param1 is ",param1,"value1 is ",value1,"param2 is ",param2,"value2 is ",value2)
    #x=urllib.parse.quote(url+"?"+param1+"="+value1+"&"+param2+"="+value2)
    req = PreparedRequest()
    params = {param1:value1,param2:value2}
    req.prepare_url(url, params)
    #print(req.url)
    return req.url

def my_format(my_number):
    my_int=int(my_number)
    my_string=f"{my_int:3d}"
    return my_string

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


def replacecolon(data):
    if isinstance(data,str):
        data=data.replace(":","ः")
    return data

def format_mantra_sets(subsection, section_title, subsection_title):
    global MAX_COLUMNS
    issue_url = 'https://github.com/hvram1/jaimineeyasamavedam/issues/new'

    number_pattern = re.compile(r'॥\s*(\d+)\s*॥')
    
    # Pattern to handle the case where a word like "word(swara)" might be missed by the tokenization
    # We rely on the core tokenization loop below instead of a pre-processing step.

   
    formatted_sets = []
    mantra_for_issues = ""
    mantra_sets = subsection.get('mantra_sets', [])
    mantra_array = []
    
    # ... (Code for loading mantra_array from input data remains the same) ...
    for mantra_set in mantra_sets:
        mantra_words = mantra_set.get('mantra-words', [])
        mantra = ""
        for w, word in enumerate(mantra_words):
            actual_word = word.get('word', 'WORD')
            mantra += " " + actual_word
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
        
    for mantra in mantra_array:
        errorFlag = False
        mantra_for_issue = ""
        mantra_number = "" 

        # Clean up the mantra
        mantra = mantra.replace("{[}", "X")
        mantra = mantra.replace(":", "ः")
       
        
        # Extract and remove mantra numbers
        if match_instance := re.search(number_pattern, mantra):
            #mantra_number = match_instance.group(0).strip() # Capture the number (e.g., "॥1॥")
            mantra_number = f"॥ {match_instance.group(1).strip()} ॥" # Capture and reformat (e.g., "॥ 1 ॥")
            mantra = mantra.replace(match_instance.group(0), "") # Remove it from the mantra string

         # ADD THIS LINE HERE:
        MAX_COLS_PER_LINE = 125  # Adjust this based on page width
        
             
        # --- NEW "ALIGNED TWO-ROW" LOGIC START ---
        
        mantra_row_cols = []
        swara_row_cols = []
        i = 0
        
        while i < len(mantra):
            # 1. Skip whitespace
            if mantra[i].isspace():
                i += 1
                continue
            
            
            # 2. Check for danda
            if mantra[i] in '।॥|':
                
                # --- ADD A NEW SPACER COLUMN ---
                # Add ONE blank column with a fixed 1em space
                mantra_row_cols.append(r'{\hspace{1em}}')
               
               
               # <ADDED JUST NOW> Add empty cell in swara row below the spacer
                swara_row_cols.append(r'{\hspace{1em}}') # Empty cell below the spacer
                # ---------------------------------

                # Add danda column (with \quad for space AFTER)
                danda_token = r'{\hspace{3pt}\textbf{' + mantra[i] + r'}\hspace{3pt}\quad}'
                mantra_row_cols.append(danda_token)
                swara_row_cols.append('{}') # Empty cell in swara row
                
                i += 1
                continue
            








            # 3. Check for pattern: [Word] + (Swara)
            match = re.match(r'\s*([^\s()।॥]+)\(([^)]+)\)', mantra[i:])

            if match:
                # Found a word with a swara
                mantra_word = match.group(1) # e.g., 'आया'
                swara_word = match.group(2)  # e.g., 'थाच्'
            
                # Split the word into graphemes to isolate the last character
                mylist = combine_ardhaksharas(mantra_word)
                
                if len(mylist) > 0:
                    # Isolate the target grapheme (the character the swara goes under)
                    target_grapheme = mylist[-1]
                    # Get all preceding graphemes
                    preceding_graphemes = ''.join(mylist[0:-1])

                    # Add preceding graphemes to their own column
                    if preceding_graphemes:
                        mantra_row_cols.append(f'{{{preceding_graphemes}}}')
                        swara_row_cols.append('{}') # Empty cell below

                    # Add target grapheme and swara to the next column
                    mantra_row_cols.append(f'{{{target_grapheme}}}')
                    swara_row_cols.append(f'{{\\hspace{{2pt}}\\smallredfont {swara_word}}}')
                else:
                    # Fallback for empty mantra word
                    mantra_row_cols.append('{}')
                    swara_row_cols.append(f'{{\\hspace{{2pt}}\\smallredfont {swara_word}}}')

                # Advance index past the matched block
                i += len(match.group(0)) + (match.pos - mantra[i:].find(match.group(0)))
            
            # 4. Continuous text block (no swara)
            else:
                token_start = i
                
                while i < len(mantra):
                    if mantra[i] in '।॥|(' or mantra[i].isspace():
                        break
                    i += 1
                
                continuous_text = mantra[token_start:i].strip()

                if continuous_text:
                    mantra_row_cols.append(f'{{{continuous_text}}}')
                    swara_row_cols.append('{}') # Empty cell below
                if i == token_start:
                    i += 1  # Avoid infinite loop
        
        # --- NEW "ALIGNED TWO-ROW" LOGIC END ---            
                   
        # --- TABLE ASSEMBLY WITH LINE WRAPPING START ---
        
        if len(mantra_row_cols) > 0:
            all_tables = []
            
            # Split columns into chunks for line wrapping
            for chunk_start in range(0, len(mantra_row_cols), MAX_COLS_PER_LINE):
                chunk_end = min(chunk_start + MAX_COLS_PER_LINE, len(mantra_row_cols))
                
                mantra_chunk = mantra_row_cols[chunk_start:chunk_end]
                swara_chunk = swara_row_cols[chunk_start:chunk_end]
                
                if len(mantra_chunk) > 0:
                    # Join columns in this chunk
                    mantra_row_str = '&'.join(mantra_chunk)
                    swara_row_str = '&'.join(swara_chunk)
                    
                    # Combine rows with line break
                    result_mantra = f'{mantra_row_str} \\\\[0.1ex] {swara_row_str}'
                    
                    # Create dynamic column spec for this chunk
                    num_cols = len(mantra_chunk)
                    dynamic_col_spec = "l" * num_cols
                    
                    # Build table for this chunk
                    tbl_start_string = f'\\begin{{tabular}}[t]{{{dynamic_col_spec}}}'
                    tbl_end_string = '\\end{tabular}'
                    
                    table_str = f'{tbl_start_string}{result_mantra}\\\\{tbl_end_string}'
                    all_tables.append(table_str)
            
            # Join all table chunks
            if all_tables:
                if mantra_number:
                    # Add number at the end of the last line
                    page_string = '\n'.join(all_tables) + f'\\hfill \\textbf{{{mantra_number}}}'
                else:
                    page_string = '\n'.join(all_tables)
                    
                formatted_sets.append(page_string)

        mantra_for_issues += "\n\n" + mantra_for_issue
    
    # ... (Rest of the function for issue link generation remains the same) ...
    issue_body = (
        f' This is the current swara position . {mantra_for_issues}. \n\n'
        f'Please enter the new swara in the same format (i.e.) mantra(swara)mantramantra(swara) and log a correction'
    )
    issue_link = my_encodeURL(issue_url, "title", "Issue in Swara section=" + section_title + ",subsection=" + subsection_title, "body", issue_body)
    latex_issue_link = escape_for_latex(issue_link)
    
   # if errorFlag == False:
   #     col_value = f"\\textbf{{ \\href{{{latex_issue_link}}}{{ \\emoji {{lady-beetle}}}} }}"
   # else:
     #   col_value = f"\\textbf{{ \\href{{{latex_issue_link}}}{{ \\emoji {{x}}}} }}"
    
    #formatted_sets.append("\n")
    #formatted_sets.append(col_value)
    
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
        input_file = "corrections_003.json"
    
    ts_string_Devanagari = Path(input_file).read_text(encoding="utf-8")
   
    data_Devanagari = json.loads(ts_string_Devanagari)
    template_file = latex_jinja_env.get_template(templateFile_Devanagari)
    text_template_file = latex_jinja_env.get_template(text_templateFile_Devanagari)
    
    supersections = data_Devanagari.get('supersection', {})
    current_os = platform.system() # Gets "Windows", "Darwin" (Mac), or "Linux"
    CreatePdf(template_file,f"Devanagari","Devanagari",supersections, current_os=current_os)
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