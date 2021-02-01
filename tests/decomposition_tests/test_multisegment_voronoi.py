from ground.hints import Multisegment
from hypothesis import given

from sect.decomposition import (Diagram,
                                multisegment_voronoi)
from . import strategies


@given(strategies.rational_multisegments)
def test_basic(multisegment: Multisegment) -> None:
    result = multisegment_voronoi(multisegment)

    assert isinstance(result, Diagram)


@given(strategies.empty_multisegments)
def test_empty(multisegment: Multisegment) -> None:
    result = multisegment_voronoi(multisegment)

    assert not result.cells
    assert not result.edges
    assert not result.vertices
