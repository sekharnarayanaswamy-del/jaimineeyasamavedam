"""
Base Renderer interface for the Jaimineeya Samaveda Pipeline.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pathlib import Path

from src.core.models import VedicDocument


class BaseRenderer(ABC):
    """Abstract base class for all Vedic text renderers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    def render(
        self,
        document: VedicDocument,
        output_path: Path,
        **kwargs: Any
    ) -> int:
        """
        Renders the given VedicDocument to the target output path.
        
        Returns:
            Exit code (0 for success, non-zero for failure).
        """
        pass
