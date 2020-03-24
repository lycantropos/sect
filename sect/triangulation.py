from typing import (List,
                    Optional,
                    Sequence)

from .core.delaunay import Triangulation
from .hints import (Point,
                    Segment,
                    Triangle)

Triangulation = Triangulation


def delaunay(points: Sequence[Point]) -> Triangulation:
    return Triangulation.from_points(points)


def constrained_delaunay(points: Sequence[Point],
                         *,
                         border: Sequence[Segment],
                         extra_constraints: Optional[Sequence[Segment]] = None
                         ) -> Triangulation:
    result = delaunay(points)
    result.constrain(border, extra_constraints)
    return result


def delaunay_triangles(points: Sequence[Point]) -> List[Triangle]:
    return delaunay(points).triangles()


def constrained_delaunay_triangles(
        points: Sequence[Point],
        *,
        border: Sequence[Segment],
        extra_constraints: Optional[Sequence[Segment]] = None
) -> List[Triangle]:
    return (constrained_delaunay(points,
                                 border=border,
                                 extra_constraints=extra_constraints)
            .triangles())
