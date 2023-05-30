from __future__ import annotations

import random
from typing import (List,
                    Tuple)

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
                          context: Context) -> Graph:
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
        ...     context=context
        ... )
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
            for segment in multisegment.segments
        ]
        return cls._from_box_with_edges(
                context.segments_box(multisegment.segments), edges, shuffler,
                context
        )

    @classmethod
    def from_polygon(cls,
                     polygon: Polygon,
                     *,
                     shuffler: Shuffler = random.shuffle,
                     context: Context) -> Graph:
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
        ...     context=context
        ... )
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
            for start, end in contour_to_edges_endpoints(border)
        ]
        for hole in polygon.holes:
            is_hole_negatively_oriented = (
                    to_contour_orientation(hole, orienteer)
                    is Orientation.CLOCKWISE
            )
            edges.extend(
                    Edge.from_endpoints(start, end,
                                        is_hole_negatively_oriented, context)
                    if start < end
                    else
                    Edge.from_endpoints(end, start,
                                        not is_hole_negatively_oriented,
                                        context)
                    for start, end in contour_to_edges_endpoints(hole)
            )
        return cls._from_box_with_edges(context.contour_box(border), edges,
                                        shuffler, context)

    @property
    def height(self) -> int:
        """
        Returns height of the root node.
        """
        return self.root.height

    def locate(self, point: Point) -> Location:
        """
        Finds location of point relative to decomposed geometry.

        Time complexity:
            ``O(self.height)``
        Memory complexity:
            ``O(1)``
        """
        return self.root.locate(point)

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

    @classmethod
    def _from_box_with_edges(cls,
                             box: Box,
                             edges: List[Edge],
                             shuffler: Shuffler,
                             context: Context) -> Graph:
        shuffler(edges)
        edges_iterator = iter(edges)
        result = cls(
                to_single_trapezoid_node_replacement(
                        box_to_leaf(box, context).trapezoid,
                        next(edges_iterator)
                )
        )
        for edge in edges_iterator:
            add_edge(result, edge)
        return result


def add_edge(graph: Graph, edge: Edge) -> None:
    assert graph.height > 0
    trapezoids = find_intersecting_trapezoids(graph, edge)
    first_trapezoid = trapezoids[0]
    if len(trapezoids) == 1:
        replacement_node = to_single_trapezoid_node_replacement(
                first_trapezoid, edge
        )
        first_trapezoid.node.replace_with(replacement_node)
    else:
        prev_above, prev_below = add_edge_to_first_trapezoid(first_trapezoid,
                                                             edge)
        # prepare for the loop
        prev_trapezoid = first_trapezoid
        for middle_trapezoid in trapezoids[1:-1]:
            prev_above, prev_below = add_edge_to_middle_trapezoid(
                    middle_trapezoid, edge, prev_above, prev_below,
                    prev_trapezoid
            )
            # prepare for next loop
            prev_trapezoid = middle_trapezoid
        add_edge_to_last_trapezoid(trapezoids[-1], edge, prev_above,
                                   prev_below, prev_trapezoid)


def add_edge_to_first_trapezoid(trapezoid: Trapezoid,
                                edge: Edge) -> Tuple[Trapezoid, Trapezoid]:
    above_node, below_node = (
        Leaf(edge.left, trapezoid.right, edge, trapezoid.above),
        Leaf(edge.left, trapezoid.right, trapezoid.below, edge)
    )
    replacement_node: Node
    replacement_node = YNode(edge, below_node, above_node)
    above, below = above_node.trapezoid, below_node.trapezoid
    # set pairs of trapezoid neighbours
    if edge.left == trapezoid.left:
        above.upper_left = trapezoid.upper_left
        below.lower_left = trapezoid.lower_left
    else:
        left_node = Leaf(trapezoid.left, edge.left, trapezoid.below,
                         trapezoid.above)
        left = left_node.trapezoid
        left.lower_left = trapezoid.lower_left
        left.upper_left = trapezoid.upper_left
        left.lower_right = below
        left.upper_right = above
        replacement_node = XNode(edge.left, left_node, replacement_node)
    above.upper_right = trapezoid.upper_right
    below.lower_right = trapezoid.lower_right
    trapezoid.node.replace_with(replacement_node)
    return above, below


def add_edge_to_last_trapezoid(
        trapezoid: Trapezoid,
        edge: Edge,
        prev_above: Trapezoid,
        prev_below: Trapezoid,
        prev_trapezoid: Trapezoid
) -> None:
    if prev_above.above is trapezoid.above:
        above_node = prev_above.node
        above = prev_above
        above.right = edge.right
    else:
        above_node = Leaf(trapezoid.left, edge.right, edge, trapezoid.above)
        above = above_node.trapezoid
        above.lower_left = prev_above
        above.upper_left = (prev_above
                            if trapezoid.upper_left is prev_trapezoid
                            else trapezoid.upper_left)
    if prev_below.below is trapezoid.below:
        below_node = prev_below.node
        below = prev_below
        below.right = edge.right
    else:
        below_node = Leaf(trapezoid.left, edge.right, trapezoid.below, edge)
        below = below_node.trapezoid
        below.upper_left = prev_below
        below.lower_left = (prev_below
                            if trapezoid.lower_left is prev_trapezoid
                            else trapezoid.lower_left)
    replacement_node: Node
    replacement_node = YNode(edge, below_node, above_node)
    # set pairs of trapezoid neighbours
    if edge.right == trapezoid.right:
        above.upper_right = trapezoid.upper_right
        below.lower_right = trapezoid.lower_right
    else:
        right_node = Leaf(edge.right, trapezoid.right, trapezoid.below,
                          trapezoid.above)
        right = right_node.trapezoid
        right.lower_right = trapezoid.lower_right
        right.upper_right = trapezoid.upper_right
        above.upper_right = below.lower_right = right
        replacement_node = XNode(edge.right, replacement_node, right_node)
    trapezoid.node.replace_with(replacement_node)


def add_edge_to_middle_trapezoid(
        trapezoid: Trapezoid,
        edge: Edge,
        prev_above: Trapezoid,
        prev_below: Trapezoid,
        prev_trapezoid: Trapezoid
) -> Tuple[Trapezoid, Trapezoid]:
    if prev_above.above is trapezoid.above:
        above = prev_above
        above.right = trapezoid.right
        above_node = above.node
    else:
        above_node = Leaf(trapezoid.left, trapezoid.right, edge,
                          trapezoid.above)
        above = above_node.trapezoid
        above.lower_left = prev_above
        above.upper_left = (prev_above
                            if trapezoid.upper_left is prev_trapezoid
                            else trapezoid.upper_left)
    if prev_below.below is trapezoid.below:
        below = prev_below
        below.right = trapezoid.right
        below_node = below.node
    else:
        below_node = Leaf(trapezoid.left, trapezoid.right, trapezoid.below,
                          edge)
        below = below_node.trapezoid
        below.upper_left = prev_below
        below.lower_left = (prev_below
                            if trapezoid.lower_left is prev_trapezoid
                            else trapezoid.lower_left)
    above.upper_right = trapezoid.upper_right
    below.lower_right = trapezoid.lower_right
    replacement_node = YNode(edge, below_node, above_node)
    trapezoid.node.replace_with(replacement_node)
    return above, below


def to_single_trapezoid_node_replacement(trapezoid: Trapezoid,
                                         edge: Edge) -> Node:
    above_node, below_node = (
        Leaf(edge.left, edge.right, edge, trapezoid.above),
        Leaf(edge.left, edge.right, trapezoid.below, edge)
    )
    result: Node
    result = YNode(edge, below_node, above_node)
    above, below = above_node.trapezoid, below_node.trapezoid
    if edge.right == trapezoid.right:
        below.lower_right = trapezoid.lower_right
        above.upper_right = trapezoid.upper_right
    else:
        right_node = Leaf(edge.right, trapezoid.right, trapezoid.below,
                          trapezoid.above)
        right = right_node.trapezoid
        right.lower_right = trapezoid.lower_right
        right.upper_right = trapezoid.upper_right
        below.lower_right = right
        above.upper_right = right
        result = XNode(edge.right, result, right_node)
    if edge.left == trapezoid.left:
        below.lower_left = trapezoid.lower_left
        above.upper_left = trapezoid.upper_left
    else:
        left_node = Leaf(trapezoid.left, edge.left, trapezoid.below,
                         trapezoid.above)
        left = left_node.trapezoid
        left.lower_left = trapezoid.lower_left
        left.upper_left = trapezoid.upper_left
        left.lower_right = below
        left.upper_right = above
        result = XNode(edge.left, left_node, result)
    return result


def box_to_leaf(box: Box, context: Context) -> Leaf:
    min_x, min_y, max_x, max_y = box.min_x, box.min_y, box.max_x, box.max_y
    delta_x, delta_y = max_x - min_x, max_y - min_y
    # handle horizontal/vertical cases
    delta_x, delta_y = delta_x or 1, delta_y or 1
    min_x, min_y, max_x, max_y = (min_x - delta_x, min_y - delta_y,
                                  max_x + delta_x, max_y + delta_y)
    point_cls = context.point_cls
    return Leaf(point_cls(min_x, min_y), point_cls(max_x, min_y),
                Edge.from_endpoints(point_cls(min_x, min_y),
                                    point_cls(max_x, min_y), False, context),
                Edge.from_endpoints(point_cls(min_x, max_y),
                                    point_cls(max_x, max_y), True, context))


def find_intersecting_trapezoids(graph: Graph, edge: Edge) -> List[Trapezoid]:
    trapezoid = graph.root.search_edge(edge)
    result = [trapezoid]
    right = edge.right
    while trapezoid.right < right:
        candidate = ((trapezoid.upper_right or trapezoid.lower_right)
                     if (edge.orientation_of(trapezoid.right)
                         is Orientation.CLOCKWISE)
                     else (trapezoid.lower_right or trapezoid.upper_right))
        assert candidate is not None, ('Expected neighbour trapezoid, '
                                       'but none found.')
        trapezoid = candidate
        result.append(trapezoid)
    return result
