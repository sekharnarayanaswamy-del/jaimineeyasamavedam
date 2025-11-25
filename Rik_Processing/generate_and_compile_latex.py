import subprocess
import os
import re


# ----------------------------------------------------
# 1. Utility function: Accent Replacements
# ----------------------------------------------------
def replace_accents(text):
    """
    Replaces ASCII markers (1), (2), etc., with LaTeX commands.
    We do NOT add any extra spacing or breaks here.
    """
    replacements = [
        ('(1)', r'\accentmark{22}{\char"0951}'),  # Swarita
        ('(2)', r'\accentmark{27}{\char"1CD2}'),  # Anudatta
        ('(3)', r'\accentmark{20}{\char"1CF8}'),  # Kampa
        ('(4)', r'\accentmark{20}{\char"1CF9}'),  # Trikampa
    ]
  
    for marker, replacement in replacements:
        text = text.replace(marker, replacement)
    
    return text

# ----------------------------------------------------
# 2. NEW: Consecutive Accent Handler (Updated)
# ----------------------------------------------------
def handle_consecutive_accents(text):
    """
    Inserts a small \kern to separate specific accent transitions 
    that are prone to visual overlap.
    
    Handled Transitions:
    1. Anudatta (2) -> Anudatta (2)
    2. Swarita (1)  -> Anudatta (2) [NEW]
    """
    
    # CASE A: Anudatta (2) followed by Anudatta (2)
    # ---------------------------------------------
    # Pattern: Match (2) ONLY if followed by 1-5 chars and then another (2)
    pat_2_2 = r'(\(2\))(?=[^()]{1,5}\(2\))'
    text = re.sub(pat_2_2, r'\1\\kern0.15em', text)

    # CASE B: Swarita (1) followed by Anudatta (2)
    # ---------------------------------------------
    # Pattern: Match (1) ONLY if followed by 1-5 chars and then (2)
    # This prevents the vertical line of Swarita from hitting the line of Anudatta
    pat_1_2 = r'(\(1\))(?=[^()]{1,5}\(2\))'
    text = re.sub(pat_1_2, r'\1\\kern0.15em', text)

     # CASE C:  Anudatta (2) followed by Kamba (3) or Trikamba (4)
    # ---------------------------------------------
    # Pattern: Match (1) ONLY if followed by 1-5 chars and then (2)
    # This prevents the vertical line of Swarita from hitting the line of Anudatta
    pat_2_3= r'(\(2\))(?=[^()]{1,5}\(3\))'
    text = re.sub(pat_2_3, r'\1\\kern0.15em', text)

    pat_2_4= r'(\(2\))(?=[^()]{1,5}\(4\))'
    text = re.sub(pat_2_4, r'\1\\kern0.15em', text)
    
    return text
# ----------------------------------------------------
# 2. Utility function: Format Header
# ----------------------------------------------------
def format_header(text):
    """Format the header text (first 4 lines) as bold and centered."""
    lines = text.split('\n')
    if len(lines) >= 4:
        header_line1 = lines[0].strip()
        header_line2 = lines[1].strip()
        header_line3 = lines[2].strip()
        header_line4 = lines[3].strip()
        
        formatted_header = (
            r'\begin{center}' + '\n' +
            r'\Huge\textbf{' + header_line1 + r'}\\' + '\n' +
            r'\Large\textbf{' + header_line2 + r'}\\' + '\n' +
            r'\Large\textbf{' + header_line3 + r'}\\' + '\n' +
            r'\Large\textbf{' + header_line4 + r'}\\' + '\n' +
            r'\end{center}' + '\n' +
            r'\vspace{2\baselineskip}' + '\n\n'
        )
        return formatted_header + '\n'.join(lines[4:])
    else:
        return text

# ----------------------------------------------------
# 3. Utility function: Line Breaks (With Clearpage for Atha)
# ----------------------------------------------------
def add_enhanced_linebreaks(text):
    # --- STEP 0: NORMALIZE ---
    text = text.replace('II.', '॥').replace('II', '॥').replace('||', '॥')
    text = text.replace('|', r'।\ ').replace('।', r'।\ ')
    text = text.strip()
    danda = r'॥'

    # --- STEP 1: DE-FRAGMENTATION (Fix Broken Headers) ---
    # Merge "||" + "Atha/Iti" if split across lines
    text = re.sub(r'॥\s+((?:अथ|इति|समाप्तः))', r'॥ \1', text)
    # Merge "Text..." + "||" (Orphan closing danda)
    text = re.sub(r'(समाप्तः|खण्डः|प्रारम्भः)\s*\n\s*॥', r'\1 ॥', text)

    # --- STEP 2: GLUE MANTRA NUMBERS TO PRECEDING TEXT ---
    # Finds: (Any Space/Newline) + (|| Digits ||)
    # Replaces with: (Space) + (|| Digits ||)
    mantra_block_pattern = r'॥\s*[\d\u0966-\u096F]+\s*॥'
    text = re.sub(r'\s+(' + mantra_block_pattern + ')', r' \1', text)

    # --- STEP 3: WRAP SPECIAL BLOCKS IN \mbox{} ---
    
    # 3a. MANTRA NUMBERS: Force Spaces & Protect
    # || 10 ||  ->  \mbox{॥ 10 ॥}
    text = re.sub(r'॥\s*([\d\u0966-\u096F]+)\s*॥', r'\\mbox{॥ \1 ॥}', text)
    
    # 3b. HEADERS: Protect & Add Clearpage for Atha
    # We use a single pass to handle Iti, Samaptah, and Atha blocks.
    def mbox_wrapper_headers(match):
        content = match.group(0)
        # Normalize internal spaces to single space
        content = re.sub(r'\s+', ' ', content)
        
        # Create the wrapped block
        wrapped_block = r'\mbox{' + content + r'}'
        
        # CHECK: If this block contains "Atha", prepend \clearpage
        if 'अथ' in content:
            return r'\clearpage' + '\n' + wrapped_block
            
        return wrapped_block

    # Regex matches: || ... (Atha OR Iti OR Samaptah) ... ||
    pat_headers = r'॥[^॥]*?(?:अथ|इति|समाप्तः)[^॥]*?॥'
    text = re.sub(pat_headers, mbox_wrapper_headers, text, flags=re.DOTALL)

    # --- STEP 4: ADD LINE BREAKS (\\) ---
    # Add a LaTeX break ` \\` after every protected block (\mbox)
    # This ensures headers and mantra numbers end their lines immediately.
    text = re.sub(r'(\\mbox\{.*?\})', r'\1 \\\\', text)

    # --- STEP 5: CLEANUP ---
    # Fix double breaks
    text = re.sub(r'\\\\\s*\\\\', r'\\\\', text)
    # Remove orphan dandas on empty lines
    text = re.sub(r'(?m)^\s*॥\s*$', '', text)
    # Clean paragraph spacing
    text = re.sub(r'\n\s*\n\s*\n', r'\n\n', text)
    
    return text.lstrip()

# ----------------------------------------------------
# 4. Utility function: Reduce Trailing Whitespace (UPDATED)
# ----------------------------------------------------
def eliminate_trailing_whitespace(text):
    zero_space = r'\\hspace{0pt}' 
    
    # 1. Handle standalone Dandas
    text = re.sub(r'\s(॥)', zero_space + r'\1', text)
    
    # 2. Handle Mantra Numbers (Adjusted for the new spacing)
    # Matches: (Space) (|| Space Digits Space ||)
    # We apply the zero_space buffer before the leading Danda
    mantra_number_pattern = r'(\s)(॥\s*[\u0966-\u096F]+\s*॥)'
    text = re.sub(mantra_number_pattern, zero_space + r'\2', text)
    
    return text
  
# ----------------------------------------------------
# 4. Utility function: Reduce Trailing Whitespace
# ----------------------------------------------------

def reduce_trailing_whitespace(text):
    #"""
    #Inserts LaTeX \allowbreak and negative space (\!) before Danda (॥) 
    #or mantra numbers to force a line break opportunity.
    #"""
    
    # LaTeX command to allow a break and slightly pull back space
    break_command = r'\\allowbreak\\!'
    
    # 1. Targets the space before a standalone Danda: " ॥" -> "\allowbreak\!॥"
    # We replace the leading space and insert the break command.
    text = re.sub(r'\s(॥)', break_command + r'\1', text)

    # 2. Targets the space before the mantra number block: " ॥ १ ॥" -> "\allowbreak\!॥ १ ॥"
    mantra_number_pattern = r'(\s)(॥\s*[\u0966-\u096F][\u0966-\u096F\s]*॥)'
    
    # We replace the leading space and insert the break command.
    text = re.sub(mantra_number_pattern, break_command + r'\2', text)
    
    return text

    # ----------------------------------------------------
    # NEW UTILITY: Remove Internal Spaces (Continuous Script - Samhita aka Scriptio continua)
    # ----------------------------------------------------
def remove_mantra_spaces(text):
    """
    Removes all spaces within mantra lines to create continuous text.
    Preserves spaces in:
    1. The Header (first 4 lines)
    2. Colophons (lines containing 'इति', 'अथ', 'समाप्तः')
    """
    lines = text.split('\n')
    processed_lines = []
    
    # Keywords that indicate a footer/header line where spaces should remain
    # We check for these to avoid collapsing "Iti Prathamah..." into "ItiPrathamah..."
    preserve_keywords = ['इति', 'अथ', 'समाप्तः']
    
    for i, line in enumerate(lines):
        # 1. Preserve the main document header (first 4 lines)
        if i < 4:
            processed_lines.append(line)
            continue
            
        # 2. Check if this line is a Colophon/Structure line
        if any(keyword in line for keyword in preserve_keywords):
            processed_lines.append(line)
            continue
        
        # 3. It is a Mantra line: Remove all spaces and tabs
        # This turns "अग्निमीळे पुरोहितं" into "अग्निमीळेपुरोहितं"
        clean_line = line.replace(' ', '').replace('\t', '')
        
        processed_lines.append(clean_line)
        
    return '\n'.join(processed_lines)


#----------------------------------------------------
# 7. CHECK OUTPUT PERMISSION (NEW FUNCTION)
# ----------------------------------------------------
def get_writable_filename(base_filename):
    """
    Checks if the PDF file is open/locked. If so, asks the user for a new name.
    """
    while True:
        pdf_filename = f"{base_filename}.pdf"
        
        # If the file doesn't exist, we are good to go.
        if not os.path.exists(pdf_filename):
            return base_filename

        # If it exists, try to open it in append mode to check for lock.
        try:
            with open(pdf_filename, 'a'):
                pass # Success, file is writable
            return base_filename
        except PermissionError:
            print(f"\nERROR: The file '{pdf_filename}' is open in another program.")
            print("Please close the PDF or provide a new filename.")
            new_name = input("Enter new base filename (or press Enter to retry): ").strip()
            
            if new_name:
                base_filename = new_name
            # If they just press Enter, we loop back and try the same name again (hoping they closed it)

# ----------------------------------------------------
# 5. Main processing function
# ----------------------------------------------------
def generate_and_compile_latex(input_text, base_filename='vedic_output'):
    """
    Generate LaTeX file with processed text and compile it using LuaLaTeX.
    """
    
    base_filename = get_writable_filename(base_filename)
    tex_filename = f'{base_filename}.tex'

    #-- FIX: Corrected processing pipeline ---
    # 1. Format header FIRST
    processed_text = format_header(input_text)
    # 2. NEW: Remove spaces (Create Continuous Script)
    # We do this BEFORE adding LaTeX commands to avoid breaking code.
    processed_text = remove_mantra_spaces(processed_text)
    
    # 1. First, detect consecutive accents and inject \kern ONLY for those cases
    processed_text = handle_consecutive_accents(processed_text)
    
    # 2. Then replace all accents with LaTeX commands
    # (The \kerns we added above are preserved)
    processed_text = replace_accents(processed_text)
   
    processed_text = add_enhanced_linebreaks(processed_text)

    # 6. Handle trailing whitespace LAST
    processed_text = eliminate_trailing_whitespace(processed_text)
    # --- End of pipeline fix ---


    # Get the absolute path to the font directory
    font_path = r'C:/Users/sekha/OneDrive/Documents/GitHub/jaimineeyasamavedam/Rik_Processing/AdishilaVedic/'
    
    # Create LaTeX document
    latex_content = r'''\documentclass[12pt,a4paper]{article}
\usepackage{fontspec}
\usepackage[margin=1in]{geometry}
\usepackage{setspace}
\onehalfspacing

% Set the main font to Adishila Vedic with Devanagari script support
\setmainfont{Adishila Vedic}[
    Path = ''' + font_path + r''',
    Extension = .ttf,
    UprightFont = AdishilaVedic,
    BoldFont = AdishilaVedicBold,
    Script=Devanagari,
    Renderer=HarfBuzz,
]

% Command to format accent marks with larger size and bold
\newcommand{\accentmark}[2]{%
    {\fontsize{#1pt}{#1pt}\selectfont\bfseries\addfontfeature{FakeBold=3}#2}%
}

% --- ACCENT OVERLAP ADJUSTMENT ---
% Defines a small negative space (kerning) to pull the next character closer
% Used when two "danger" accents (Anudatta/Kampa) appear consecutively.
\newcommand{\accentadj}{\kern0.15ex}



% --- ADD THESE LINES FOR AGGRESSIVE LINE BREAKING ---
\setlength{\emergencystretch}{1em}
\tolerance=10000 % Allow high tolerance for stretching/shrinking lines
\pretolerance=10000 % Allow high pretolerance
\emergencystretch=1in % Allow emergency stretching to fit text
\setlength{\parindent}{0pt} % Removes the indentation at start of paragraphs
\raggedright                % Forces text to align left, ignoring right margin evenness

\begin{document}
\fontsize{18pt}{27pt}\selectfont

''' + processed_text + r'''

\end{document}
'''
    
    # Write LaTeX file
    try:
        with open(tex_filename, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        print(f"LaTeX file created: {tex_filename}")
        
        # Compile with LuaLaTeX
        print("Compiling with LuaLaTeX...")
        result = subprocess.run(['lualatex', '-interaction=nonstopmode', tex_filename], 
                              capture_output=True, text=True, check=True, encoding='utf-8')
        
        print(f"✓ PDF created successfully: {base_filename}.pdf")
        
    except FileNotFoundError:
        print("Error: LuaLaTeX not found.")
    except subprocess.CalledProcessError as e:
        print("Error during compilation:")
        if e.stdout: print('\n'.join(e.stdout.splitlines()[-10:]))
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    input_file = r'C:\Users\sekha\OneDrive\Documents\GitHub\jaimineeyasamavedam\Rik_Processing\vedic_text.txt'
    if os.path.exists(input_file):
        try:
            with open(input_file, 'r', encoding='UTF-8') as f:
                text = f.read()                      
            generate_and_compile_latex(text, 'vedic_output')
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"File not found: {input_file}")

#
