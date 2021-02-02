from typing import Type

from ground.hints import (Contour,
                          Multipoint)
from hypothesis import given

from sect.core.voronoi.events.models import are_almost_equal
from sect.decomposition import Diagram
from sect.triangulation import Triangulation
from tests.utils import (contour_to_multipoint,
                         to_circumcenter)
from . import strategies


@given(strategies.diagram_classes, strategies.multipoints)
def test_basic(diagram_cls: Type[Diagram],
               multipoint: Multipoint) -> None:
    result = diagram_cls.from_multipoint(multipoint)

    assert isinstance(result, diagram_cls)


@given(strategies.diagram_classes, strategies.triangulation_classes,
       strategies.rational_contours)
def test_duality(diagram_cls: Type[Diagram],
                 triangulation_cls: Type[Triangulation],
                 contour: Contour) -> None:
    contour_vertices_multipoint = contour_to_multipoint(contour)

    result = diagram_cls.from_multipoint(contour_vertices_multipoint)

    circumcenters = [
        to_circumcenter(triangle)
        for triangle in (triangulation_cls.delaunay(contour.vertices)
                         .triangles())]
    assert all(any(are_almost_equal(vertex.x, center.x)
                   and are_almost_equal(vertex.y, center.y)
                   for center in circumcenters)
               for vertex in result.vertices)
