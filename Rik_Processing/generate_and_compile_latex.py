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
# 3. Utility function: Line Breaks (FIXED WITH FLATTENING)
# ----------------------------------------------------
def add_enhanced_linebreaks_4(text):
    # --- STEP 0: NORMALIZE ---
    text = text.replace('II.', '॥').replace('II', '॥').replace('||', '॥')
    text = text.replace('|', r'।\ ').replace('।', r'।\ ')
    text = text.lstrip()
    danda = r'॥'

    # --- STEP 0.5: AGGRESSIVE PRE-MERGE ---
    # Attempts to glue '||' and 'Atha' if they are separated by whitespace
    # We use [\|॥] to catch both standard and double pipe dandas
    text = re.sub(r'[\|॥]+\s+(अथ)', r'॥ \1', text)

    # --- DEFINE PATTERNS ---
    
    # 1. ITI PATTERN
    iti_pat = r'(' + danda + r'.*?इति.*?' + danda + r')'
    
    # 2. SAMAPTAH PATTERN
    samaptah_pat = r'((?:' + danda + r')?.*?समाप्तः.*?\s*' + danda + r')'
    
    # 3. ATHA PATTERN (The Flattening Fix)
    # We capture: (Optional Danda + Spaces) + Atha + ... + End Danda
    atha_pat = r'((?:' + danda + r'\s*)?अथ.*?' + danda + r')'
    
    mantra_pat = r'(' + danda + r'\s*[\d\u0966-\u096F]+\s*' + danda + r')'

    # --- STEP 1: GLUE 'ITI' + 'SAMAPTAH' ---
    double_footer_pattern = iti_pat + r'\s+' + samaptah_pat
    text = re.sub(double_footer_pattern, r'\1 \\\\*[1ex] \2 \\\\[1ex]\n', text, flags=re.DOTALL)

    # --- STEP 2: HANDLE REMAINING 'ITI' ---
    single_footer_pattern = iti_pat + r'(?!\s*\\)'
    text = re.sub(single_footer_pattern, r'\1 \\\\[1ex]\n', text, flags=re.DOTALL)
    
    # --- STEP 2.5: HANDLE REMAINING 'SAMAPTAH' ---
    single_samaptah_pattern = samaptah_pat + r'(?!\s*\\)'
    text = re.sub(single_samaptah_pattern, r'\1 \\\\[1ex]\n', text, flags=re.DOTALL)

    # --- STEP 3: HANDLE 'ATHA' HEADERS (NEW FLATTENING LOGIC) ---
    # Instead of a simple replace, we use a function to STRIP newlines inside the match.
    def flatten_atha(match):
        content = match.group(1)
        # Replace all newlines/tabs with a single space
        content = re.sub(r'\s+', ' ', content)
        return content.strip() + r' \\\\' + '\n'

    text = re.sub(atha_pat, flatten_atha, text, flags=re.DOTALL)

    # --- STEP 4: HANDLE MANTRA LINE BREAKS ---
    mantra_break_pattern = mantra_pat + r'(?!\s*\\\\)'
    text = re.sub(mantra_break_pattern, r'\1 \\\\\n', text)
    
    # --- STEP 4.5: FIX MANTRA NUMBER SPACING & PREVENT SPLITTING ---
    # We find || Digits || and wrap them in \mbox{...}
    # \mbox prevents LaTeX from breaking the line inside this block.
    number_spacing_pattern = r'॥\s*([\u0966-\u096F]+)\s*॥'
    text = re.sub(number_spacing_pattern, r'\\mbox{॥ \1 ॥}', text)

   # --- STEP 5: ORPHAN CLEANUP ---
    # Removes lines containing ONLY Dandas/Pipes
    orphan_pattern = r'(?m)^\s*[\|॥\u0964\u0965I]+\s*$'
    text = re.sub(orphan_pattern, '', text)
    
    # Clean up double dandas that might have merged
    text = re.sub(r'॥\s*॥', r'॥', text)
    # Remove excess newlines
    text = re.sub(r'\n\s*\n\s*\n', r'\n\n', text)
    
    return text.lstrip()        
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

def add_enhanced_linebreaks_2(text):
    # --- STEP 0: NORMALIZE ---
    text = text.replace('II.', '॥').replace('II', '॥').replace('||', '॥')
    text = text.replace('|', r'।\ ').replace('।', r'।\ ')
    text = text.lstrip()
    danda = r'॥'

    # --- DEFINE PATTERNS ---
    
    # 1. ITI PATTERN
    iti_pat = r'(' + danda + r'.*?इति.*?' + danda + r')'
    
    # 2. SAMAPTAH PATTERN
    samaptah_pat = r'((?:' + danda + r')?.*?समाप्तः.*?\s*' + danda + r')'
    
    # 3. ATHA PATTERN (STRICTER)
    # logic: Optional Danda -> whitespace -> Literal "Atha"
    # Removed ".*?" before Atha to ensure it grabs the IMMEDIATE preceding Danda
    atha_pat = r'((?:' + danda + r'\s*)?अथ.*?' + danda + r')'
    
    mantra_pat = r'(' + danda + r'\s*[\d\u0966-\u096F]+\s*' + danda + r')'

    # --- STEP 1: GLUE 'ITI' + 'SAMAPTAH' ---
    double_footer_pattern = iti_pat + r'\s+' + samaptah_pat
    text = re.sub(double_footer_pattern, r'\1 \\\\*[1ex] \2 \\\\[1ex]\n', text, flags=re.DOTALL)

    # --- STEP 2: HANDLE REMAINING 'ITI' ---
    single_footer_pattern = iti_pat + r'(?!\s*\\)'
    text = re.sub(single_footer_pattern, r'\1 \\\\[1ex]\n', text, flags=re.DOTALL)
    
    # --- STEP 2.5: HANDLE REMAINING 'SAMAPTAH' ---
    single_samaptah_pattern = samaptah_pat + r'(?!\s*\\)'
    text = re.sub(single_samaptah_pattern, r'\1 \\\\[1ex]\n', text, flags=re.DOTALL)

    # --- STEP 3: HANDLE 'ATHA' HEADERS ---
    atha_break_pattern = atha_pat + r'(?!\s*\\\\)'
    text = re.sub(atha_break_pattern, r'\1 \\\\\n', text, flags=re.DOTALL)

    # --- STEP 4: HANDLE MANTRA LINE BREAKS ---
    mantra_break_pattern = mantra_pat + r'(?!\s*\\\\)'
    text = re.sub(mantra_break_pattern, r'\1 \\\\\n', text)
    
    # --- STEP 4.5: FIX MANTRA NUMBER SPACING & PREVENT SPLITTING ---
    # We find || Digits || and wrap them in \mbox{...}
    # \mbox prevents LaTeX from breaking the line inside this block.
    number_spacing_pattern = r'॥\s*([\u0966-\u096F]+)\s*॥'
    text = re.sub(number_spacing_pattern, r'\\mbox{॥ \1 ॥}', text)

   # --- STEP 5: ORPHAN CLEANUP ---
    # Removes lines containing ONLY Dandas/Pipes
    orphan_pattern = r'(?m)^\s*[\|॥\u0964\u0965I]+\s*$'
    text = re.sub(orphan_pattern, '', text)
    
    # Clean up double dandas that might have merged
    text = re.sub(r'॥\s*॥', r'॥', text)
    # Remove excess newlines
    text = re.sub(r'\n\s*\n\s*\n', r'\n\n', text)
    
    return text.lstrip()

# ----------------------------------------------------
# 3. Utility function: Line Breaks (FIXED FOR ORPHANS & ATHA)
# ----------------------------------------------------
def add_enhanced_linebreaks_1(text):
    # --- STEP 0: NORMALIZE ---
    text = text.replace('II.', '॥').replace('II', '॥').replace('||', '॥')
    # Convert single '|' to Devanagari Single Danda (।) PLUS a space.
    text = text.replace('|', r'।\ ').replace('।', r'।\ ')
    text = text.lstrip()
    danda = r'॥'

    # --- DEFINE PATTERNS ---
    
    # 1. ITI PATTERN
    iti_pat = r'(' + danda + r'.*?इति.*?' + danda + r')'
    
    # 2. SAMAPTAH PATTERN
    # Captures "|| ... Samaptah ... ||"
    samaptah_pat = r'((?:' + danda + r')?.*?समाप्तः.*?\s*' + danda + r')'
    
    # 3. ATHA PATTERN (FIXED)
    # The (?:\s*'+danda+r')? looks for an optional Danda BEFORE "Atha".
    # We added \s* inside the group so it captures the Danda even if there is a newline between them.
    atha_pat = r'((?:' + danda + r'\s*)?.*?अथ.*?' + danda + r')'
    
    mantra_pat = r'(' + danda + r'\s*[\d\u0966-\u096F]+\s*' + danda + r')'

    # --- STEP 1: GLUE 'ITI' + 'SAMAPTAH' ---
    double_footer_pattern = iti_pat + r'\s+' + samaptah_pat
    text = re.sub(double_footer_pattern, r'\1 \\\\*[1ex] \2 \\\\[1ex]\n', text, flags=re.DOTALL)

    # --- STEP 2: HANDLE REMAINING 'ITI' ---
    single_footer_pattern = iti_pat + r'(?!\s*\\)'
    text = re.sub(single_footer_pattern, r'\1 \\\\[1ex]\n', text, flags=re.DOTALL)
    
    # --- STEP 2.5: HANDLE REMAINING 'SAMAPTAH' ---
    single_samaptah_pattern = samaptah_pat + r'(?!\s*\\)'
    text = re.sub(single_samaptah_pattern, r'\1 \\\\[1ex]\n', text, flags=re.DOTALL)

    # --- STEP 3: HANDLE 'ATHA' HEADERS ---
    # This logic now pulls the '||' onto the same line as 'Atha'
    atha_break_pattern = atha_pat + r'(?!\s*\\\\)'
    text = re.sub(atha_break_pattern, r'\1 \\\\\n', text, flags=re.DOTALL)

    # --- STEP 4: HANDLE MANTRA LINE BREAKS ---
    mantra_break_pattern = mantra_pat + r'(?!\s*\\\\)'
    text = re.sub(mantra_break_pattern, r'\1 \\\\\n', text)
    
    # --- STEP 4.5: FIX MANTRA NUMBER SPACING ---
    # Ensures || 5 || format
    number_spacing_pattern = r'॥\s*([\u0966-\u096F]+)\s*॥'
    text = re.sub(number_spacing_pattern, r'॥ \1 ॥', text)

   # --- STEP 5: ORPHAN CLEANUP (CRITICAL FIX) ---
    # This specifically targets lines that contain ONLY dandas or whitespace
    # and removes them completely. This fixes the extra lines in your image.
    orphan_pattern = r'(?m)^\s*[\|॥\u0964\u0965I]+\s*$'
    text = re.sub(orphan_pattern, '', text)
    
    # Clean up double dandas that might have merged
    text = re.sub(r'॥\s*॥', r'॥', text)
    # Remove excess newlines
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

   
   
    # --- OLD APPROACH BELOW (FOR REFERENCE) --- 
    
    #mantra_pattern = r'(' + danda + r'\s*[\u0966-\u096F]+\s*' + danda + r')'
    #text = re.sub(mantra_pattern, r'\1 \\\\\n', text)
    #header_pattern = r'(' + danda + r'\s*इति.*?' + danda + r')'
    #text = re.sub(header_pattern, r'\1 \n\\clearpage', text, flags=re.DOTALL)
    # --- STEP 1: Handle the "Iti / End of Section" Footer ---
    # This glues the last mantra to the "Iti" line and forces a page clear.
    # Note: We added flags=re.DOTALL to handle multiline matching
    #section_end_pattern = r'(' + danda + r'\s*[\u0966-\u096F]+\s*' + danda + r')\s*(' + danda + r'\s*इति.*?' + danda + r')'
    #section_end_replacement = r'\1 \\\\*[3ex] \2 \n\\clearpage'
    
    #text = re.sub(section_end_pattern, section_end_replacement, text, flags=re.DOTALL)
    #text = re.sub(pattern, replacement, text)

    # --- STEP 2: Handle Standard Mantra Line Breaks ---
    # This adds a new line (\\) after every other mantra number.
    # Logic:
    # 1. Match the mantra end (|| digits ||) -> Group 1
    # 2. Negative Lookahead (?!\s*\\\\): 
    #    "Only match if NOT followed immediately by a LaTeX break (\\)."
    #    This ensures we don't mess up the lines processed in Step 1.
    
    #general_pattern = r'(' + danda + r'\s*[\u0966-\u096F]+\s*' + danda + r')(?!\s*\\\\)'
    #general_replacement = r'\1 \\\\[\\baselineskip]\n'
    
    #text = re.sub(general_pattern, general_replacement, text)
    
    
        # 1. Handle khanda colophon FIRST (before mantra numbers)
        # Pattern: ॥ इति ... खण्डः ॥
        # This should be on its own line with a page break after
        #khanda_pattern = r'॥\s*इति.*?खण्डः\s*॥'
        #text = re.sub(khanda_pattern, r'\\par\\nopagebreak\\vspace{1em}\\textbf{\g<0>}\\clearpage', text)
    
        
    #return text

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
    # NEW UTILITY: Remove Internal Spaces (Continuous Script)
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
