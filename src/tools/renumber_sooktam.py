"""
Legacy Compatibility Wrapper for renumber_sooktam.py
----------------------------------------------------
This module delegates directly to the canonical Unified Ingestion & Renumbering
Tool located at src/ingest/renumber.py.

Maintained for backward compatibility with existing build scripts and workflows.
"""

import sys
from pathlib import Path

# Ensure src/ is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

try:
    from ingest.renumber import (
        validate_structural_tags,
        inject_metadata_to_text,
        renumber_text,
        renumber_text_file,
        RenumberEngine,
        main,
        build_cli_parser
    )
    from core.swara_engine import int_to_devanagari, devanagari_to_int
    from core.version import get_corpus_edition, set_corpus_edition, increment_corpus_edition
except ImportError:
    from src.ingest.renumber import (
        validate_structural_tags,
        inject_metadata_to_text,
        renumber_text,
        renumber_text_file,
        RenumberEngine,
        main,
        build_cli_parser
    )
    from src.core.swara_engine import int_to_devanagari, devanagari_to_int
    from src.core.version import get_corpus_edition, set_corpus_edition, increment_corpus_edition

# Legacy helper aliases
def get_project_version(corpus: str = "samhita") -> str:
    return get_corpus_edition(corpus)

def set_project_version(version: str, corpus: str = "samhita") -> bool:
    return set_corpus_edition(corpus, version)

def increment_project_version(corpus: str = "samhita") -> str:
    return increment_corpus_edition(corpus)


if __name__ == "__main__":
    main()
