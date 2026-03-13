import re

def devanagari_to_int(text):
    mapping = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}
    for d_char, num in mapping.items():
        text = text.replace(d_char, num)
    try:
        return int(text)
    except ValueError:
        return None

def main():
    try:
        with open('data/output/JSV_Rik_Table - for analysis.txt', 'r', encoding='utf-16le') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading utf-16le: {e}")
        try:
             with open('data/output/JSV_Rik_Table - for analysis.txt', 'r', encoding='utf-8') as f:
                 lines = f.readlines()
        except:
             print("Error reading utf-8 too")
             return

    if not lines:
        return
        
    delimiter = '\t'
    
    # Add a new column header for the note
    header_parts = lines[0].rstrip('\n').rstrip('\r').split(delimiter)
    header_parts.append("Discontinuity_Note")
    out_lines = [delimiter.join(header_parts) + "\n"]
    
    last_num = None
    last_line = None
    
    for i, line in enumerate(lines[1:]):
        parts = line.rstrip('\n').rstrip('\r').split(delimiter)
        if len(parts) > 6:
            col_g = parts[6].strip()
            # The number is at the end: ॥२७१ or ॥२७१॥
            # Let's extract all consecutive Devanagari numerals at the end
            match = re.search(r'([०-९]+)[^०-९]*$', col_g)
            if match:
                num_str = match.group(1)
                num = devanagari_to_int(num_str)
                
                if num is not None:
                    if last_num is not None:
                        if num != last_num + 1:
                            # Prepend the previous row
                            prev_parts = last_line.rstrip('\n').rstrip('\r').split(delimiter)
                            prev_parts.append(f"Jump to {num}")
                            out_lines.append(delimiter.join(prev_parts) + "\n")
                            
                            # Append the current row
                            parts.append(f"Jumped from {last_num}")
                            out_lines.append(delimiter.join(parts) + "\n")
                            
                            # Add an empty row for visual separation in Excel (optional, but good for grouping)
                            out_lines.append("\n")
                    last_num = num
                    last_line = line

    # Dump output as a .txt file encoding utf-16le for Excel
    with open('data/output/non_contiguous_analysis_v2.txt', 'w', encoding='utf-16le') as f:
        for line in out_lines:
            f.write(line)
            
    print(f"Found non-contiguous jumps. Saved to data/output/non_contiguous_analysis_v2.txt")

if __name__ == '__main__':
    main()
