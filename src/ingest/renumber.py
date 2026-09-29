"""
Unified Ingestion & Renumbering Tool for Jaimineeya Samaveda Pipeline.
----------------------------------------------------------------------
Canonical Location: src/ingest/renumber.py

Consolidates all structural tag renumbering, pre-flight tag balance validation,
multi-directional block alignment, verse danda renumbering (Devanagari numerals),
and 3-tier versioned metadata block injection into a single unified module and CLI.

Consolidates and supersedes legacy tools:
  - src/tools/renumber_sections.py
  - src/tools/renumber_sooktam.py
"""

import sys
import os
import re
import argparse
import shutil
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Union
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = REPO_ROOT / "src" / "pipeline_config.yaml"
VERSION_FILE = REPO_ROOT / "src" / "VERSION"

# Ensure src/ is on sys.path for core module access
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

try:
    from core.swara_engine import int_to_devanagari, devanagari_to_int
    from core.version import (
        get_corpus_edition,
        get_build_metadata,
        increment_corpus_edition,
        set_corpus_edition
    )
except ImportError:
    try:
        from src.core.swara_engine import int_to_devanagari, devanagari_to_int
        from src.core.version import (
            get_corpus_edition,
            get_build_metadata,
            increment_corpus_edition,
            set_corpus_edition
        )
    except ImportError:
        # Fallback numeral converters if core module unavailable
        DEVA_TO_ARABIC = str.maketrans('०१२३४५६७८९', '0123456789')
        ARABIC_TO_DEVA = str.maketrans('0123456789', '०१२३४५६७८९')
        def int_to_devanagari(n: int) -> str:
            return str(n).translate(ARABIC_TO_DEVA)
        def devanagari_to_int(s: str) -> int:
            digits = re.sub(r'[^\d०-९]', '', str(s))
            return int(digits.translate(DEVA_TO_ARABIC)) if digits else 0
        def get_corpus_edition(corpus: str = "samhita") -> str:
            if VERSION_FILE.exists():
                return VERSION_FILE.read_text(encoding='utf-8').strip()
            return "3.28"
        def increment_corpus_edition(corpus: str = "samhita") -> str:
            v = get_corpus_edition(corpus)
            parts = v.split('.')
            if len(parts) >= 2:
                parts[-1] = str(int(parts[-1]) + 1)
                return ".".join(parts)
            return v
        def get_build_metadata(corpus: str = "samhita", input_file=None, increment=False):
            from datetime import datetime
            return {
                "version": get_corpus_edition(corpus),
                "generated_at": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            }

DEVANAGARI_DIGIT_CLASS = r'[०-९]'
TAG_TYPES = [
    "SuperSection Title",
    "Section Title",
    "SubSection Title",
    "Rik Metadata",
    "Rik Text",
    "Mantra Sets",
    "Footnote"
]

START_TAG_PATTERN = re.compile(r'#\s*Start of (.*?)(?:\s*--\s*(.*?))?(?:\s*##.*)?$', re.IGNORECASE)
END_TAG_PATTERN = re.compile(r'#\s*End of (.*?)(?:\s*--\s*(.*?))?(?:\s*##.*)?$', re.IGNORECASE)
METADATA_BLOCK_PATTERN = re.compile(r'#\s*\[JSV METADATA\].*?#\s*\[END METADATA\]\s*', re.DOTALL)


def load_pipeline_config() -> dict:
    """Loads master pipeline configuration from pipeline_config.yaml."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {}


def validate_structural_tags(lines: List[str]) -> Tuple[bool, List[str]]:
    """
    Validates that all structural tags (# Start of / # End of) are balanced and well-formed.
    
    Checks:
      - SuperSection Title, Section Title, SubSection Title
      - Rik Metadata, Rik Text, Mantra Sets, Footnote
    
    Returns:
        (is_valid, errors) where errors is a list of descriptive error strings.
    """
    stack = []
    errors = []

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue

        start_m = START_TAG_PATTERN.search(stripped)
        if start_m:
            tag_name = start_m.group(1).strip()
            tag_id = (start_m.group(2) or "").strip()
            if tag_name in TAG_TYPES or any(t.lower() == tag_name.lower() for t in TAG_TYPES):
                stack.append({"name": tag_name, "id": tag_id, "line": line_num})
            continue

        end_m = END_TAG_PATTERN.search(stripped)
        if end_m:
            tag_name = end_m.group(1).strip()
            tag_id = (end_m.group(2) or "").strip()
            if tag_name in TAG_TYPES or any(t.lower() == tag_name.lower() for t in TAG_TYPES):
                if not stack:
                    errors.append(f"Line {line_num}: Found '# End of {tag_name}' (id: '{tag_id}') with no open start tag.")
                else:
                    last = stack.pop()
                    if last["name"].lower() != tag_name.lower():
                        errors.append(
                            f"Line {line_num}: Tag mismatch! Expected '# End of {last['name']}' "
                            f"(opened at line {last['line']}), but found '# End of {tag_name}'."
                        )

    while stack:
        last = stack.pop()
        errors.append(f"Line {last['line']}: Unclosed block! '# Start of {last['name']}' (id: '{last['id']}') was never closed.")

    return len(errors) == 0, errors


def inject_metadata_to_text(content: str, version: str, timestamp: str) -> str:
    """Injects or updates the # [JSV METADATA] block at the top of a text file."""
    new_meta = (
        f"# [JSV METADATA]\n"
        f"# Version: {version}\n"
        f"# Generated At: {timestamp}\n"
        f"# [END METADATA]\n\n"
    )
    if METADATA_BLOCK_PATTERN.search(content):
        return METADATA_BLOCK_PATTERN.sub(new_meta, content, count=1)
    else:
        return new_meta + content.lstrip()


def renumber_text(
    lines: List[str],
    preserve_super: bool = False,
    reset_per_super: bool = False,
    reset_samam_per_section: bool = True,
    reset_samam_per_super: bool = True,
    start_sup: int = 1,
    start_sec: int = 1,
    start_sub: int = 1,
    preserve_all: bool = False,
    no_renumber: bool = False
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Executes the canonical 3-pass renumbering algorithm on a list of text lines.
    
    Pass 1: Global Sequence Identifiers (supersection_N, section_N, subsection_N)
    Pass 2: Multi-directional Block Alignment (Mantra Sets, Rik Text, Rik Metadata)
    Pass 3: Verse Delimiter & Samam/Rik Counter Renumbering (Devanagari numerals)
    
    Returns:
        (transformed_lines, stats_dict)
    """
    stats = {
        "supersections": 0,
        "sections": 0,
        "subsections": 0,
        "samams": 0,
        "riks": 0
    }

    if no_renumber:
        return lines, stats

    # ─── Pass 1: Global Sequence Identifiers (section_N, subsection_N) ───
    current_sup = start_sup - 1
    current_sec = start_sec - 1
    current_sub = start_sub - 1
    total_sups = 0
    total_secs = 0
    total_subs = 0
    
    pass1_lines = []
    for line in lines:
        if re.search(r'#\s*Start of SuperSection Title', line, re.IGNORECASE):
            total_sups += 1
            current_sup += 1
            if reset_per_super:
                current_sec = 0  # Will be incremented to 1 at next Section
                current_sub = 0
            if not preserve_super:
                line = re.sub(r'supersection_\d+', f'supersection_{current_sup}', line)
        elif re.search(r'#\s*End of SuperSection Title', line, re.IGNORECASE):
            if not preserve_super:
                line = re.sub(r'supersection_\d+', f'supersection_{current_sup}', line)
        
        elif re.search(r'#\s*Start of Section Title', line, re.IGNORECASE):
            total_secs += 1
            current_sec += 1
            if not preserve_all:
                line = re.sub(r'section_\d+', f'section_{max(1, current_sec)}', line)
        elif re.search(r'#\s*End of Section Title', line, re.IGNORECASE):
            if not preserve_all:
                line = re.sub(r'section_\d+', f'section_{max(1, current_sec)}', line)
        
        elif re.search(r'#\s*Start of SubSection Title', line, re.IGNORECASE):
            total_subs += 1
            current_sub += 1
            if not preserve_all:
                line = re.sub(r'subsection_\d+', f'subsection_{max(1, current_sub)}', line)
        elif re.search(r'#\s*End of SubSection Title', line, re.IGNORECASE):
            if not preserve_all:
                line = re.sub(r'subsection_\d+', f'subsection_{max(1, current_sub)}', line)

        pass1_lines.append(line)

    stats["supersections"] = total_sups
    stats["sections"] = total_secs
    stats["subsections"] = total_subs

    # ─── Pass 2: Align Rik / Metadata / Mantra blocks ───
    pass2_lines = []
    subsection_pattern = r'#\s*Start of SubSection Title\s*--\s*subsection_(\d+)'

    for i, line in enumerate(pass1_lines):
        if re.search(r'#\s*(Start|End) of (Mantra Sets)', line, re.IGNORECASE):
            prev_sub_num = None
            for j in range(i - 1, -1, -1):
                m = re.search(subsection_pattern, pass1_lines[j], re.IGNORECASE)
                if m:
                    prev_sub_num = m.group(1)
                    break
            if prev_sub_num is not None:
                line = re.sub(r'subsection_\d+', f'subsection_{prev_sub_num}', line)

        elif re.search(r'#\s*(Start|End) of (Rik Text|Rik Metadata)', line, re.IGNORECASE):
            next_sub_num = None
            for j in range(i + 1, len(pass1_lines)):
                m = re.search(subsection_pattern, pass1_lines[j], re.IGNORECASE)
                if m:
                    next_sub_num = m.group(1)
                    break
            if next_sub_num is not None:
                line = re.sub(r'subsection_\d+', f'subsection_{next_sub_num}', line)

        pass2_lines.append(line)

    # ─── Pass 3: Renumber Samam and Rik verse counters ───
    final_lines = []
    in_mantra_set = False
    in_rik_text = False
    in_subsection_title = False

    samam_counter = 1
    rik_counter = 1
    global_samam_total = 0
    global_rik_total = 0

    verse_marker = r'(?:॥|\|\||।।।|┃|।)'
    verse_pattern = rf'({verse_marker})\s*{DEVANAGARI_DIGIT_CLASS}+\s*({verse_marker})'

    for line in pass2_lines:
        # Handle block resets
        if re.search(r'#\s*Start of SuperSection Title', line, re.IGNORECASE):
            if reset_samam_per_section or reset_samam_per_super:
                samam_counter = 1
                rik_counter = 1
        elif re.search(r'#\s*Start of Section Title', line, re.IGNORECASE):
            if reset_samam_per_section:
                samam_counter = 1
                rik_counter = 1

        # Determine Mode (Mantra vs Rik)
        if re.search(r'#\s*Start of Mantra Sets', line, re.IGNORECASE):
            in_mantra_set = True
        elif re.search(r'#\s*End of Mantra Sets', line, re.IGNORECASE):
            pass 
        elif re.search(r'#\s*Start of Rik Text', line, re.IGNORECASE):
            in_rik_text = True
        elif re.search(r'#\s*End of Rik Text', line, re.IGNORECASE):
            pass

        # Handle Titling danda cleanup
        if re.search(r'#\s*Start of SubSection Title', line, re.IGNORECASE):
            in_subsection_title = True
        elif re.search(r'#\s*End of SubSection Title', line, re.IGNORECASE):
            in_subsection_title = False
        
        if in_subsection_title and line.strip() and not line.strip().startswith('#'):
            text = line.strip()
            if (text.startswith('॥') or text.startswith('┃')) and (text.endswith('॥') or text.endswith('┃') or text.endswith(')')):
                prefix = line[:line.find('॥')] if '॥' in line else line[:line.find('┃')]
                clean_text = re.sub(rf'{DEVANAGARI_DIGIT_CLASS}|\d+-', '', text).replace('॥', '').replace('┃', '').replace('(', '').replace(')', '').strip()
                line = f"{prefix}॥ {clean_text} ॥\n"

        # Apply Renumbering
        if in_mantra_set or in_rik_text:
            def verse_repl(m):
                nonlocal samam_counter, rik_counter, global_samam_total, global_rik_total
                if in_mantra_set:
                    num = int_to_devanagari(samam_counter)
                    samam_counter += 1
                    global_samam_total += 1
                else:
                    num = int_to_devanagari(rik_counter)
                    rik_counter += 1
                    global_rik_total += 1
                return f"॥ {num} ॥"
            
            # Check for joined tags on same line
            if '#' in line:
                parts = line.split('#', 1)
                parts[0] = re.sub(verse_pattern, verse_repl, parts[0])
                line = f"{parts[0].rstrip()}\n#{parts[1]}"
            else:
                line = re.sub(verse_pattern, verse_repl, line)

        # Close blocks AFTER processing line
        if re.search(r'#\s*End of Mantra Sets', line, re.IGNORECASE):
            in_mantra_set = False
        elif re.search(r'#\s*End of Rik Text', line, re.IGNORECASE):
            in_rik_text = False

        final_lines.append(line)

    stats["samams"] = global_samam_total
    stats["riks"] = global_rik_total

    return final_lines, stats


def renumber_text_file(
    input_file: Union[str, Path],
    output_file: Optional[Union[str, Path]] = None,
    preserve_super: bool = False,
    reset_per_super: bool = False,
    reset_samam_per_section: bool = True,
    reset_samam_per_super: bool = True,
    start_sup: int = 1,
    start_sec: int = 1,
    start_sub: int = 1,
    preserve_all: bool = False,
    no_renumber: bool = False,
    custom_version: Optional[str] = None,
    dry_run: bool = False,
    backup: bool = False,
    fail_on_error: bool = True,
    corpus_name: str = "samhita"
) -> bool:
    """
    Orchestrates pre-flight validation, multi-pass renumbering, and metadata injection for a file.
    """
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        return False

    out_path = Path(output_file) if output_file else input_path

    print(f"Processing: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Pre-flight Structural Validation
    print("  Structural Integrity Check...")
    is_valid, errors = validate_structural_tags(lines)
    if not is_valid:
        print("\n[CRITICAL ERROR] Structural Integrity compromised:")
        for err in errors:
            print(f"  - {err}")
        print("\nRenumbering ABORTED to prevent data corruption. Please fix tags and retry.")
        if fail_on_error:
            sys.exit(1)
        return False

    print(f"  Integrity verified ({len(lines):,} lines). Proceeding...")

    # Multi-pass renumbering
    new_lines, stats = renumber_text(
        lines=lines,
        preserve_super=preserve_super,
        reset_per_super=reset_per_super,
        reset_samam_per_section=reset_samam_per_section,
        reset_samam_per_super=reset_samam_per_super,
        start_sup=start_sup,
        start_sec=start_sec,
        start_sub=start_sub,
        preserve_all=preserve_all,
        no_renumber=no_renumber
    )

    final_content_str = "".join(new_lines)

    # Determine Version & Inject Metadata
    meta = get_build_metadata(corpus_name=corpus_name, input_file=input_path, increment=False)
    version_to_use = custom_version if custom_version else meta.get("version", "3.28")
    final_content = inject_metadata_to_text(final_content_str, version_to_use, meta.get("generated_at", ""))

    if dry_run:
        print("[DRY RUN] Completed without writing to disk.")
        print(f"  Stats: {stats['supersections']} SuperSections, {stats['sections']} Sections, "
              f"{stats['subsections']} SubSections | {stats['samams']} Samams, {stats['riks']} Riks.")
        return True

    # Create backup if requested
    if backup and out_path.exists():
        bak_path = out_path.with_suffix(out_path.suffix + ".bak")
        shutil.copy2(out_path, bak_path)
        print(f"  Backup created: {bak_path.name}")

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(final_content)

    if no_renumber:
        print(f"Success! Verified tag balance and metadata injected (inject-only mode) -> {out_path}")
    else:
        print(f"Success! Saved to {out_path}")
        print(f"  Final State: {stats['supersections']} SuperSections, {stats['sections']} Sections, "
              f"{stats['subsections']} SubSections | Total Samams: {stats['samams']}, Total Riks: {stats['riks']}")

    return True


class RenumberEngine:
    """High-level object-oriented interface for renumbering and tag validation."""
    validate_structural_tags = staticmethod(validate_structural_tags)
    renumber_file = staticmethod(renumber_text_file)
    renumber_text = staticmethod(renumber_text)
    inject_metadata = staticmethod(inject_metadata_to_text)


def build_cli_parser() -> argparse.ArgumentParser:
    """Builds the comprehensive, unified CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Unified Jaimineeya Ingestion & Renumbering Tool (3-pass structural and verse renumbering).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    # Target file
    parser.add_argument("input_file", help="Path to input text or markup file")
    parser.add_argument("-o", "--output", help="Path to output file (default: overwrite input in-place)")
    parser.add_argument("-t", "--type", choices=["samhita", "aaranam", "collection"],
                        help="Corpus type preset (loads defaults from pipeline_config.yaml)")

    # Section / Structural Indexing
    parser.add_argument("--start-super", type=int, default=None, help="Starting number for SuperSections")
    parser.add_argument("--start-sec", type=int, default=None, help="Starting number for Sections")
    parser.add_argument("--start-sub", type=int, default=None, help="Starting number for SubSections")
    
    # Reset & Continuity Behavior
    parser.add_argument("--reset-per-super", dest="reset_per_super", action="store_true", default=None,
                        help="Reset Section and SubSection counters at each SuperSection boundary")
    parser.add_argument("--no-reset-per-super", dest="reset_per_super", action="store_false",
                        help="Do not reset Section/SubSection counters across SuperSections")
    parser.add_argument("--contiguous-samams", action="store_true", default=False,
                        help="Do NOT reset Samam numbering at Section boundaries")
    
    # Preservations
    parser.add_argument("--preserve-super", action="store_true", default=False,
                        help="Keep existing SuperSection numbers untouched")
    parser.add_argument("--preserve-all", action="store_true", default=False,
                        help="Keep all structural section/subsection IDs untouched; only renumber verses")

    # Versioning & Metadata
    parser.add_argument("--jsv-version", help="Manual edition version string override (e.g. 3.29)")
    parser.add_argument("--increment", action="store_true", default=False,
                        help="Explicitly increment the corpus edition patch version (e.g. 3.28 -> 3.29)")
    parser.add_argument("--no-increment", action="store_true", default=False,
                        help="Do not increment version in pipeline_config.yaml / metadata header")
    parser.add_argument("--no-renumber", action="store_true", default=False,
                        help="Inject-Only mode: validate tags and update metadata header without modifying verses/IDs")

    # Execution modes
    parser.add_argument("--dry-run", action="store_true", default=False,
                        help="Perform pre-flight checks and preview renumbering stats without writing to disk")
    parser.add_argument("--backup", dest="backup", action="store_true", default=False,
                        help="Create a .bak backup file before overwriting target")
    parser.add_argument("--no-backup", dest="backup", action="store_false",
                        help="Do not create a backup file")

    return parser


def main():
    """Main CLI entrypoint for unified renumbering."""
    parser = build_cli_parser()
    args = parser.parse_args()

    config = load_pipeline_config()
    renum_cfg = config.get("renumber_sooktam", {})

    corpus_type = args.type
    if not corpus_type:
        # Deduce corpus type from path if possible
        lowered = str(args.input_file).lower()
        if "aaranam" in lowered:
            corpus_type = "aaranam"
        elif "collection" in lowered:
            corpus_type = "collection"
        else:
            corpus_type = "samhita"

    type_cfg = renum_cfg.get(corpus_type, {}) if corpus_type else {}

    def resolve(cli_val, yaml_val, fallback):
        if cli_val is not None:
            return cli_val
        if yaml_val is not None:
            return yaml_val
        return fallback

    start_sup = resolve(args.start_super, type_cfg.get("start_super"), 1)
    start_sec = resolve(args.start_sec, type_cfg.get("start_section"), 1)
    start_sub = resolve(args.start_sub, type_cfg.get("start_subsection"), 1)
    reset_sup = resolve(args.reset_per_super, type_cfg.get("reset_per_super"), False)
    
    contiguous_sam = args.contiguous_samams or type_cfg.get("contiguous_samams", False)
    reset_samam_sec = not contiguous_sam

    # Version handling
    if args.jsv_version:
        target_version = args.jsv_version
    elif args.dry_run or args.no_increment or not args.increment:
        target_version = get_corpus_edition(corpus_type)
    else:
        target_version = increment_corpus_edition(corpus_type)

    success = renumber_text_file(
        input_file=args.input_file,
        output_file=args.output,
        preserve_super=args.preserve_super,
        reset_per_super=reset_sup,
        reset_samam_per_section=reset_samam_sec,
        reset_samam_per_super=reset_samam_sec,
        start_sup=start_sup,
        start_sec=start_sec,
        start_sub=start_sub,
        preserve_all=args.preserve_all,
        no_renumber=args.no_renumber,
        custom_version=target_version,
        dry_run=args.dry_run,
        backup=args.backup,
        fail_on_error=True,
        corpus_name=corpus_type
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
