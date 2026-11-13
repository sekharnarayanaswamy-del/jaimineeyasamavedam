#!/usr/bin/env python3
"""
CLI entry point for applying selected Sanskrit Sandhi corrections.
Forwards to src/tools/apply_sandhi_patch.py.
"""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.tools.apply_sandhi_patch import main

if __name__ == '__main__':
    main()
