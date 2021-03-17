from copy import copy
from operator import itemgetter
from typing import (List,
                    Optional,
                    Tuple,
                    Type)

from dendroid import red_black
from ground.base import Context
from ground.hints import (Multipoint,
                          Multisegment,
                          Point,
                          Segment)
from prioq.base import PriorityQueue
from reprit.base import generate_repr

from .abcs import Diagram
from .beach_line_key import BeachLineKey
from .beach_line_value import BeachLineValue
from .enums import SourceCategory
from .events import (Circle,
                     Site)
from .events.computers import (to_point_point_point_circle,
                               to_point_point_segment_circle,
                               to_point_segment_segment_circle,
                               to_segment_segment_segment_circle)
from .events.predicates import (point_point_point_circle_exists,
                                point_point_segment_circle_exists,
                                point_segment_segment_circle_exists,
                                segment_segment_segment_circle_exists)
from .faces import (Cell,
                    Edge,
                    Vertex)
from .utils import (are_same_vertical_points,
                    to_unique_just_seen)


def to_diagram_cls(context: Context) -> Type[Diagram]:
    class Result(Diagram):
        __slots__ = ('cells', 'edges', 'vertices', '_beach_line', '_circles',
                     '_end_points', '_sites', '_site_index')

        def __init__(self,
                     cells: Optional[List[Cell]] = None,
                     edges: Optional[List[Edge]] = None,
                     vertices: Optional[List[Vertex]] = None) -> None:
            self.cells = [] if cells is None else cells
            self.edges = [] if edges is None else edges
            self.vertices = [] if vertices is None else vertices
            self._sites, self._site_index = [], None
            self._beach_line = red_black.Tree.from_components([])
            self._circles = PriorityQueue(key=itemgetter(0))
            self._end_points = PriorityQueue(key=itemgetter(0))

        __repr__ = generate_repr(__init__)

        @classmethod
        def from_multipoint(cls, multipoint: Multipoint) -> 'Diagram':
            result = cls()
            for point in multipoint.points:
                result._insert_point(point)
            result._construct()
            return result

        @classmethod
        def from_multisegment(cls, multisegment: Multisegment) -> 'Diagram':
            result = cls()
            for segment in multisegment.segments:
                result._insert_segment(segment)
            result._construct()
            return result

        @property
        def _site(self) -> Site:
            return self._sites[self._site_index]

        def _activate_circle(self,
                             first_site: Site,
                             second_site: Site,
                             third_site: Site,
                             bisector_node: red_black.Node) -> None:
            if first_site.is_point:
                if second_site.is_point:
                    if third_site.is_point:
                        # (point, point, point) sites
                        if not point_point_point_circle_exists(
                                first_site, second_site, third_site, context):
                            return
                        circle = to_point_point_point_circle(
                                first_site, second_site, third_site, context)
                    else:
                        # (point, point, segment) sites
                        if not point_point_segment_circle_exists(
                                first_site, second_site, third_site, 3,
                                context):
                            return
                        circle = to_point_point_segment_circle(
                                first_site, second_site, third_site, 3,
                                context)
                elif third_site.is_point:
                    # (point, segment, point) sites
                    if not point_point_segment_circle_exists(
                            first_site, third_site, second_site, 2, context):
                        return
                    circle = to_point_point_segment_circle(
                            first_site, third_site, second_site, 2, context)
                else:
                    # (point, segment, segment) sites.
                    if not point_segment_segment_circle_exists(
                            first_site, second_site, third_site, 1, context):
                        return
                    circle = to_point_segment_segment_circle(
                            first_site, second_site, third_site, 1, context)
            elif second_site.is_point:
                if third_site.is_point:
                    # (segment, point, point) sites
                    if not point_point_segment_circle_exists(
                            second_site, third_site, first_site, 1, context):
                        return
                    circle = to_point_point_segment_circle(
                            second_site, third_site, first_site, 1, context)
                else:
                    # (segment, point, segment) sites
                    if not point_segment_segment_circle_exists(
                            second_site, first_site, third_site, 2, context):
                        return
                    circle = to_point_segment_segment_circle(
                            second_site, first_site, third_site, 2, context)
            elif third_site.is_point:
                # (segment, segment, point) sites
                if not point_segment_segment_circle_exists(
                        third_site, first_site, second_site, 3, context):
                    return
                circle = to_point_segment_segment_circle(
                        third_site, first_site, second_site, 3, context)
            else:
                # (segment, segment, segment) sites
                if not segment_segment_segment_circle_exists(
                        first_site, second_site, third_site):
                    return
                circle = to_segment_segment_segment_circle(
                        first_site, second_site, third_site, context)
            if (circle.lies_outside_vertical_segment(first_site)
                    or circle.lies_outside_vertical_segment(second_site)
                    or circle.lies_outside_vertical_segment(third_site)):
                return
            self._circles.push((circle, bisector_node))
            bisector_node.value.circle = circle

        def _construct(self) -> None:
            self._init_sites_queue()
            self._init_beach_line()
            while self._circles or self._site_index < len(self._sites):
                if (not self._circles
                        or (self._site_index < len(self._sites)
                            and self._site < self._circles.peek()[0])):
                    self._process_site()
                else:
                    self._process_circle()
                while self._circles and not self._circles.peek()[0].is_active:
                    self._circles.pop()
            self._beach_line.clear()
            finalize(self)

        def _init_beach_line(self) -> None:
            sites = self._sites
            if not sites:
                return
            elif len(sites) == 1:
                # handle single site case
                process_single_site(self, sites[0])
                self._site_index += 1
            else:
                skip = 0
                while (self._site_index < len(sites)
                       and are_same_vertical_points(self._site.start,
                                                    sites[0].start)
                       and self._site.is_vertical):
                    self._site_index += 1
                    skip += 1
                if skip == 1:
                    # init beach line with the first two sites
                    self._init_beach_line_default()
                else:
                    # init beach line with collinear vertical sites
                    self._init_beach_line_collinear_sites()

        def _init_beach_line_collinear_sites(self) -> None:
            first_index, second_index = 0, 1
            while second_index != self._site_index:
                # create a new beach line node
                first_site, second_site = (self._sites[first_index],
                                           self._sites[second_index])
                new_node = BeachLineKey(first_site, second_site,
                                        context=context)
                # update the diagram
                edge, _ = insert_new_edge(self, first_site, second_site)
                # insert a new bisector into the beach line
                self._beach_line.insert(new_node, BeachLineValue(edge))
                first_index += 1
                second_index += 1

        def _init_beach_line_default(self) -> None:
            # get the first and the second sites
            self._insert_new_arc(self._sites[0], self._sites[0],
                                 self._sites[1])
            # the second site was already processed, move the position
            self._site_index += 1

        def _init_sites_queue(self) -> None:
            self._sites.sort()
            self._sites = to_unique_just_seen(self._sites)
            for index, site in enumerate(self._sites):
                site.sorted_index = index
            self._site_index = 0

        def _insert_new_arc(self,
                            first_arc_site: Site,
                            second_arc_site: Site,
                            site: Site) -> red_black.Node:
            # create two new bisectors with opposite directions
            new_left_node = BeachLineKey(first_arc_site, site,
                                         context=context)
            new_right_node = BeachLineKey(site, second_arc_site,
                                          context=context)
            # set correct orientation for the first site of the second node
            if site.is_segment:
                new_right_node.left_site.inverse()
            # update the output
            edges = insert_new_edge(self, second_arc_site, site)
            self._beach_line.insert(new_right_node, BeachLineValue(edges[1]))
            if site.is_segment:
                # update the beach line with temporary bisector,
                # that will # disappear after processing site
                # corresponding to the second endpoint of the segment site
                new_node = BeachLineKey(site, site,
                                        context=context)
                new_node.right_site.inverse()
                node = self._beach_line.insert(new_node, BeachLineValue(None))
                # update the data structure that holds temporary bisectors
                self._end_points.push((site.end, node))
            return self._beach_line.insert(new_left_node,
                                           BeachLineValue(edges[0]))

        def _insert_point(self, point: Point) -> None:
            self._sites.append(Site(context.angle_orientation, point, point,
                                    point, SourceCategory.SINGLE_POINT))

        def _insert_segment(self, segment: Segment) -> None:
            orienteer = context.angle_orientation
            sites = self._sites
            start, end = segment.start, segment.end
            sites.append(Site(orienteer, start, start, segment,
                              SourceCategory.SEGMENT_START_POINT))
            sites.append(Site(orienteer, end, end, segment,
                              SourceCategory.SEGMENT_END_POINT))
            sites.append(Site(orienteer, start, end, segment,
                              SourceCategory.INITIAL_SEGMENT)
                         if start < end
                         else Site(orienteer, end, start, segment,
                                   SourceCategory.REVERSE_SEGMENT))

        def _process_circle(self) -> None:
            circle, first_node = self._circles.pop()
            last_node = first_node
            second_site = copy(first_node.key.right_site)
            second_bisector = first_node.value.edge
            first_node = self._beach_line.predecessor(first_node)
            first_bisector = first_node.value.edge
            first_site = copy(first_node.key.left_site)
            if (not first_site.is_segment and second_site.is_segment
                    and second_site.end == first_site.start):
                second_site.inverse()
            first_node.key.right_site = second_site
            first_node.value.edge, _ = insert_new_edge_from_intersection(
                    self, first_site, second_site, circle, first_bisector,
                    second_bisector)
            self._beach_line.remove(last_node)
            last_node = first_node
            if first_node is not self._beach_line.min():
                first_node.value.deactivate_circle()
                first_node = self._beach_line.predecessor(first_node)
                self._activate_circle(first_node.key.left_site, first_site,
                                      second_site, last_node)
            last_node = self._beach_line.successor(last_node)
            if last_node is not red_black.NIL:
                last_node.value.deactivate_circle()
                self._activate_circle(first_site, second_site,
                                      last_node.key.right_site, last_node)

        def _process_site(self) -> None:
            last_index = self._site_index + 1
            if not self._site.is_segment:
                while (self._end_points
                       and self._end_points.peek()[0] == self._site.start):
                    _, node = self._end_points.pop()
                    self._beach_line.remove(node)
            else:
                while (last_index < len(self._sites)
                       and self._sites[last_index].is_segment
                       and self._sites[last_index].start == self._site.start):
                    last_index += 1
            # find the node in the binary search tree
            # with left arc lying above the new site point
            new_key = BeachLineKey(self._site, self._site,
                                   context=context)
            right_node = self._beach_line.supremum(new_key)
            while self._site_index < last_index:
                site = copy(self._site)
                left_node = right_node
                if right_node is red_black.NIL:
                    # the above arc corresponds
                    # to the second arc of the last node,
                    # move the iterator to the last node
                    left_node = self._beach_line.max()
                    # get the second site of the last node
                    arc_site = left_node.key.right_site
                    # insert new nodes into the beach line, update the output
                    right_node = self._insert_new_arc(arc_site, arc_site, site)
                    # add a candidate circle to the queue;
                    # there could be only one new circle
                    # formed by a new bisector and the one on the left
                    self._activate_circle(left_node.key.left_site,
                                          left_node.key.right_site, site,
                                          right_node)
                elif right_node is self._beach_line.min():
                    # the above arc corresponds
                    # to the first site of the first node
                    arc_site = right_node.key.left_site
                    # insert new nodes into the beach line
                    left_node = self._insert_new_arc(arc_site, arc_site, site)
                    # if the site is a segment, update its direction
                    if site.is_segment:
                        site.inverse()
                    # add a candidate circle to the queue;
                    # there could be only one new circle
                    # formed by a new bisector and the one on the right
                    self._activate_circle(site, right_node.key.left_site,
                                          right_node.key.right_site,
                                          right_node)
                    right_node = left_node
                else:
                    # the above arc corresponds neither to the first,
                    # nor to the last site in the beach line
                    second_arc_site = right_node.key.left_site
                    third_site = right_node.key.right_site
                    # remove the candidate circle from the queue
                    right_node.value.deactivate_circle()
                    left_node = self._beach_line.predecessor(left_node)
                    first_arc_site = left_node.key.right_site
                    first_site = left_node.key.left_site
                    # insert new nodes into the beach line
                    new_node = self._insert_new_arc(first_arc_site,
                                                    second_arc_site, site)
                    # add candidate circles to the queue;
                    # there could be up to two circles
                    # formed by a new bisector and the one on the left or right
                    self._activate_circle(first_site, first_arc_site, site,
                                          new_node)
                    # if the site is a segment, update its direction
                    if site.is_segment:
                        site.inverse()
                    self._activate_circle(site, second_arc_site, third_site,
                                          right_node)
                    right_node = new_node
                self._site_index += 1

    Result.__name__ = Result.__qualname__ = Diagram.__name__
    return Result


def finalize(diagram: Diagram) -> None:
    remove_degenerate_edges(diagram)
    for edge in diagram.edges:
        edge.set_as_incident()
    remove_degenerate_vertices(diagram)
    # set up next/prev pointers for infinite edges
    if diagram.vertices:
        # update prev/next pointers for the ray edges
        update_ray_edges(diagram)
    elif diagram.edges:
        # update prev/next pointers for the line edges
        update_line_edges(diagram)


def insert_new_edge(diagram: Diagram,
                    first_site: Site,
                    second_site: Site) -> Tuple[Edge, Edge]:
    if not diagram.cells:
        diagram.cells.append(Cell(first_site.source,
                                  first_site.source_category))
    # the second site represents a new site during site processing,
    # add a new cell to the cell records
    diagram.cells.append(Cell(second_site.source, second_site.source_category))
    is_linear = is_linear_edge(first_site, second_site)
    is_primary = is_primary_edge(first_site, second_site)
    first_edge = Edge(None, diagram.cells[first_site.sorted_index], is_linear,
                      is_primary)
    second_edge = Edge(None, diagram.cells[second_site.sorted_index],
                       is_linear, is_primary)
    first_edge.opposite, second_edge.opposite = second_edge, first_edge
    diagram.edges.append(first_edge)
    diagram.edges.append(second_edge)
    return first_edge, second_edge


def insert_new_edge_from_intersection(diagram: Diagram,
                                      first_site: Site,
                                      second_site: Site,
                                      circle: Circle,
                                      first_bisector: Edge,
                                      second_bisector: Edge
                                      ) -> Tuple[Edge, Edge]:
    new_vertex = Vertex(circle.center_x, circle.center_y)
    diagram.vertices.append(new_vertex)
    # update vertex pointers of the old edges
    first_bisector.start = second_bisector.start = new_vertex
    is_linear = is_linear_edge(first_site, second_site)
    is_primary = is_primary_edge(first_site, second_site)
    first_edge = Edge(None, diagram.cells[first_site.sorted_index], is_linear,
                      is_primary)
    second_edge = Edge(new_vertex, diagram.cells[second_site.sorted_index],
                       is_linear, is_primary)
    first_edge.opposite, second_edge.opposite = second_edge, first_edge
    first_edge.left_from_end, second_edge.left_in_start = (
        first_bisector, second_bisector.opposite)
    first_bisector.left_in_start, second_bisector.left_in_start = (
        first_edge, first_bisector.opposite)
    (first_bisector.opposite.left_from_end,
     second_bisector.opposite.left_from_end) = second_bisector, second_edge
    diagram.edges.append(first_edge)
    diagram.edges.append(second_edge)
    return first_edge, second_edge


def is_linear_edge(first_site: Site, second_site: Site) -> bool:
    return (not is_primary_edge(first_site, second_site)
            or first_site.is_segment is second_site.is_segment)


def is_primary_edge(first_site: Site, second_site: Site) -> bool:
    first_site_is_segment, second_site_is_segment = (
        first_site.is_segment, second_site.is_segment)
    if first_site_is_segment and not second_site_is_segment:
        return (first_site.start != second_site.start
                and first_site.end != second_site.start)
    elif not first_site_is_segment and second_site_is_segment:
        return (second_site.start != first_site.start
                and second_site.end != first_site.start)
    return True


def process_single_site(diagram: Diagram, site: Site) -> None:
    diagram.cells.append(Cell(site.source, site.source_category))


def remove_degenerate_edges(diagram: Diagram) -> None:
    first_degenerate_edge_index = 0
    for edge_index in range(0, len(diagram.edges), 2):
        edge = diagram.edges[edge_index]
        if edge.is_degenerate:
            edge.disconnect()
        else:
            if edge_index != first_degenerate_edge_index:
                diagram.edges[first_degenerate_edge_index] = edge
                next_edge = diagram.edges[first_degenerate_edge_index + 1] = (
                    diagram.edges[edge_index + 1])
                edge.opposite, next_edge.opposite = next_edge, edge
                if edge.left_in_start is not None:
                    (edge.left_in_start.left_from_end,
                     next_edge.left_from_end.left_in_start) = edge, next_edge
                if next_edge.left_in_start is not None:
                    (edge.left_from_end.left_in_start,
                     next_edge.left_in_start.left_from_end) = edge, next_edge
            first_degenerate_edge_index += 2
    del diagram.edges[first_degenerate_edge_index:]


def remove_degenerate_vertices(diagram: Diagram) -> None:
    first_degenerate_vertex_index = 0
    for index, vertex in enumerate(diagram.vertices):
        if vertex.is_degenerate:
            continue
        if index != first_degenerate_vertex_index:
            diagram.vertices[first_degenerate_vertex_index] = vertex
            cursor = vertex.incident_edge
            while True:
                cursor.start = vertex
                cursor = cursor.left_from_start
                if cursor is vertex.incident_edge:
                    break
        first_degenerate_vertex_index += 1
    del diagram.vertices[first_degenerate_vertex_index:]


def update_line_edges(diagram: Diagram) -> None:
    edge_index = 0
    edge = diagram.edges[edge_index]
    edge.left_in_start = edge.left_from_end = edge
    edge_index += 1
    edge = diagram.edges[edge_index]
    edge_index += 1
    while edge_index < len(diagram.edges):
        next_edge = diagram.edges[edge_index]
        edge_index += 1
        edge.left_in_start = edge.left_from_end = next_edge
        next_edge.left_in_start = next_edge.left_from_end = edge
        edge = diagram.edges[edge_index]
        edge_index += 1
    edge.left_in_start = edge.left_from_end = edge


def update_ray_edges(diagram: Diagram) -> None:
    for cell in diagram.cells:
        if cell.is_degenerate:
            continue
        # move to the previous edge while it is possible
        # in the clockwise direction
        left_edge = cell.incident_edge
        while left_edge.left_in_start is not None:
            left_edge = left_edge.left_in_start
            # terminate if this is not a boundary cell
            if left_edge is cell.incident_edge:
                break
        if left_edge.left_in_start is not None:
            continue
        right_edge = cell.incident_edge
        while right_edge.left_from_end is not None:
            right_edge = right_edge.left_from_end
        left_edge.left_in_start, right_edge.left_from_end = (right_edge,
                                                             left_edge)
