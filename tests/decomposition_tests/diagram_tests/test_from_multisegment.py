from typing import Type

from ground.hints import Multisegment
from hypothesis import given

from sect.decomposition import Diagram
from . import strategies


@given(strategies.diagram_classes, strategies.rational_multisegments)
def test_basic(diagram_cls: Type[Diagram],
               multisegment: Multisegment) -> None:
    result = diagram_cls.from_multisegment(multisegment)

    assert isinstance(result, Diagram)


@given(strategies.diagram_classes, strategies.empty_multisegments)
def test_empty(diagram_cls: Type[Diagram],
               multisegment: Multisegment) -> None:
    result = diagram_cls.from_multisegment(multisegment)

    assert not result.cells
    assert not result.edges
    assert not result.vertices
