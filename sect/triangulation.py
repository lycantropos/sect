from itertools import chain
from typing import (Iterable,
                    List,
                    Sequence)

from .core.delaunay import Triangulation
from .core.utils import (contour_to_segments as _contour_to_segments,
                         flatten as _flatten)
from .hints import (Contour,
                    Point,
                    Segment,
                    Triangle)

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

    :param points: points to triangulate
    :returns: triangulation of the points.
    """
    return Triangulation.from_points(points)


def constrained_delaunay(border: Contour,
                         holes: Sequence[Contour] = (),
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
        ``O(vertices_count)``
        where ``vertices_count = len(border) + sum(map(len, holes))\
 + len(extra_points) + len(extra_constraints)``.
    Reference:
        http://www.sccg.sk/~samuelcik/dgs/quad_edge.pdf
        https://www.newcastle.edu.au/__data/assets/pdf_file/0019/22519/23_A-fast-algortithm-for-generating-constrained-Delaunay-triangulations.pdf
        https://doi.org/10.1016/j.advengsoft.2013.04.004
        http://www4.ujaen.es/~fmartin/bool_op.html

    :param border: border of the polygon.
    :param holes: holes of the polygon.
    :param extra_points:
        additional points to be presented in the triangulation.
    :param extra_constraints:
        additional constraints to be presented in the triangulation.
    :returns:
        triangulation of the border, holes & extra points
        considering constraints.
    """
    result = delaunay(chain(border, _flatten(holes), extra_points))
    border_segments = _contour_to_segments(border)
    result.constrain(chain(border_segments,
                           _flatten(map(_contour_to_segments, holes)),
                           extra_constraints))
    result.bound(border_segments)
    result.cut(holes)
    return result


def delaunay_triangles(points: Sequence[Point]) -> List[Triangle]:
    """
    Returns Delaunay subdivision of the points into triangles.

    Based on divide-and-conquer algorithm by L. Guibas & J. Stolfi.

    Time complexity:
        ``O(len(points) * log len(points))``
    Memory complexity:
        ``O(len(points))``
    Reference:
        http://www.sccg.sk/~samuelcik/dgs/quad_edge.pdf

    :param points: points to triangulate
    :returns: Delaunay subdivision of the points into triangles.

    >>> (delaunay_triangles([(0, 0), (3, 0), (0, 3)])
    ...  == [((0, 0), (3, 0), (0, 3))])
    True
    >>> (delaunay_triangles([(0, 0), (3, 0), (3, 3), (0, 3)])
    ...  == [((0, 3), (3, 0), (3, 3)), ((0, 0), (3, 0), (0, 3))])
    True
    >>> (delaunay_triangles([(0, 0), (3, 0), (1, 1), (0, 3)])
    ...  == [((0, 0), (3, 0), (1, 1)),
    ...      ((0, 0), (1, 1), (0, 3)),
    ...      ((0, 3), (1, 1), (3, 0))])
    True
    """
    return delaunay(points).triangles()


def constrained_delaunay_triangles(border: Contour,
                                   holes: Sequence[Contour] = (),
                                   *,
                                   extra_points: Sequence[Point] = (),
                                   extra_constraints: Sequence[Segment] = ()
                                   ) -> List[Triangle]:
    """
    Returns subdivision of the polygon given by border and holes
    (with potentially extra points and constraints)
    into triangles.

    Based on
    - divide-and-conquer algorithm by L. Guibas & J. Stolfi
    for generating Delaunay triangulation,
    - algorithm by S. W. Sloan for adding constraints to Delaunay
    triangulation,
    - algorithm by F. Martinez et al. for deleting in-hole triangles.

    Time complexity:
        ``O(vertices_count * log vertices_count)`` for convex polygons
        without extra constraints,
        ``O(vertices_count ** 2)`` otherwise,
        where ``vertices_count = len(border) + sum(map(len, holes))\
 + len(extra_points) + len(extra_constraints)``.
    Memory complexity:
        ``O(vertices_count)``
        where ``vertices_count = len(border) + sum(map(len, holes))\
 + len(extra_points) + len(extra_constraints)``.
    Reference:
        http://www.sccg.sk/~samuelcik/dgs/quad_edge.pdf
        https://www.newcastle.edu.au/__data/assets/pdf_file/0019/22519/23_A-fast-algortithm-for-generating-constrained-Delaunay-triangulations.pdf
        https://doi.org/10.1016/j.advengsoft.2013.04.004
        http://www4.ujaen.es/~fmartin/bool_op.html

    :param border: border of the polygon.
    :param holes: holes of the polygon.
    :param extra_points:
        additional points to be presented in the triangulation.
    :param extra_constraints:
        additional constraints to be presented in the triangulation.
    :returns:
        subdivision of the border, holes & extra points
        considering constraints into triangles.

    >>> (constrained_delaunay_triangles([(0, 0), (3, 0), (0, 3)])
    ...  == [((0, 0), (3, 0), (0, 3))])
    True
    >>> (constrained_delaunay_triangles([(0, 0), (3, 0), (3, 3), (0, 3)])
    ...  == [((0, 3), (3, 0), (3, 3)), ((0, 0), (3, 0), (0, 3))])
    True
    >>> (constrained_delaunay_triangles([(0, 0), (3, 0), (1, 1), (0, 3)])
    ...  == [((0, 0), (3, 0), (1, 1)),
    ...      ((0, 0), (1, 1), (0, 3))])
    True
    """
    return (constrained_delaunay(border, holes,
                                 extra_points=extra_points,
                                 extra_constraints=extra_constraints)
            .triangles())
