"""
Legacy Compatibility Wrapper for renumber_sections.py
------------------------------------------------------
Delegates to the canonical Unified Ingestion & Renumbering Tool (src/ingest/renumber.py).
Maintained for backward compatibility with legacy scripts.
"""

import sys
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from ingest.renumber import renumber_text_file


def main():
    parser = argparse.ArgumentParser(description="Renumber supersections, sections, and subsections in a Jaimineeya text file.")
    parser.add_argument('input_file', help="Path to the input text file")
    parser.add_argument('--start-super', type=int, default=1, help="Starting number for supersections")
    parser.add_argument('--start-sec', type=int, default=1, help="Starting number for sections")
    parser.add_argument('--start-sub', type=int, default=1, help="Starting number for subsections")
    parser.add_argument('--dry-run', action='store_true', help="Print changes without writing to file")
    
    args = parser.parse_args()

    success = renumber_text_file(
        input_file=args.input_file,
        start_sup=args.start_super,
        start_sec=args.start_sec,
        start_sub=args.start_sub,
        dry_run=args.dry_run,
        fail_on_error=True
    )
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
