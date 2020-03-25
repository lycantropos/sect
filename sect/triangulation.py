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
    return Triangulation.from_points(points)


def constrained_delaunay(border: Contour,
                         holes: Sequence[Contour] = (),
                         *,
                         extra_points: Sequence[Point] = (),
                         extra_constraints: Iterable[Segment] = ()
                         ) -> Triangulation:
    result = delaunay(chain(border, _flatten(holes), extra_points))
    border_segments = _contour_to_segments(border)
    result.constrain(chain(border_segments,
                           _flatten(map(_contour_to_segments, holes)),
                           extra_constraints))
    result.bound(border_segments)
    result.cut(holes)
    return result


def delaunay_triangles(points: Sequence[Point]) -> List[Triangle]:
    return delaunay(points).triangles()


def constrained_delaunay_triangles(border: Contour,
                                   holes: Sequence[Contour] = (),
                                   *,
                                   extra_points: Sequence[Point],
                                   extra_constraints: Sequence[Segment] = ()
                                   ) -> List[Triangle]:
    return (constrained_delaunay(border, holes,
                                 extra_points=extra_points,
                                 extra_constraints=extra_constraints)
            .triangles())
