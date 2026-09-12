"""
Typed AST Models for Jaimineeya Samaveda Pipeline.

Provides formal data structures and bi-directional serialization for the
canonical VedicDocument Abstract Syntax Tree (AST).
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, Any, Dict, List, Union


@dataclass
class MantraVerse:
    """Represents an individual mantra verse."""
    corrected_mantra: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"corrected-mantra": self.corrected_mantra}

    @classmethod
    def from_dict(cls, data: Union[Dict[str, Any], str]) -> MantraVerse:
        if isinstance(data, str):
            return cls(corrected_mantra=data)
        return cls(
            corrected_mantra=data.get("corrected-mantra") or data.get("mantra") or ""
        )


@dataclass
class HeaderInfo:
    """Represents header metadata for a subsection."""
    header: str = ""
    header_number: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"header": self.header}
        if self.header_number is not None:
            d["header_number"] = self.header_number
        return d

    @classmethod
    def from_dict(cls, data: Union[Dict[str, Any], str, None]) -> HeaderInfo:
        if not data:
            return cls()
        if isinstance(data, str):
            return cls(header=data)
        return cls(
            header=str(data.get("header", "")),
            header_number=data.get("header_number")
        )


@dataclass
class ProcedureRef:
    """Ritual procedure linkage referencing a prayoga markdown file."""
    file: str = ""
    title: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"file": self.file, "title": self.title}

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional[ProcedureRef]:
        if not data:
            return None
        return cls(
            file=data.get("file", ""),
            title=data.get("title", "")
        )


@dataclass
class SubSection:
    """Represents an individual liturgical subsection."""
    header: HeaderInfo = field(default_factory=HeaderInfo)
    rik_id: Optional[int] = None
    rik_ids: List[int] = field(default_factory=list)
    rik_text: str = ""
    rik_metadata: str = ""
    rik_rishi: str = ""
    rik_devata: str = ""
    rik_chandas: str = ""
    saman_metadata: str = ""
    saman_rishi: str = ""
    saman_devata: str = ""
    saman_chandas: str = ""
    corrected_mantra_sets: List[MantraVerse] = field(default_factory=list)
    content_lines: List[str] = field(default_factory=list)
    footnotes: Dict[str, str] = field(default_factory=dict)
    procedure_ref: Optional[ProcedureRef] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "header": self.header.to_dict(),
            "rik_id": self.rik_id,
            "saman_metadata": self.saman_metadata,
            "mantra_sets": [],
            "corrected-mantra_sets": [m.to_dict() for m in self.corrected_mantra_sets],
            "footnotes": dict(self.footnotes),
            "rik_rishi": self.rik_rishi,
            "rik_devata": self.rik_devata,
            "rik_chandas": self.rik_chandas,
            "saman_rishi": self.saman_rishi,
            "saman_devata": self.saman_devata,
            "saman_chandas": self.saman_chandas,
            "procedure_ref": self.procedure_ref.to_dict() if self.procedure_ref else None,
            "rik_metadata": self.rik_metadata,
            "rik_text": self.rik_text,
        }
        if self.rik_ids:
            d["rik_ids"] = list(self.rik_ids)
        if self.content_lines:
            d["content_lines"] = list(self.content_lines)
        if self.extra:
            for k, v in self.extra.items():
                if k not in d:
                    d[k] = v
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SubSection:
        if not data:
            return cls()
        
        # Parse mantra sets
        raw_m = data.get("corrected-mantra_sets", []) or data.get("mantra_sets", [])
        mantra_sets = [MantraVerse.from_dict(m) for m in raw_m]

        # Parse procedure ref
        raw_proc = data.get("procedure_ref")
        proc_ref = ProcedureRef.from_dict(raw_proc) if raw_proc else None

        # Parse footnotes
        raw_fn = data.get("footnotes", {})
        footnotes = dict(raw_fn) if isinstance(raw_fn, dict) else {}

        # Known standard keys
        standard_keys = {
            "header", "rik_id", "rik_ids", "rik_text", "rik_metadata",
            "rik_rishi", "rik_devata", "rik_chandas",
            "saman_metadata", "saman_rishi", "saman_devata", "saman_chandas",
            "mantra_sets", "corrected-mantra_sets", "content_lines",
            "footnotes", "procedure_ref"
        }
        extra = {k: v for k, v in data.items() if k not in standard_keys}

        return cls(
            header=HeaderInfo.from_dict(data.get("header")),
            rik_id=data.get("rik_id"),
            rik_ids=list(data.get("rik_ids", [])),
            rik_text=str(data.get("rik_text", "")),
            rik_metadata=str(data.get("rik_metadata", "")),
            rik_rishi=str(data.get("rik_rishi", "")),
            rik_devata=str(data.get("rik_devata", "")),
            rik_chandas=str(data.get("rik_chandas", "")),
            saman_metadata=str(data.get("saman_metadata", "")),
            saman_rishi=str(data.get("saman_rishi", "")),
            saman_devata=str(data.get("saman_devata", "")),
            saman_chandas=str(data.get("saman_chandas", "")),
            corrected_mantra_sets=mantra_sets,
            content_lines=list(data.get("content_lines", [])),
            footnotes=footnotes,
            procedure_ref=proc_ref,
            extra=extra
        )


@dataclass
class Section:
    """Represents a major section (Khandah / Kandah)."""
    section_title: str = ""
    count: Optional[str] = None
    subsections: Dict[str, SubSection] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "section_title": self.section_title,
            "subsections": {k: sub.to_dict() for k, sub in self.subsections.items()}
        }
        if self.count is not None:
            d["count"] = self.count
        if self.extra:
            for k, v in self.extra.items():
                if k not in d:
                    d[k] = v
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Section:
        if not data:
            return cls()
        
        subsections: Dict[str, SubSection] = {}
        raw_subs = data.get("subsections", {})
        if isinstance(raw_subs, dict):
            for k, v in raw_subs.items():
                if isinstance(v, dict):
                    subsections[k] = SubSection.from_dict(v)

        standard_keys = {"section_title", "count", "subsections"}
        extra = {k: v for k, v in data.items() if k not in standard_keys}

        return cls(
            section_title=str(data.get("section_title", "")),
            count=data.get("count"),
            subsections=subsections,
            extra=extra
        )


@dataclass
class SuperSection:
    """Represents a major patha or parva division."""
    supersection_title: str = ""
    count: Optional[str] = None
    sections: Dict[str, Section] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "supersection_title": self.supersection_title,
            "sections": {k: sec.to_dict() for k, sec in self.sections.items()}
        }
        if self.count is not None:
            d["count"] = self.count
        if self.extra:
            for k, v in self.extra.items():
                if k not in d:
                    d[k] = v
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SuperSection:
        if not data:
            return cls()

        sections: Dict[str, Section] = {}
        raw_secs = data.get("sections", {})
        if isinstance(raw_secs, dict):
            for k, v in raw_secs.items():
                if k == "count":
                    continue
                if isinstance(v, dict):
                    sections[k] = Section.from_dict(v)

        standard_keys = {"supersection_title", "count", "sections"}
        extra = {k: v for k, v in data.items() if k not in standard_keys}

        return cls(
            supersection_title=str(data.get("supersection_title", "")),
            count=data.get("count"),
            sections=sections,
            extra=extra
        )


@dataclass
class DocumentMeta:
    """Metadata container for a Vedic document."""
    title: str = ""
    version: str = ""
    generated_at: str = ""
    source: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "title": self.title,
            "version": self.version,
            "generated_at": self.generated_at,
        }
        if self.source:
            d["source"] = self.source
        if self.extra:
            for k, v in self.extra.items():
                if k not in d:
                    d[k] = v
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DocumentMeta:
        if not data:
            return cls()
        standard_keys = {"title", "version", "generated_at", "source"}
        extra = {k: v for k, v in data.items() if k not in standard_keys}
        return cls(
            title=str(data.get("title", "")),
            version=str(data.get("version", "")),
            generated_at=str(data.get("generated_at", "")),
            source=str(data.get("source", "")),
            extra=extra
        )


@dataclass
class VedicDocument:
    """Master document model encapsulating the complete AST."""
    meta: DocumentMeta = field(default_factory=DocumentMeta)
    supersections: Dict[str, SuperSection] = field(default_factory=dict)
    closing_mantras: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self, use_singular_supersection: bool = False) -> Dict[str, Any]:
        """Serializes back to JSON-compatible dictionary."""
        ss_key = "supersection" if use_singular_supersection else "supersections"
        d: Dict[str, Any] = {
            "meta": self.meta.to_dict(),
            ss_key: {k: ss.to_dict() for k, ss in self.supersections.items()},
            "closing_mantras": list(self.closing_mantras),
        }
        if self.extra:
            for k, v in self.extra.items():
                if k not in d:
                    d[k] = v
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> VedicDocument:
        """Parses a dictionary into a validated VedicDocument instance."""
        meta = DocumentMeta.from_dict(data.get("meta", {}))
        
        # Handle both 'supersection' and 'supersections'
        raw_ss = data.get("supersections") or data.get("supersection", {})
        supersections: Dict[str, SuperSection] = {}
        if isinstance(raw_ss, dict):
            for k, v in raw_ss.items():
                if k == "count":
                    continue
                if isinstance(v, dict):
                    supersections[k] = SuperSection.from_dict(v)

        closing_mantras = list(
            data.get("closing_mantras") or data.get("closing-mantras") or []
        )

        standard_keys = {"meta", "supersections", "supersection", "closing_mantras", "closing-mantras"}
        extra = {k: v for k, v in data.items() if k not in standard_keys}

        return cls(
            meta=meta,
            supersections=supersections,
            closing_mantras=closing_mantras,
            extra=extra
        )
