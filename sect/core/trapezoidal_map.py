from functools import reduce
from typing import (Iterable,
                    List,
                    Tuple)

from robust.angular import Orientation

from sect.hints import (Contour,
                        Coordinate,
                        Point,
                        Shuffler)
from .edge import Edge
from .leaf import Leaf
from .node import Node
from .trapezoid import Trapezoid
from .utils import to_contour_orientation
from .x_node import XNode
from .y_node import YNode


def build_graph(contour: Contour, shuffler: Shuffler) -> Node:
    edges = []
    is_contour_positively_oriented = (to_contour_orientation(contour)
                                      is Orientation.COUNTERCLOCKWISE)
    for index in range(len(contour)):
        start, end = contour[index - 1], contour[index]
        edges.append(Edge(start, end, is_contour_positively_oriented)
                     if start < end
                     else Edge(end, start, not is_contour_positively_oriented))
    shuffler(edges)
    return reduce(add_edge_to_graph, edges, contour_to_start_node(contour))


def contour_to_start_node(contour: Contour) -> Leaf:
    min_x, min_y, max_x, max_y = points_to_bounding_box(contour)
    delta_x, delta_y = max_x - min_x, max_y - min_y
    min_x, min_y, max_x, max_y = (min_x - delta_x, min_y - delta_y,
                                  max_x + delta_x, max_y + delta_y)
    return Leaf(Trapezoid((min_x, min_y), (max_x, min_y),
                          Edge((min_x, min_y), (max_x, min_y), False),
                          Edge((min_x, max_y), (max_x, max_y), True)))


def points_to_bounding_box(points: Iterable[Point]
                           ) -> Tuple[Coordinate, Coordinate,
                                      Coordinate, Coordinate]:
    points = iter(points)
    first_point = next(points)
    min_x, min_y = max_x, max_y = first_point
    for point in points:
        x, y = point
        min_x, max_x = min(min_x, x), max(max_x, x)
        min_y, max_y = min(min_y, y), max(max_y, y)
    return min_x, min_y, max_x, max_y


def add_edge_to_graph(root: Node, edge: Edge) -> Node:
    trapezoids = find_intersecting_trapezoids(root, edge)
    p, q = edge_left, edge_right = edge.left, edge.right
    left_old = None  # old trapezoid to the left.
    left_below = None  # below trapezoid to the left.
    left_above = None  # above trapezoid to the left.
    for index, old in enumerate(trapezoids):
        start_trap = index == 0
        end_trap = index == len(trapezoids) - 1
        have_left = start_trap and edge_left != old.left
        have_right = end_trap and edge_right != old.right
        left = right = None
        if start_trap and end_trap:
            if have_left:
                left = Trapezoid(old.left, p, old.below, old.above)
            below = Trapezoid(p, q, old.below, edge)
            above = Trapezoid(p, q, edge, old.above)
            if have_right:
                right = Trapezoid(q, old.right, old.below, old.above)
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
            # Old trapezoid is the first of 2+ trapezoids
            # that the segment intersects.
            if have_left:
                left = Trapezoid(old.left, p, old.below, old.above)
            below = Trapezoid(p, old.right, old.below, edge)
            above = Trapezoid(p, old.right, edge, old.above)

            # Set pairs of trapezoid neighbours.
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
            # Old trapezoid is the last of 2+ trapezoids that the segment
            # intersects.
            if left_below.below == old.below:
                below = left_below
                below.right = q
            else:
                below = Trapezoid(old.left, q, old.below, edge)

            if left_above.above == old.above:
                above = left_above
                above.right = q
            else:
                above = Trapezoid(old.left, q, edge, old.above)

            if have_right:
                right = Trapezoid(q, old.right, old.below, old.above)

            # Set pairs of trapezoid neighbours.
            if have_right:
                right.lower_right = old.lower_right
                right.upper_right = old.upper_right
                below.lower_right = right
                above.upper_right = right
            else:
                below.lower_right = old.lower_right
                above.upper_right = old.upper_right

            # Connect to new trapezoids replacing old.
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
            # Middle trapezoid.
            # Old trapezoid is neither the first nor last of the 3+ trapezoids
            # that the segment intersects.
            if left_below.below == old.below:
                below = left_below
                below.right = old.right
            else:
                below = Trapezoid(old.left, old.right, old.below, edge)

            if left_above.above == old.above:
                above = left_above
                above.right = old.right
            else:
                above = Trapezoid(old.left, old.right, edge, old.above)

            # Connect to new trapezoids replacing prevOld.
            if below is not left_below:  # below is new.
                below.upper_left = left_below
                below.lower_left = (left_below
                                    if old.lower_left is left_old
                                    else old.lower_left)

            if above is not left_above:  # above is new.
                above.lower_left = left_above
                above.upper_left = (left_above
                                    if old.upper_left is left_old
                                    else old.upper_left)
            below.lower_right = old.lower_right
            above.upper_right = old.upper_right
        candidate = YNode(edge,
                          below.trapezoid_node
                          if below is left_below
                          else Leaf(below),
                          above.trapezoid_node
                          if above is left_above
                          else Leaf(above))
        if have_right:
            candidate = XNode(q, candidate, Leaf(right))
        if have_left:
            candidate = XNode(p, Leaf(left), candidate)
        old_node = old.trapezoid_node
        if old_node is root:
            root = candidate
        else:
            old_node.replace_with(candidate)
        if not end_trap:
            # Prepare for next loop.
            left_old = old
            left_above = above
            left_below = below
    return root


def find_intersecting_trapezoids(graph: Node, edge: Edge) -> List[Trapezoid]:
    trapezoid = graph.search_edge(edge)
    result = [trapezoid]
    right = edge.right
    while trapezoid.right < right:
        trapezoid_right_orientation = edge.orientation_with(trapezoid.right)
        assert trapezoid_right_orientation, ('Unable to deal '
                                             'with point on segment.')
        if trapezoid_right_orientation is Orientation.COUNTERCLOCKWISE:
            trapezoid = trapezoid.lower_right
        else:
            trapezoid = trapezoid.upper_right
        assert trapezoid is not None, ('Expected neighbour trapezoid, '
                                       'but none found.')
        result.append(trapezoid)
    return result
