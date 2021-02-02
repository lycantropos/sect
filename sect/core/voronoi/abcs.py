from abc import (ABC,
                 abstractmethod)
from typing import List

from ground.hints import (Multipoint,
                          Multisegment)

from .faces import (Cell,
                    Edge,
                    Vertex)


class Diagram(ABC):
    cells = ...  # type: List[Cell]
    edges = ...  # type: List[Edge]
    vertices = ...  # type: List[Vertex]

    @classmethod
    @abstractmethod
    def from_multipoint(cls, multipoint: Multipoint) -> 'Diagram':
        """Constructs diagram from given multipoint."""

    @classmethod
    @abstractmethod
    def from_multisegment(cls, multisegment: Multisegment) -> 'Diagram':
        """Constructs diagram from given multisegment."""
