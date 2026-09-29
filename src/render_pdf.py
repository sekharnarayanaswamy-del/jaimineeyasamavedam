"""
Backward-compatibility wrapper for src/render.py.
-------------------------------------------------
Maintains 100% backward compatibility for existing scripts and CLI invocations
that still call or import from `render_pdf`. All actual document compilation logic
now resides in `src/render.py` and `src/renderers/`.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = Path(__file__).resolve().parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Re-export all symbols from the unified render engine
from src.render import *

if __name__ == "__main__":
    from src.render import main
    main()