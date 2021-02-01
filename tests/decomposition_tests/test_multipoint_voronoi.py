from ground.hints import (Contour,
                          Multipoint)
from hypothesis import given

from sect.core.voronoi.events.models import are_almost_equal
from sect.decomposition import (Diagram,
                                multipoint_voronoi)
from sect.triangulation import delaunay
from tests.utils import (contour_to_multipoint,
                         to_circumcenter)
from . import strategies


@given(strategies.multipoints)
def test_basic(multipoint: Multipoint) -> None:
    result = multipoint_voronoi(multipoint)

    assert isinstance(result, Diagram)


@given(strategies.rational_contours)
def test_duality(contour: Contour) -> None:
    result = multipoint_voronoi(contour_to_multipoint(contour))

    circumcenters = [to_circumcenter(triangle)
                     for triangle in delaunay(contour.vertices).triangles()]
    assert all(any(are_almost_equal(vertex.x, center.x)
                   and are_almost_equal(vertex.y, center.y)
                   for center in circumcenters)
               for vertex in result.vertices)
