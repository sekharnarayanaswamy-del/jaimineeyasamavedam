"""
Data models representing the Jaimineeya hierarchy (Parva -> Kandah -> Sama)
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Sama:
    """Represents a single Sama (verse/song)"""
    id: str
    title: str = ""
    rik_metadata: str = ""
    saman_metadata: str = ""
    rik_text: str = ""
    mantra_text: str = ""
    procedure_ref: Dict = field(default_factory=dict)
    footnotes: List[str] = field(default_factory=list)
    audio_filename: str = ""
    sama_number: int = 0
    global_number: int = 0  # Global sama number across all kandahs
    
    # Classification Fields
    saman_rishi: str = ""
    saman_devata: str = ""
    saman_chandas: str = ""
    rik_rishi: str = ""
    rik_devata: str = ""
    rik_chandas: str = ""
    rik_classifications: List[Dict] = field(default_factory=list)
    rik_ids: List[int] = field(default_factory=list)  # Relative Rik IDs in Kandah


@dataclass
class Kandah:
    """Represents a Kandah (chapter/section)"""
    id: str
    title: str
    samas: List[Sama] = field(default_factory=list)
    kandah_number: int = 0


@dataclass
class Parva:
    """Represents a Parva (top-level supersection)"""
    id: str
    title: str
    kandahs: List[Kandah] = field(default_factory=list)
    parva_number: int = 0
