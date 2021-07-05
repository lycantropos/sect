import random
from typing import List

from ground.base import (Context,
                         Location,
                         Orientation)
from ground.hints import (Box,
                          Multisegment,
                          Point,
                          Polygon)
from reprit.base import generate_repr

from sect.core.utils import (contour_to_edges_endpoints,
                             to_contour_orientation)
from .edge import Edge
from .hints import Shuffler
from .leaf import Leaf
from .node import Node
from .trapezoid import Trapezoid
from .x_node import XNode
from .y_node import YNode


class Graph:
    """Represents trapezoidal decomposition graph."""

    @classmethod
    def from_multisegment(cls,
                          multisegment: Multisegment,
                          *,
                          shuffler: Shuffler = random.shuffle,
                          context: Context) -> 'Graph':
        """
        Constructs trapezoidal decomposition graph of given multisegment.

        Based on incremental randomized algorithm by R. Seidel.

        Time complexity:
            ``O(segments_count * log segments_count)`` expected,
            ``O(segments_count ** 2)`` worst
        Memory complexity:
            ``O(segments_count)``

        where ``segments_count = len(multisegment.segments)``

        Reference:
            https://doi.org/10.1016%2F0925-7721%2891%2990012-4
            https://www.cs.princeton.edu/courses/archive/fall05/cos528/handouts/A%20Simple%20and%20fast.pdf

        :param multisegment: target multisegment.
        :param shuffler:
            function which mutates sequence by shuffling its elements,
            required for randomization.
        :param context: geometric context.
        :returns: trapezoidal decomposition graph of the multisegment.

        >>> from ground.base import get_context
        >>> context = get_context()
        >>> Multisegment, Point, Segment = (context.multisegment_cls,
        ...                                 context.point_cls,
        ...                                 context.segment_cls)
        >>> graph = Graph.from_multisegment(
        ...     Multisegment([Segment(Point(0, 0), Point(1, 0)),
        ...                   Segment(Point(0, 0), Point(0, 1))]),
        ...     context=context)
        >>> Point(1, 0) in graph
        True
        >>> Point(0, 1) in graph
        True
        >>> Point(1, 1) in graph
        False
        >>> graph.locate(Point(1, 0)) is Location.BOUNDARY
        True
        >>> graph.locate(Point(0, 1)) is Location.BOUNDARY
        True
        >>> graph.locate(Point(1, 1)) is Location.EXTERIOR
        True
        """
        edges = [
            Edge.from_endpoints(segment.start, segment.end, False, context)
            if segment.start < segment.end
            else Edge.from_endpoints(segment.end, segment.start, False,
                                     context)
            for segment in multisegment.segments]
        shuffler(edges)
        result = cls(box_to_node(context.segments_box(multisegment.segments),
                                 context))
        for edge in edges:
            add_edge(result, edge)
        return result

    @classmethod
    def from_polygon(cls,
                     polygon: Polygon,
                     *,
                     shuffler: Shuffler = random.shuffle,
                     context: Context) -> 'Graph':
        """
        Constructs trapezoidal decomposition graph of given polygon.

        Based on incremental randomized algorithm by R. Seidel.

        Time complexity:
            ``O(vertices_count * log vertices_count)`` expected,
            ``O(vertices_count ** 2)`` worst
        Memory complexity:
            ``O(vertices_count)``

        where

            .. code-block:: python

                vertices_count = (len(polygon.border.vertices)
                                  + sum(len(hole.vertices)
                                        for hole in polygon.holes)
                                  + len(extra_points) + len(extra_constraints))

        Reference:
            https://doi.org/10.1016%2F0925-7721%2891%2990012-4
            https://www.cs.princeton.edu/courses/archive/fall05/cos528/handouts/A%20Simple%20and%20fast.pdf

        :param polygon: target polygon.
        :param shuffler:
            function which mutates sequence by shuffling its elements,
            required for randomization.
        :param context: geometric context.
        :returns: trapezoidal decomposition graph of the border and holes.

        >>> from ground.base import get_context
        >>> context = get_context()
        >>> Contour, Point, Polygon = (context.contour_cls, context.point_cls,
        ...                            context.polygon_cls)
        >>> graph = Graph.from_polygon(
        ...     Polygon(Contour([Point(0, 0), Point(6, 0), Point(6, 6),
        ...                      Point(0, 6)]),
        ...             [Contour([Point(2, 2), Point(2, 4), Point(4, 4),
        ...                       Point(4, 2)])]),
        ...     context=context)
        >>> Point(1, 1) in graph
        True
        >>> Point(2, 2) in graph
        True
        >>> Point(3, 3) in graph
        False
        >>> graph.locate(Point(1, 1)) is Location.INTERIOR
        True
        >>> graph.locate(Point(2, 2)) is Location.BOUNDARY
        True
        >>> graph.locate(Point(3, 3)) is Location.EXTERIOR
        True
        """
        border = polygon.border
        orienteer = context.angle_orientation
        is_border_positively_oriented = (to_contour_orientation(border,
                                                                orienteer)
                                         is Orientation.COUNTERCLOCKWISE)
        edges = [
            Edge.from_endpoints(start, end, is_border_positively_oriented,
                                context)
            if start < end
            else Edge.from_endpoints(end, start,
                                     not is_border_positively_oriented,
                                     context)
            for start, end in contour_to_edges_endpoints(border)]
        for hole in polygon.holes:
            is_hole_negatively_oriented = (
                    to_contour_orientation(hole, orienteer)
                    is Orientation.CLOCKWISE)
            edges.extend(
                    Edge.from_endpoints(start, end,
                                        is_hole_negatively_oriented,
                                        context)
                    if start < end
                    else
                    Edge.from_endpoints(end, start,
                                        not is_hole_negatively_oriented,
                                        context)
                    for start, end in contour_to_edges_endpoints(hole))
        shuffler(edges)
        result = cls(box_to_node(context.contour_box(border), context))
        for edge in edges:
            add_edge(result, edge)
        return result

    @property
    def height(self) -> int:
        """
        Returns height of the root node.
        """
        return self.root.height

    __slots__ = 'root',

    def __init__(self, root: Node) -> None:
        """
        Initializes graph.

        Time complexity:
            ``O(1)``
        Memory complexity:
            ``O(1)``
        """
        self.root = root

    def __contains__(self, point: Point) -> bool:
        """
        Checks if point is contained in decomposed geometry.

        Time complexity:
            ``O(self.height)``
        Memory complexity:
            ``O(1)``
        """
        return bool(self.root.locate(point))

    __repr__ = generate_repr(__init__)

    def locate(self, point: Point) -> Location:
        """
        Finds location of point relative to decomposed geometry.

        Time complexity:
            ``O(self.height)``
        Memory complexity:
            ``O(1)``
        """
        return self.root.locate(point)


def add_edge(graph: Graph, edge: Edge) -> None:
    trapezoids = find_intersecting_trapezoids(graph, edge)
    edge_left, edge_right = edge.left, edge.right
    prev_trapezoid = prev_below = prev_above = None
    for index, trapezoid in enumerate(trapezoids):
        is_first, is_last = index == 0, index == len(trapezoids) - 1
        have_left, have_right = (is_first and edge_left != trapezoid.left,
                                 is_last and edge_right != trapezoid.right)
        left = right = None
        if is_first and is_last:
            if have_left:
                left = Trapezoid(trapezoid.left, edge_left, trapezoid.below,
                                 trapezoid.above)
            below = Trapezoid(edge_left, edge_right, trapezoid.below, edge)
            above = Trapezoid(edge_left, edge_right, edge, trapezoid.above)
            if have_right:
                right = Trapezoid(edge_right, trapezoid.right, trapezoid.below,
                                  trapezoid.above)
            if have_left:
                left.lower_left = trapezoid.lower_left
                left.upper_left = trapezoid.upper_left
                left.lower_right = below
                left.upper_right = above
            else:
                below.lower_left = trapezoid.lower_left
                above.upper_left = trapezoid.upper_left
            if have_right:
                right.lower_right = trapezoid.lower_right
                right.upper_right = trapezoid.upper_right
                below.lower_right = right
                above.upper_right = right
            else:
                below.lower_right = trapezoid.lower_right
                above.upper_right = trapezoid.upper_right
        elif is_first:
            # old trapezoid is the first of 2+ trapezoids
            # that the segment intersects
            if have_left:
                left = Trapezoid(trapezoid.left, edge_left, trapezoid.below,
                                 trapezoid.above)
            below = Trapezoid(edge_left, trapezoid.right, trapezoid.below,
                              edge)
            above = Trapezoid(edge_left, trapezoid.right, edge,
                              trapezoid.above)
            # set pairs of trapezoid neighbours
            if have_left:
                left.lower_left = trapezoid.lower_left
                left.upper_left = trapezoid.upper_left
                left.lower_right = below
                left.upper_right = above
            else:
                below.lower_left = trapezoid.lower_left
                above.upper_left = trapezoid.upper_left
            below.lower_right = trapezoid.lower_right
            above.upper_right = trapezoid.upper_right
        elif is_last:
            # old trapezoid is the last of 2+ trapezoids
            # that the segment intersects
            if prev_below.below is trapezoid.below:
                below = prev_below
                below.right = edge_right
            else:
                below = Trapezoid(trapezoid.left, edge_right, trapezoid.below,
                                  edge)
            if prev_above.above is trapezoid.above:
                above = prev_above
                above.right = edge_right
            else:
                above = Trapezoid(trapezoid.left, edge_right, edge,
                                  trapezoid.above)
            if have_right:
                right = Trapezoid(edge_right, trapezoid.right, trapezoid.below,
                                  trapezoid.above)
            # set pairs of trapezoid neighbours
            if have_right:
                right.lower_right = trapezoid.lower_right
                right.upper_right = trapezoid.upper_right
                below.lower_right = right
                above.upper_right = right
            else:
                below.lower_right = trapezoid.lower_right
                above.upper_right = trapezoid.upper_right
            # connect to new trapezoids replacing old
            if below is not prev_below:
                below.upper_left = prev_below
                below.lower_left = (
                    prev_below
                    if trapezoid.lower_left is prev_trapezoid
                    else trapezoid.lower_left)
            if above is not prev_above:
                above.lower_left = prev_above
                above.upper_left = (
                    prev_above
                    if trapezoid.upper_left is prev_trapezoid
                    else trapezoid.upper_left)
        else:
            # middle trapezoid,
            # old trapezoid is neither the first
            # nor last of the 3+ trapezoids
            # that the segment intersects
            if prev_below.below is trapezoid.below:
                below = prev_below
                below.right = trapezoid.right
            else:
                below = Trapezoid(trapezoid.left, trapezoid.right,
                                  trapezoid.below, edge)
            if prev_above.above is trapezoid.above:
                above = prev_above
                above.right = trapezoid.right
            else:
                above = Trapezoid(trapezoid.left, trapezoid.right, edge,
                                  trapezoid.above)
            # connect to new trapezoids replacing prev_trapezoid
            if below is not prev_below:
                # below is new
                below.upper_left = prev_below
                below.lower_left = (
                    prev_below
                    if trapezoid.lower_left is prev_trapezoid
                    else trapezoid.lower_left)
            if above is not prev_above:
                # above is new
                above.lower_left = prev_above
                above.upper_left = (
                    prev_above
                    if trapezoid.upper_left is prev_trapezoid
                    else trapezoid.upper_left)
            below.lower_right = trapezoid.lower_right
            above.upper_right = trapezoid.upper_right
        candidate = YNode(edge,
                          below.node
                          if below is prev_below
                          else Leaf(below),
                          above.node
                          if above is prev_above
                          else Leaf(above))
        if have_right:
            candidate = XNode(edge_right, candidate, Leaf(right))
        if have_left:
            candidate = XNode(edge_left, Leaf(left), candidate)
        trapezoid_node = trapezoid.node
        if trapezoid_node is graph.root:
            graph.root = candidate
        else:
            trapezoid_node.replace_with(candidate)
        # prepare for next loop
        prev_trapezoid, prev_above, prev_below = trapezoid, above, below


def box_to_node(box: Box, context: Context) -> Leaf:
    min_x, min_y, max_x, max_y = box.min_x, box.min_y, box.max_x, box.max_y
    delta_x, delta_y = max_x - min_x, max_y - min_y
    # handle horizontal/vertical cases
    delta_x, delta_y = delta_x or 1, delta_y or 1
    min_x, min_y, max_x, max_y = (min_x - delta_x, min_y - delta_y,
                                  max_x + delta_x, max_y + delta_y)
    point_cls = context.point_cls
    return Leaf(Trapezoid(
            point_cls(min_x, min_y), point_cls(max_x, min_y),
            Edge.from_endpoints(point_cls(min_x, min_y),
                                point_cls(max_x, min_y), False,
                                context),
            Edge.from_endpoints(point_cls(min_x, max_y),
                                point_cls(max_x, max_y), True,
                                context)))


def find_intersecting_trapezoids(graph: Graph, edge: Edge) -> List[Trapezoid]:
    trapezoid = graph.root.search_edge(edge)
    result = [trapezoid]
    right = edge.right
    while trapezoid.right < right:
        trapezoid = ((trapezoid.upper_right or trapezoid.lower_right)
                     if (edge.orientation_of(trapezoid.right)
                         is Orientation.CLOCKWISE)
                     else (
                trapezoid.lower_right or trapezoid.upper_right))
        assert trapezoid is not None, ('Expected neighbour trapezoid, '
                                       'but none found.')
        result.append(trapezoid)
    return result
