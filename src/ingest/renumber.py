"""
Unified Renumbering Engine for Jaimineeya Samaveda Pipeline.

Provides 3-pass structural and liturgical tag renumbering, pre-flight tag
balance validation, and versioned metadata block injection.
"""

import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Use centralized core utilities
from src.core.swara_engine import int_to_devanagari, devanagari_to_int


class RenumberEngine:
    """Manages pre-flight validation and multi-pass renumbering of Vedic text files."""

    @staticmethod
    def validate_structural_tags(lines: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates that all structural tags (# Start of / # End of) are balanced.
        Returns:
            (is_valid, error_message)
        """
        stack = []
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("# Start of"):
                tag = stripped[10:].strip()
                stack.append((tag, line_num))
            elif stripped.startswith("# End of"):
                tag = stripped[8:].strip()
                if not stack:
                    return False, f"Line {line_num}: Unexpected '# End of {tag}' with no matching start"
                last_tag, last_line = stack.pop()
                if last_tag != tag:
                    return False, f"Line {line_num}: Mismatched tag. Expected '# End of {last_tag}' (started line {last_line}), found '# End of {tag}'"
        
        if stack:
            unclosed = ", ".join(f"'{tag}' (line {line})" for tag, line in stack)
            return False, f"Unclosed structural tags: {unclosed}"
        return True, None

    @staticmethod
    def renumber_file(
        input_file: Path,
        output_file: Optional[Path] = None,
        preserve_super: bool = False,
        reset_per_super: bool = False,
        reset_samam_per_section: bool = False,
        start_sup: int = 1,
        start_sec: int = 1,
        start_sub: int = 1,
        preserve_all: bool = False,
        no_renumber: bool = False,
        backup: bool = True
    ) -> bool:
        """
        Executes unified 3-pass renumbering on the target text file.
        Delegates to tools/renumber_sooktam for complete backward compatibility.
        """
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        from renumber_sooktam import renumber_text_file

        return renumber_text_file(
            input_file=input_file,
            output_file=output_file,
            preserve_super=preserve_super,
            reset_per_super=reset_per_super,
            reset_samam_per_section=reset_samam_per_section,
            start_sup=start_sup,
            start_sec=start_sec,
            start_sub=start_sub,
            preserve_all=preserve_all,
            no_renumber=no_renumber,
            backup=backup
        )
