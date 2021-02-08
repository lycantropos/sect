from typing import Type

from ground.hints import Multisegment
from hypothesis import given

from sect.decomposition import Diagram
from tests.utils import multisegment_pop_left
from . import strategies


@given(strategies.diagram_classes, strategies.rational_multisegments)
def test_basic(diagram_cls: Type[Diagram],
               multisegment: Multisegment) -> None:
    result = diagram_cls.from_multisegment(multisegment)

    assert isinstance(result, diagram_cls)


@given(strategies.diagram_classes, strategies.empty_multisegments)
def test_base_case(diagram_cls: Type[Diagram],
                   multisegment: Multisegment) -> None:
    result = diagram_cls.from_multisegment(multisegment)

    assert not result.cells
    assert not result.edges
    assert not result.vertices


@given(strategies.diagram_classes, strategies.non_empty_rational_multisegments)
def test_step(diagram_cls: Type[Diagram],
              multisegment: Multisegment) -> None:
    first_segment, rest_multisegment = multisegment_pop_left(multisegment)

    result = diagram_cls.from_multisegment(rest_multisegment)
    next_result = diagram_cls.from_multisegment(multisegment)

    assert len(result.cells) < len(next_result.cells)
    assert len(result.edges) < len(next_result.edges)
    assert len(result.vertices) <= len(next_result.vertices)
