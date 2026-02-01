#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
add_text_delimiters.py

Utility to introduce text delimiters (markers/comments) around structural elements
in Jaimineeyasamaveda text files for further processing.

Delimiter formats:
- SuperSection: # Start/End of SuperSection Title -- supersection_N ## DO NOT EDIT
- Section: # Start/End of Section Title -- section_N ## DO NOT EDIT  
- SubSection: # Start/End of SubSection Title -- subsection_N ## DO NOT EDIT
- Mantra Sets: #Start/End of Mantra Sets -- subsection_N ## DO NOT EDIT
"""

import re
import os
import sys
from pathlib import Path


class TextDelimiterProcessor:
    """
    Processor to add structural delimiters to Jaimineeyasamaveda text files.
    """
    
    def __init__(self):
        # Counters for generating unique IDs
        self.supersection_counter = 0
        self.section_counter = 0
        self.subsection_counter = 0
        
        # Current context for associating mantra sets with subsections
        self.current_subsection_id = None
        
        # Patterns for identifying structural elements
        # SuperSection: ॥ व्रत पर्व ॥ (double dandas with spaces around title)
        self.supersection_pattern = re.compile(r'^॥\s+(.+?)\s+॥\s*$')
        
        # Section patterns:
        # - खण्डः patterns like "प्रथम खण्डः (191)" or "॥ अथ द्वितीय खण्डः ॥"
        self.section_pattern = re.compile(r'^(?:॥\s*)?(?:अथ\s+)?(.+?खण्डः?(?:\s*\(\d+\))?)\s*(?:॥\s*)?$')
        
        # SubSection: ||title|| or ।। title ।। (double pipes or double dandas)
        self.subsection_pattern = re.compile(r'^(?:\|\||\।\।)\s*(.+?)\s*(?:\|\||\।\।)\s*$')
        
        # Check if line already has delimiters
        self.has_start_delimiter = re.compile(r'^#\s*Start of')
        self.has_end_delimiter = re.compile(r'^#\s*End of')
        self.has_mantra_start = re.compile(r'^#\s*Start of Mantra Sets')
        self.has_mantra_end = re.compile(r'^#\s*End of Mantra Sets')
    
    def is_blank_or_whitespace(self, line):
        """Check if a line is blank or contains only whitespace."""
        return not line.strip()
    
    def is_mantra_line(self, line):
        """
        Check if a line appears to be a mantra line.
        Mantra lines typically:
        - Contain Sanskrit text
        - Often end with ॥ N ॥ pattern (mantra number)
        - Are not structural markers (supersection, section, subsection)
        """
        stripped = line.strip()
        if not stripped:
            return False
        
        # Skip if it's a delimiter line
        if stripped.startswith('#'):
            return False
        
        # Skip if it matches structural patterns
        if self.supersection_pattern.match(stripped):
            return False
        if self.section_pattern.match(stripped):
            return False
        if self.subsection_pattern.match(stripped):
            return False
        
        # Check for mantra content - contains Devanagari and potentially ends with mantra number
        if re.search(r'[\u0900-\u097F]', stripped):  # Contains Devanagari
            return True
        
        return False
    
    def identify_line_type(self, line):
        """
        Identify the type of a given line.
        Returns: tuple (type, title) where type is one of:
        - 'supersection', 'section', 'subsection', 'mantra', 'blank', 'delimiter', 'other'
        """
        stripped = line.strip()
        
        if not stripped:
            return ('blank', None)
        
        if stripped.startswith('#'):
            return ('delimiter', None)
        
        # Check for section (खण्डः patterns) FIRST - this takes priority
        # Lines containing खण्डः are sections, even if wrapped in ॥ ... ॥
        match = self.section_pattern.match(stripped)
        if match:
            return ('section', match.group(1).strip())
        
        # Check for supersection (॥ title ॥ with spaces) - only if NOT a section
        match = self.supersection_pattern.match(stripped)
        if match:
            return ('supersection', match.group(1).strip())
        
        # Check for subsection (||title|| or ।।title।।)
        match = self.subsection_pattern.match(stripped)
        if match:
            return ('subsection', match.group(1).strip())
        
        # Check for mantra line
        if self.is_mantra_line(line):
            return ('mantra', None)
        
        return ('other', None)
    
    def strip_existing_delimiters(self, lines):
        """
        Remove all existing delimiter lines from the content.
        
        Args:
            lines: List of lines from the file
        
        Returns:
            List of lines with delimiter comments removed
        """
        cleaned_lines = []
        delimiter_patterns = [
            r'^#\s*Start of SuperSection Title',
            r'^#\s*End of SuperSection Title',
            r'^#\s*Start of Section Title',
            r'^#\s*End of Section Title',
            r'^#\s*Start of SubSection Title',
            r'^#\s*End of SubSection Title',
            r'^#\s*Start of Mantra Sets',
            r'^#\s*End of Mantra Sets',
        ]
        combined_pattern = re.compile('|'.join(delimiter_patterns))
        
        for line in lines:
            stripped = line.strip()
            if not combined_pattern.match(stripped):
                cleaned_lines.append(line)
        
        return cleaned_lines
    
    def process_file(self, input_path, output_path=None, 
                     start_supersection=1, start_section=1, start_subsection=1,
                     strip_existing=True, skip_header_lines=5):
        """
        Process a file and add delimiters around structural elements.
        
        Args:
            input_path: Path to input file
            output_path: Path to output file (if None, overwrites input)
            start_supersection: Starting counter for supersection IDs
            start_section: Starting counter for section IDs
            start_subsection: Starting counter for subsection IDs
            strip_existing: If True, remove existing delimiters before processing
            skip_header_lines: Number of lines at start to preserve as-is (header)
        
        Returns:
            Dictionary with processing statistics
        """
        self.supersection_counter = start_supersection - 1
        self.section_counter = start_section - 1
        self.subsection_counter = start_subsection - 1
        self.skip_header_lines = skip_header_lines
        
        if output_path is None:
            output_path = input_path
        
        # Read input file
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Strip existing delimiters if requested
        if strip_existing:
            lines = self.strip_existing_delimiters(lines)
        
        processed_lines = []
        stats = {
            'supersections': 0,
            'sections': 0,
            'subsections': 0,
            'mantra_sets': 0,
            'lines_processed': len(lines)
        }
        
        i = 0
        pending_mantras = []  # Buffer to collect consecutive mantra lines
        
        # Preserve header lines as-is
        while i < len(lines) and i < skip_header_lines:
            processed_lines.append(lines[i])
            i += 1
        
        while i < len(lines):
            line = lines[i]
            line_type, title = self.identify_line_type(line)
            
            # If we have pending mantras and encounter a non-mantra line,
            # we need to wrap up the mantra set
            if pending_mantras and line_type != 'mantra':
                if self.current_subsection_id:
                    # Add mantra set end delimiter
                    processed_lines.append(f"#End of Mantra Sets -- {self.current_subsection_id} ## DO NOT EDIT\n")
                    stats['mantra_sets'] += 1
                pending_mantras = []
            
            if line_type == 'blank':
                processed_lines.append(line)
            
            elif line_type == 'delimiter':
                # Already has delimiter, keep as-is
                processed_lines.append(line)
            
            elif line_type == 'supersection':
                self.supersection_counter += 1
                supersection_id = f"supersection_{self.supersection_counter}"
                
                processed_lines.append(f"# Start of SuperSection Title -- {supersection_id} ## DO NOT EDIT\n")
                processed_lines.append(line)
                processed_lines.append(f"# End of SuperSection Title -- {supersection_id} ## DO NOT EDIT\n")
                
                stats['supersections'] += 1
            
            elif line_type == 'section':
                self.section_counter += 1
                section_id = f"section_{self.section_counter}"
                
                processed_lines.append(f"# Start of Section Title -- {section_id} ## DO NOT EDIT\n")
                processed_lines.append(line)
                processed_lines.append(f"# End of Section Title -- {section_id} ## DO NOT EDIT\n")
                
                stats['sections'] += 1
            
            elif line_type == 'subsection':
                self.subsection_counter += 1
                subsection_id = f"subsection_{self.subsection_counter}"
                self.current_subsection_id = subsection_id
                
                processed_lines.append(f"# Start of SubSection Title -- {subsection_id} ## DO NOT EDIT\n")
                processed_lines.append(line)
                processed_lines.append(f"# End of SubSection Title -- {subsection_id} ## DO NOT EDIT\n")
                
                stats['subsections'] += 1
            
            elif line_type == 'mantra':
                # First mantra in a set - add start delimiter
                if not pending_mantras and self.current_subsection_id:
                    processed_lines.append(f"#Start of Mantra Sets -- {self.current_subsection_id} ## DO NOT EDIT\n")
                
                pending_mantras.append(line)
                processed_lines.append(line)
            
            else:
                # Other content
                processed_lines.append(line)
            
            i += 1
        
        # Handle any remaining pending mantras at end of file
        if pending_mantras and self.current_subsection_id:
            processed_lines.append(f"#End of Mantra Sets -- {self.current_subsection_id} ## DO NOT EDIT\n")
            stats['mantra_sets'] += 1
        
        # Write output file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(processed_lines)
        
        return stats
    
    def preview_changes(self, input_path, num_lines=50):
        """
        Preview what the processed output would look like without writing.
        
        Args:
            input_path: Path to input file
            num_lines: Number of lines to preview
        
        Returns:
            String with preview of processed output
        """
        # Reset counters
        self.supersection_counter = 0
        self.section_counter = 0
        self.subsection_counter = 0
        
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        processed_lines = []
        pending_mantras = []
        
        for i, line in enumerate(lines[:num_lines]):
            line_type, title = self.identify_line_type(line)
            
            if pending_mantras and line_type != 'mantra':
                if self.current_subsection_id:
                    processed_lines.append(f"#End of Mantra Sets -- {self.current_subsection_id} ## DO NOT EDIT\n")
                pending_mantras = []
            
            if line_type == 'supersection':
                self.supersection_counter += 1
                supersection_id = f"supersection_{self.supersection_counter}"
                processed_lines.append(f"# Start of SuperSection Title -- {supersection_id} ## DO NOT EDIT\n")
                processed_lines.append(line)
                processed_lines.append(f"# End of SuperSection Title -- {supersection_id} ## DO NOT EDIT\n")
            
            elif line_type == 'section':
                self.section_counter += 1
                section_id = f"section_{self.section_counter}"
                processed_lines.append(f"# Start of Section Title -- {section_id} ## DO NOT EDIT\n")
                processed_lines.append(line)
                processed_lines.append(f"# End of Section Title -- {section_id} ## DO NOT EDIT\n")
            
            elif line_type == 'subsection':
                self.subsection_counter += 1
                subsection_id = f"subsection_{self.subsection_counter}"
                self.current_subsection_id = subsection_id
                processed_lines.append(f"# Start of SubSection Title -- {subsection_id} ## DO NOT EDIT\n")
                processed_lines.append(line)
                processed_lines.append(f"# End of SubSection Title -- {subsection_id} ## DO NOT EDIT\n")
            
            elif line_type == 'mantra':
                if not pending_mantras and self.current_subsection_id:
                    processed_lines.append(f"#Start of Mantra Sets -- {self.current_subsection_id} ## DO NOT EDIT\n")
                pending_mantras.append(line)
                processed_lines.append(line)
            
            else:
                processed_lines.append(line)
        
        if pending_mantras and self.current_subsection_id:
            processed_lines.append(f"#End of Mantra Sets -- {self.current_subsection_id} ## DO NOT EDIT\n")
        
        return ''.join(processed_lines)


def add_delimiters_to_file(input_file, output_file=None,
                           start_supersection=1, start_section=1, start_subsection=1):
    """
    Main utility function to add text delimiters to a file.
    
    Args:
        input_file: Path to input file
        output_file: Path to output file (if None, creates backup and overwrites input)
        start_supersection: Starting counter for supersection IDs
        start_section: Starting counter for section IDs  
        start_subsection: Starting counter for subsection IDs
    
    Returns:
        Dictionary with processing statistics
    """
    processor = TextDelimiterProcessor()
    
    # Create backup if overwriting
    if output_file is None:
        backup_path = str(input_file) + '.backup'
        import shutil
        shutil.copy2(input_file, backup_path)
        print(f"Created backup at: {backup_path}")
    
    stats = processor.process_file(
        input_file, 
        output_file,
        start_supersection=start_supersection,
        start_section=start_section,
        start_subsection=start_subsection
    )
    
    return stats


def preview_delimiters(input_file, num_lines=100):
    """
    Preview the delimiter additions without modifying the file.
    
    Args:
        input_file: Path to input file
        num_lines: Number of lines to preview
    
    Returns:
        String with preview output
    """
    processor = TextDelimiterProcessor()
    return processor.preview_changes(input_file, num_lines)


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) < 2:
        print("Usage: python add_text_delimiters.py <input_file> [output_file]")
        print("\nThis utility adds structural delimiters to Jaimineeyasamaveda text files.")
        print("\nDelimiter types:")
        print("  - SuperSection: # Start/End of SuperSection Title -- supersection_N")
        print("  - Section: # Start/End of Section Title -- section_N")
        print("  - SubSection: # Start/End of SubSection Title -- subsection_N")
        print("  - Mantra Sets: #Start/End of Mantra Sets -- subsection_N")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # First preview
    print("=" * 60)
    print("PREVIEW (first 50 lines):")
    print("=" * 60)
    preview = preview_delimiters(input_file, 50)
    print(preview)
    print("=" * 60)
    
    # Ask for confirmation if not providing output file
    if output_file is None:
        response = input("\nThis will modify the file in-place (backup will be created). Continue? [y/N]: ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
    
    stats = add_delimiters_to_file(input_file, output_file)
    
    print("\nProcessing complete!")
    print(f"  Lines processed: {stats['lines_processed']}")
    print(f"  Supersections found: {stats['supersections']}")
    print(f"  Sections found: {stats['sections']}")
    print(f"  Subsections found: {stats['subsections']}")
    print(f"  Mantra sets wrapped: {stats['mantra_sets']}")
