import sys
from pathlib import Path
import json
import re
import os

def parse_mantra_set(mantra_set_text):
    """
    Parses a block of mantra set text into a list of mantra/swara dictionaries.
    Filters out tags.
    """
    mantra_sets = []
    
    # Split the text by newlines, filtering out empty lines and tag lines.
    mantras = [
        m.strip() 
        for m in mantra_set_text.split('\n') 
        if m.strip() and not m.strip().startswith('<') and not m.strip().startswith('#')
    ]
    
    for mantra in mantras:
        if mantra:
            # The entire line is placed in 'corrected-mantra', including inline swara markings.
            mantra_sets.append({
                "corrected-mantra": mantra,
                "corrected-swara": ""  # Left empty as per user's example
            })
            
    return mantra_sets

def convert_corrections_to_json(file_path="corrections_003.txt"):
    """
    Reads the text file, extracts hierarchical data using regex, and constructs 
    the final JSON object.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found. Please ensure it is in the same directory.")
        return None

    json_output = {"supersection": {}}
    
    # --- 1. Extract ALL Supersections ---
    supersection_pattern = re.compile(
        r'# Start of SuperSection Title -- (supersection_\d+) ## DO NOT EDIT\s*'
        r'(.*?)'
        r'\s*# End of SuperSection Title -- \1 ## DO NOT EDIT\s*'
        r'(.*?)'
        r'(?=# Start of SuperSection Title -- supersection_\d+ ## DO NOT EDIT|$)',
        re.DOTALL
    )
    supersections_data = supersection_pattern.findall(file_content)
    
    if not supersections_data:
        print("Error: No supersection markers were found. Check file structure.")
        return None

    # Process each supersection
    for supersection_id, title_content, supersection_content in supersections_data:
        supersection_id = supersection_id.strip()
        
        # Extract and clean the title
        # Remove XML/HTML-style tags
        title_content = re.sub(r'<[^>]+>', '', title_content, flags=re.DOTALL)
        # Remove pipes (|| or ॥) and trim whitespace for the final title
        supersection_title = re.sub(r'[|॥\s]', '', title_content).strip()
        
        # Initialize the supersection object
        json_output["supersection"][supersection_id] = {
            "supersection_title": supersection_title,
            "sections": {}
        }
        current_supersection_sections = json_output["supersection"][supersection_id]["sections"]

        # --- 2. Extract Sections within this supersection ---
        section_pattern = re.compile(
            r'# Start of Section Title -- (section_\d+) ## DO NOT EDIT\s*'
            r'(.*?)\s*\((.*?)\)\s*'
            r'# End of Section Title -- \1 ## DO NOT EDIT\s*'
            r'(.*?)'
            r'(?=# Start of Section Title -- section_\d+ ## DO NOT EDIT|# Start of SuperSection Title -- supersection_\d+ ## DO NOT EDIT|$)',
            re.DOTALL
        )
        sections_data = section_pattern.findall(supersection_content)
        
        # Calculate section count
        section_count = len(sections_data)
        current_supersection_sections["count"] = {
            "prev_count": 0,
            "current_count": section_count,
            "total_count": section_count
        }
        
        # --- 3. Extract Subsections and Mantra Sets within each section ---
        subsection_pattern = re.compile(
            r'# Start of SubSection Title -- (subsection_\d+) ## DO NOT EDIT\s*'
            r'(.*?)'
            r'\s*# End of SubSection Title -- \1 ## DO NOT EDIT\s*'
            r'#Start of Mantra Sets -- \1 ## DO NOT EDIT\s*'
            r'(.*?)'
            r'\s*#End of Mantra Sets -- \1 ## DO NOT EDIT',
            re.DOTALL
        )

        for section_id, section_title, section_count, section_content in sections_data:
            # Clean the section title
            clean_section_title = section_title.strip()
            
            current_supersection_sections[section_id] = {
                "section_title": clean_section_title,
                "section_count": section_count.strip(),
                "subsections": {}
            }
            
            subsections_data = subsection_pattern.findall(section_content)
            
            for subsection_id, raw_header_text, mantra_set_content in subsections_data:
                # Clean up header text: remove tags, extra whitespace, and trailing markers
                clean_header_text = re.sub(r'<[^>]+>', '', raw_header_text.strip()).strip().rstrip('…|')
                
                current_supersection_sections[section_id]["subsections"][subsection_id] = {
                    "corrected-mantra_sets": parse_mantra_set(mantra_set_content),
                    "header": {
                        "header": clean_header_text
                    },
                    "mantra_sets": []
                }

    return json_output

if __name__ == "__main__":
    # Get the filename from command line argument
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        # Default fallback if no argument provided
        input_file = "corrections_003.txt"
    
    # These lines should be OUTSIDE the if/else block
    input_path = Path(input_file)
    output_file_path = input_path.stem + "_out.json"
    
    output_data = convert_corrections_to_json(input_file)
    
    if output_data:
        try:
            with open(output_file_path, 'w', encoding='utf-8') as outfile:
                json.dump(output_data, outfile, indent=4, ensure_ascii=False)
            print(f"Conversion complete! The structured data is saved to '{output_file_path}'")
        except IOError as e:
            print(f"Error writing to file: {e}")