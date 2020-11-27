from hypothesis import given

from sect.decomposition import (Diagram,
                                multipoint_voronoi)
from sect.hints import Multipoint
from sect.triangulation import delaunay_triangles
from tests.utils import to_circumcenter
from . import strategies


@given(strategies.multipoints)
def test_basic(multipoint: Multipoint) -> None:
    result = multipoint_voronoi(multipoint)

    assert isinstance(result, Diagram)


@given(strategies.rational_multipoints)
def test_duality(multipoint: Multipoint) -> None:
    result = multipoint_voronoi(multipoint)

    assert ({(vertex.x, vertex.y) for vertex in result.vertices}
            == {to_circumcenter(triangle)
                for triangle in delaunay_triangles(multipoint)})
