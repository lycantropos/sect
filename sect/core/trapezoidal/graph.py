from typing import List

from ground.base import get_context
from ground.hints import (Point,
                          Polygon)
from reprit.base import generate_repr

from sect.core.hints import Multisegment
from sect.core.utils import (Orientation,
                             contour_to_edges,
                             flatten,
                             to_contour_orientation)
from sect.hints import Shuffler
from .edge import Edge
from .hints import BoundingBox
from .leaf import Leaf
from .location import Location
from .node import Node
from .trapezoid import Trapezoid
from .utils import points_to_bounding_box
from .x_node import XNode
from .y_node import YNode


class Graph:
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

    __repr__ = generate_repr(__init__)

    def __contains__(self, point: Point) -> bool:
        """
        Checks if point is contained in decomposed geometry.

        Time complexity:
            ``O(self.height)``
        Memory complexity:
            ``O(1)``
        """
        return bool(self.root.locate(point))

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

    @classmethod
    def from_multisegment(cls,
                          multisegment: Multisegment,
                          shuffler: Shuffler) -> 'Graph':
        edges = [Edge(start, end, False)
                 if start < end
                 else Edge(end, start, False)
                 for start, end in multisegment]
        shuffler(edges)
        bounding_box = points_to_bounding_box(flatten(multisegment))
        result = cls(bounding_box_to_node(bounding_box))
        for edge in edges:
            result.add_edge(edge)
        return result

    @classmethod
    def from_polygon(cls, polygon: Polygon, shuffler: Shuffler) -> 'Graph':
        border = polygon.border
        is_border_positively_oriented = (to_contour_orientation(border)
                                         is Orientation.COUNTERCLOCKWISE)
        edges = [Edge(start, end, is_border_positively_oriented)
                 if start < end
                 else Edge(end, start,
                           not is_border_positively_oriented)
                 for start, end in contour_to_edges(border)]
        for hole in polygon.holes:
            is_hole_negatively_oriented = (to_contour_orientation(hole)
                                           is Orientation.CLOCKWISE)
            edges.extend(Edge(start, end, is_hole_negatively_oriented)
                         if start < end
                         else Edge(end, start,
                                   not is_hole_negatively_oriented)
                         for start, end in contour_to_edges(hole))
        shuffler(edges)
        bounding_box = points_to_bounding_box(border.vertices)
        result = cls(bounding_box_to_node(bounding_box))
        for edge in edges:
            result.add_edge(edge)
        return result

    def add_edge(self, edge: Edge) -> None:
        trapezoids = self.find_intersecting_trapezoids(edge)
        edge_left, edge_right = edge.left, edge.right
        left_old = left_below = left_above = None
        for index, old in enumerate(trapezoids):
            start_trap = index == 0
            end_trap = index == len(trapezoids) - 1
            have_left = start_trap and edge_left != old.left
            have_right = end_trap and edge_right != old.right
            left = right = None
            if start_trap and end_trap:
                if have_left:
                    left = Trapezoid(old.left, edge_left, old.below, old.above)
                below = Trapezoid(edge_left, edge_right, old.below, edge)
                above = Trapezoid(edge_left, edge_right, edge, old.above)
                if have_right:
                    right = Trapezoid(edge_right, old.right, old.below,
                                      old.above)
                if have_left:
                    left.lower_left = old.lower_left
                    left.upper_left = old.upper_left
                    left.lower_right = below
                    left.upper_right = above
                else:
                    below.lower_left = old.lower_left
                    above.upper_left = old.upper_left
                if have_right:
                    right.lower_right = old.lower_right
                    right.upper_right = old.upper_right
                    below.lower_right = right
                    above.upper_right = right
                else:
                    below.lower_right = old.lower_right
                    above.upper_right = old.upper_right
            elif start_trap:
                # old trapezoid is the first of 2+ trapezoids
                # that the segment intersects
                if have_left:
                    left = Trapezoid(old.left, edge_left, old.below, old.above)
                below = Trapezoid(edge_left, old.right, old.below, edge)
                above = Trapezoid(edge_left, old.right, edge, old.above)

                # set pairs of trapezoid neighbours
                if have_left:
                    left.lower_left = old.lower_left
                    left.upper_left = old.upper_left
                    left.lower_right = below
                    left.upper_right = above
                else:
                    below.lower_left = old.lower_left
                    above.upper_left = old.upper_left
                below.lower_right = old.lower_right
                above.upper_right = old.upper_right
            elif end_trap:
                # old trapezoid is the last of 2+ trapezoids
                # that the segment intersects
                if left_below.below is old.below:
                    below = left_below
                    below.right = edge_right
                else:
                    below = Trapezoid(old.left, edge_right, old.below, edge)

                if left_above.above is old.above:
                    above = left_above
                    above.right = edge_right
                else:
                    above = Trapezoid(old.left, edge_right, edge, old.above)

                if have_right:
                    right = Trapezoid(edge_right, old.right, old.below,
                                      old.above)

                # set pairs of trapezoid neighbours
                if have_right:
                    right.lower_right = old.lower_right
                    right.upper_right = old.upper_right
                    below.lower_right = right
                    above.upper_right = right
                else:
                    below.lower_right = old.lower_right
                    above.upper_right = old.upper_right

                # connect to new trapezoids replacing old
                if below is not left_below:
                    below.upper_left = left_below
                    below.lower_left = (left_below
                                        if old.lower_left is left_old
                                        else old.lower_left)

                if above is not left_above:
                    above.lower_left = left_above
                    above.upper_left = (left_above
                                        if old.upper_left is left_old
                                        else old.upper_left)
            else:
                # middle trapezoid,
                # old trapezoid is neither the first
                # nor last of the 3+ trapezoids
                # that the segment intersects
                if left_below.below is old.below:
                    below = left_below
                    below.right = old.right
                else:
                    below = Trapezoid(old.left, old.right, old.below, edge)

                if left_above.above is old.above:
                    above = left_above
                    above.right = old.right
                else:
                    above = Trapezoid(old.left, old.right, edge, old.above)

                # connect to new trapezoids replacing left_old
                if below is not left_below:
                    # below is new
                    below.upper_left = left_below
                    below.lower_left = (left_below
                                        if old.lower_left is left_old
                                        else old.lower_left)

                if above is not left_above:
                    # above is new
                    above.lower_left = left_above
                    above.upper_left = (left_above
                                        if old.upper_left is left_old
                                        else old.upper_left)
                below.lower_right = old.lower_right
                above.upper_right = old.upper_right
            candidate = YNode(edge,
                              below.node
                              if below is left_below
                              else Leaf(below),
                              above.node
                              if above is left_above
                              else Leaf(above))
            if have_right:
                candidate = XNode(edge_right, candidate, Leaf(right))
            if have_left:
                candidate = XNode(edge_left, Leaf(left), candidate)
            old_node = old.node
            if old_node is self.root:
                self.root = candidate
            else:
                old_node.replace_with(candidate)
            # prepare for next loop
            left_old, left_above, left_below = old, above, below

    def find_intersecting_trapezoids(self, edge: Edge) -> List[Trapezoid]:
        trapezoid = self.root.search_edge(edge)
        result = [trapezoid]
        right = edge.right
        while trapezoid.right < right:
            trapezoid = ((trapezoid.upper_right or trapezoid.lower_right)
                         if (edge.orientation_of(trapezoid.right)
                             is Orientation.CLOCKWISE)
                         else (trapezoid.lower_right or trapezoid.upper_right))
            assert trapezoid is not None, ('Expected neighbour trapezoid, '
                                           'but none found.')
            result.append(trapezoid)
        return result


def bounding_box_to_node(bounding_box: BoundingBox) -> Leaf:
    min_x, min_y, max_x, max_y = bounding_box
    delta_x, delta_y = max_x - min_x, max_y - min_y
    # handle horizontal/vertical cases
    delta_x, delta_y = delta_x or 1, delta_y or 1
    min_x, min_y, max_x, max_y = (min_x - delta_x, min_y - delta_y,
                                  max_x + delta_x, max_y + delta_y)
    context = get_context()
    point_cls = context.point_cls
    return Leaf(Trapezoid(point_cls(min_x, min_y), point_cls(max_x, min_y),
                          Edge(point_cls(min_x, min_y),
                               point_cls(max_x, min_y), False),
                          Edge(point_cls(min_x, max_y),
                               point_cls(max_x, max_y), True)))
