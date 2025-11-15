import subprocess
import os
import re
import chardet
# ----------------------------------------------------
# 1. Utility function: Accent Replacements
# ----------------------------------------------------
def replace_accents(text):
    """Replaces ASCII markers (1), (2), etc., with LaTeX commands 
    containing the corresponding Unicode accent characters."""
    replacements = [
        ('(1)', r'\accentmark{22}{\char"0951}'),  # Swarita - U+0951 (was 20, now 22)
        ('(2)', r'\accentmark{27}{\char"1CD2}'),  # Anudatta - U+1CD2 (was 24, now 27)
        ('(3)', r'\accentmark{20}{\char"1CF8}'),  # Kampa - U+1CF8 (was 20, now 22)
        ('(4)', r'\accentmark{20}{\char"1CF9}'),  # Trikampa - U+1CF9 (was 20, now 22)
    ]
    
    for marker, replacement in replacements:
        text = text.replace(marker, replacement)
    
    return text

# ----------------------------------------------------
# 2. Utility function: Format Header
# ----------------------------------------------------
def format_header(text):
    """Format the header text (first 4 lines) as bold and centered."""
    # Split the text into lines
    lines = text.split('\n')
    
    # Check if we have at least 3 lines for the header
    if len(lines) >= 4:
        # Take first 4 lines as header
        header_line1 = lines[0].strip()
        header_line2 = lines[1].strip()
        header_line3 = lines[2].strip()
        header_line4 = lines[3].strip()
        
        # Create centered, bold header with spacing after
       
        formatted_header = (
            r'\begin{center}' + '\n' +
            r'\Huge\textbf{' + header_line1 + r'}\\' + '\n' +
            r'\Large\textbf{' + header_line2 + r'}\\' + '\n' +
            r'\Large\textbf{' + header_line3 + r'}\\' + '\n' +
            r'\Large\textbf{' + header_line4 + r'}\\' + '\n' +
            r'\end{center}' + '\n' +
            r'\vspace{2\baselineskip}' + '\n\n'  # 2 line spacing
        )
        
        # Join the remaining lines
        remaining_text = '\n'.join(lines[4:])
        
        return formatted_header + remaining_text
    else:
        # If less than 4 lines, return original text
        return text

# ----------------------------------------------------
# 3. Utility function: Line Breaks
# ----------------------------------------------------
def add_enhanced_linebreaks(text):
    """Inserts paragraph breaks after mantra numbers and Khanda colophons."""
    
    # 1. Handle khanda colophon FIRST (before mantra numbers)
    # Pattern: ॥ इति ... खण्डः ॥
    # This should be on its own line with a page break after
    khanda_pattern = r'॥\s*इति.*?खण्डः\s*॥'
    # Add line break before, the text, then page break after
    text = re.sub(khanda_pattern, r'\\par\g<0>\\par\\newpage', text)
    
    # 2. Triple spacing after Mantra Number (e.g., ॥ १ ॥)
    # Pattern matches: ॥ followed by Devanagari digits, then ॥
    mantra_pattern = r'(॥\s*[\u0966-\u096F][\u0966-\u096F\s]*॥)'
    text = re.sub(mantra_pattern, r'\1\\par\\vspace{1em}\\par', text)
    
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
def reduce_trailing_whitespace_final(text):
    # 1. Targets " ॥" -> "\,॥"
    text = re.sub(r'\s(॥)', r'\\,\1', text) 

    # 2. Targets " ॥ १ ॥" -> "\,॥ १ ॥"
    mantra_number_pattern = r'(\s)(॥\s*[\u0966-\u096F][\u0966-\u096F\s]*॥)'
    text = re.sub(mantra_number_pattern, r'\\,\2', text)
    
    return text

def eliminate_trailing_whitespace(text):
    #"""
    #Replaces standard spaces before line-ending Danda (॥) or mantra numbers 
    #with a zero-width space (\hspace{0pt}) to force a line break in LaTeX.
    #"""
    
    # LaTeX command for zero-width space
    zero_space = r'\\hspace{0pt}' 
    
    # 1. Targets " ॥" -> "\hspace{0pt}॥"
    text = re.sub(r'\s(॥)', zero_space + r'\1', text)

    # 2. Targets " ॥ १ ॥" -> "\hspace{0pt}॥ १ ॥"
    mantra_number_pattern = r'(\s)(॥\s*[\u0966-\u096F][\u0966-\u096F\s]*॥)'
    text = re.sub(mantra_number_pattern, zero_space + r'\2', text)
    
    return text  
# ----------------------------------------------------
# 5. Main processing function
# ----------------------------------------------------
def generate_and_compile_latex(input_text, base_filename='vedic_output'):
    """
    Generate LaTeX file with processed text and compile it using LuaLaTeX.
    """
    tex_filename = f'{base_filename}.tex'
    #-- FIX: Corrected processing pipeline ---
    # 1. Format header FIRST
    processed_text = format_header(input_text)
    # 2. Replace accents
    processed_text = replace_accents(processed_text)
    # 3. Add line breaks for mantras and khandas
    processed_text = add_enhanced_linebreaks(processed_text)
    # 4. Handle trailing whitespace LAST
    processed_text = eliminate_trailing_whitespace(processed_text)
    # --- End of pipeline fix ---

    # Get the absolute path to the font directory
    font_path = r'C:/Users/sekha/OneDrive/Documents/GitHub/jaimineeyasamavedam/Rik_Processing/AdishilaVedic/'
    
    # Create LaTeX document
    latex_content = r'''\documentclass[12pt,a4paper]{article}
\usepackage{fontspec}
\usepackage[margin=1in]{geometry}
\usepackage{setspace}
\singelespacing

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
% --- ADD THESE LINES FOR AGGRESSIVE LINE BREAKING ---
\setlength{\emergencystretch}{1em}
\tolerance=10000 % Allow high tolerance for stretching/shrinking lines
\pretolerance=10000 % Allow high pretolerance
\emergencystretch=1in % Allow emergency stretching to fit text

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
        print("Error: LuaLaTeX not found. Please install TeX Live or MiKTeX.")
        print(f"You can manually compile with: lualatex {tex_filename}")
    except subprocess.CalledProcessError as e:
        print("Error during compilation:")
        log_filename = f'{base_filename}_error.log'
        with open(log_filename, 'w', encoding='utf-8') as log:
            if e.stdout:
                log.write(e.stdout)
            log.write("\n\n--- STDERR ---\n\n")
            if e.stderr:
                log.write(e.stderr)
            if e.stdout:
                print('\n'.join(e.stdout.splitlines()[-15:]))
            print("\nLast 15 lines of error (STDERR):")
            if e.stderr:
                print('\n'.join(e.stderr.splitlines()[-15:]))
             
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# ----------------------------------------------------
# Example usage
# ----------------------------------------------------
if __name__ == "__main__":
    # The input file path
    input_file = r'C:\Users\sekha\OneDrive\Documents\GitHub\jaimineeyasamavedam\Rik_Processing\vedic_text.txt'
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
        print("Please ensure the file path is correct.")
    else:
        try:
            with open(input_file, 'r', encoding='UTF-8') as f:
               # f.seek(1880)
              #  snippet = f.read(40)
              #  print(snippet) 
                text = f.read()                      
            
            # Generate and compile
            generate_and_compile_latex(text, 'vedic_output')
        except UnicodeDecodeError:
            print(f"Error: Could not read '{input_file}' with UTF-8 encoding. Check file encoding.")
        except Exception as e:
            print(f"An error occurred while reading the input file: {e}")
