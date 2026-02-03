import re

filename = r'data\input\Samhita_with_Rishi_Devata_Chandas.txt'
SAMAM_PATTERN = re.compile(r'(?:॥|\|\|)\s*([\d०-९]+)\s*(?:॥|\|\|)')

def get_arabic(num_str):
    dev_map = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
               '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}
    arabic = ''.join(dev_map.get(c, c) for c in num_str)
    return int(arabic)

def debug_file():
    current_patha = ""
    current_khanda = ""
    in_block = False
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        if line.startswith("# Start of SuperSection Title"):
             current_patha = lines[i+1].strip()
        if line.startswith("# Start of Section Title"):
             current_khanda = lines[i+1].strip()
             
        if line.startswith("#Start of Mantra Sets"):
            in_block = True
            
        if line.startswith("#End of Mantra Sets"):
            in_block = False
            
        if in_block and current_patha == "बृहतिपाठः" and current_khanda == "चतुर्थ खण्डः":
            matches = SAMAM_PATTERN.findall(line)
            for m in matches:
                print(f"Line {i+1}: Found '{m}' -> {get_arabic(m)}")

if __name__ == "__main__":
    debug_file()
