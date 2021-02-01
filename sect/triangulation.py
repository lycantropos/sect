from itertools import chain
from typing import (Iterable,
                    Sequence)

from ground.hints import (Point,
                          Polygon,
                          Segment)

from .core import raw as _raw
from .core.delaunay.quad_edge import QuadEdge
from .core.delaunay.triangulation import Triangulation
from .core.delaunay.utils import (complete_vertices as _complete_vertices,
                                  contour_to_segments as _contour_to_segments)
from .core.utils import flatten as _flatten

QuadEdge = QuadEdge
Triangulation = Triangulation


def delaunay(points: Iterable[Point]) -> Triangulation:
    """
    Returns Delaunay triangulation of the points.

    Based on divide-and-conquer algorithm by L. Guibas & J. Stolfi.

    Time complexity:
        ``O(len(points) * log len(points))``
    Memory complexity:
        ``O(len(points))``
    Reference:
        http://www.sccg.sk/~samuelcik/dgs/quad_edge.pdf

    :param points: 3 or more points to triangulate.
    :returns: triangulation of the points.
    """
    return Triangulation.from_points(points)


def constrained_delaunay(polygon: Polygon,
                         *,
                         extra_points: Sequence[Point] = (),
                         extra_constraints: Iterable[Segment] = ()
                         ) -> Triangulation:
    """
    Returns constrained Delaunay triangulation of the polygon
    given by border and holes (with potentially extra points and constraints).

    Based on

    * divide-and-conquer algorithm by L. Guibas & J. Stolfi
      for generating Delaunay triangulation,

    * algorithm by S. W. Sloan for adding constraints to Delaunay
      triangulation,

    * clipping algorithm by F. Martinez et al. for deleting in-hole triangles.

    Time complexity:
        ``O(vertices_count * log vertices_count)`` for convex polygons
        without extra constraints,
        ``O(vertices_count ** 2)`` otherwise,
        where ``vertices_count = len(border) + sum(map(len, holes))\
 + len(extra_points) + len(extra_constraints)``.
    Memory complexity:
        ``O(vertices_count)``,
        where ``vertices_count = len(border) + sum(map(len, holes))\
 + len(extra_points) + len(extra_constraints)``.
    Reference:
        http://www.sccg.sk/~samuelcik/dgs/quad_edge.pdf
        https://www.newcastle.edu.au/__data/assets/pdf_file/0019/22519/23_A-fast-algortithm-for-generating-constrained-Delaunay-triangulations.pdf
        https://doi.org/10.1016/j.advengsoft.2013.04.004
        http://www4.ujaen.es/~fmartin/bool_op.html

    :param polygon: target polygon.
    :param extra_points:
        additional points to be presented in the triangulation.
    :param extra_constraints:
        additional constraints to be presented in the triangulation.
    :returns:
        triangulation of the border, holes & extra points
        considering constraints.
    """
    border, holes = polygon.border, polygon.holes
    if extra_points:
        border, holes, extra_points = _complete_vertices(border, holes,
                                                         extra_points)
    result = delaunay(chain(border.vertices,
                            _flatten(hole.vertices for hole in holes),
                            extra_points))
    border_segments = _contour_to_segments(_raw.from_contour(border))
    result.constrain(chain(border_segments,
                           _flatten(map(_contour_to_segments,
                                        _raw.from_multiregion(holes))),
                           extra_constraints))
    result.bound(border_segments)
    result.cut(_raw.from_multiregion(holes))
    return result
