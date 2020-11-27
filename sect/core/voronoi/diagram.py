from copy import copy
from operator import itemgetter
from typing import (List,
                    Optional,
                    Tuple)

from dendroid import red_black
from prioq.base import PriorityQueue
from reprit.base import generate_repr

from sect.hints import (Multipoint,
                        Multisegment,
                        Point,
                        Segment)
from .beach_line_key import BeachLineKey
from .beach_line_value import BeachLineValue
from .enums import SourceCategory
from .events import (CircleEvent,
                     SiteEvent)
from .events.computers import (to_point_point_point_circle_event,
                               to_point_point_segment_circle_event,
                               to_point_segment_segment_circle_event,
                               to_segment_segment_segment_circle_event)
from .events.predicates import (point_point_point_circle_exists,
                                point_point_segment_circle_exists,
                                point_segment_segment_circle_exists,
                                segment_segment_segment_circle_exists)
from .faces import (Cell,
                    Edge,
                    Vertex)
from .utils import (are_same_vertical_points,
                    to_unique_just_seen)


class Diagram:
    __slots__ = ('cells', 'edges', 'vertices', '_beach_line', '_circle_events',
                 '_end_points', '_site_events', '_site_event_index')

    def __init__(self,
                 cells: Optional[List[Cell]] = None,
                 edges: Optional[List[Edge]] = None,
                 vertices: Optional[List[Vertex]] = None) -> None:
        self.cells = [] if cells is None else cells
        self.edges = [] if edges is None else edges
        self.vertices = [] if vertices is None else vertices
        self._site_events = []
        self._site_event_index = None
        self._beach_line = red_black.Tree.from_components([])
        self._circle_events = PriorityQueue(key=itemgetter(0))
        self._end_points = PriorityQueue(key=itemgetter(0))

    __repr__ = generate_repr(__init__)

    def clear(self) -> None:
        self.cells.clear()
        self.edges.clear()
        self.vertices.clear()

    @classmethod
    def from_sources(cls,
                     multipoint: Multipoint,
                     multisegment: Multisegment) -> 'Diagram':
        result = Diagram()
        for point in multipoint:
            result._insert_point(point)
        for segment in multisegment:
            result._insert_segment(segment)
        result._construct()
        return result

    @property
    def _site_event(self) -> SiteEvent:
        return self._site_events[self._site_event_index]

    def _activate_circle_event(self,
                               first_site: SiteEvent,
                               second_site: SiteEvent,
                               third_site: SiteEvent,
                               bisector_node: red_black.Node) -> None:
        # check if the three input sites create a circle event
        if first_site.is_point:
            if second_site.is_point:
                if third_site.is_point:
                    # (point, point, point) sites
                    if not point_point_point_circle_exists(
                            first_site, second_site, third_site):
                        return
                    circle_event = to_point_point_point_circle_event(
                            first_site, second_site, third_site)
                else:
                    # (point, point, segment) sites
                    if not point_point_segment_circle_exists(
                            first_site, second_site, third_site, 3):
                        return
                    circle_event = to_point_point_segment_circle_event(
                            first_site, second_site, third_site, 3)
            elif third_site.is_point:
                # (point, segment, point) sites
                if not point_point_segment_circle_exists(
                        first_site, third_site, second_site, 2):
                    return
                circle_event = to_point_point_segment_circle_event(
                        first_site, third_site, second_site, 2)
            else:
                # (point, segment, segment) sites.
                if not point_segment_segment_circle_exists(
                        first_site, second_site, third_site, 1):
                    return
                circle_event = to_point_segment_segment_circle_event(
                        first_site, second_site, third_site, 1)
        elif second_site.is_point:
            if third_site.is_point:
                # (segment, point, point) sites
                if not point_point_segment_circle_exists(
                        second_site, third_site, first_site, 1):
                    return
                circle_event = to_point_point_segment_circle_event(
                        second_site, third_site, first_site, 1)
            else:
                # (segment, point, segment) sites
                if not point_segment_segment_circle_exists(
                        second_site, first_site, third_site, 2):
                    return
                circle_event = to_point_segment_segment_circle_event(
                        second_site, first_site, third_site, 2)
        elif third_site.is_point:
            # (segment, segment, point) sites
            if not point_segment_segment_circle_exists(
                    third_site, first_site, second_site, 3):
                return
            circle_event = to_point_segment_segment_circle_event(
                    third_site, first_site, second_site, 3)
        else:
            # (segment, segment, segment) sites
            if not segment_segment_segment_circle_exists(
                    first_site, second_site, third_site):
                return
            circle_event = to_segment_segment_segment_circle_event(
                    first_site, second_site, third_site)
        if (circle_event.lies_outside_vertical_segment(first_site)
                or circle_event.lies_outside_vertical_segment(second_site)
                or circle_event.lies_outside_vertical_segment(third_site)):
            return
        # add the new circle event to the circle events queue;
        # update bisector's circle event iterator to point
        # to the new circle event in the circle event queue
        self._circle_events.push((circle_event, bisector_node))
        bisector_node.value.circle_event = circle_event

    def _build(self) -> None:
        self._remove_degenerate_edges()
        for edge in self.edges:
            edge.set_as_incident()
        self._remove_degenerate_vertices()
        # set up next/prev pointers for infinite edges
        if self.vertices:
            # update prev/next pointers for the ray edges
            self._update_ray_edges()
        elif self.edges:
            # update prev/next pointers for the line edges
            self._update_line_edges()

    def _construct(self) -> None:
        self._init_sites_queue()
        self._init_beach_line()
        while (self._circle_events
               or self._site_event_index < len(self._site_events)):
            if not self._circle_events:
                self._process_site_event()
            elif self._site_event_index >= len(self._site_events):
                self._process_circle_event()
            elif self._site_event < self._circle_events.peek()[0]:
                self._process_site_event()
            else:
                self._process_circle_event()
            while (self._circle_events
                   and not self._circle_events.peek()[0].is_active):
                self._circle_events.pop()
        self._beach_line.clear()
        self._build()

    def _init_beach_line(self) -> None:
        if not self._site_events:
            return
        elif len(self._site_events) == 1:
            # handle single site event case
            self._process_single_site(self._site_events[0])
            self._site_event_index += 1
        else:
            skip = 0
            while (self._site_event_index < len(self._site_events)
                   and are_same_vertical_points(self._site_event.start,
                                                self._site_events[0].start)
                   and self._site_event.is_vertical):
                self._site_event_index += 1
                skip += 1
            if skip == 1:
                # init beach line with the first two sites
                self._init_beach_line_default()
            else:
                # init beach line with collinear vertical sites
                self._init_beach_line_collinear_sites()

    def _init_beach_line_collinear_sites(self) -> None:
        first_index, second_index = 0, 1
        while second_index != self._site_event_index:
            # create a new beach line node
            first_site, second_site = (self._site_events[first_index],
                                       self._site_events[second_index])
            new_node = BeachLineKey(first_site, second_site)
            # update the diagram
            edge, _ = self._insert_new_edge(first_site, second_site)
            # insert a new bisector into the beach line
            self._beach_line.insert(new_node, BeachLineValue(edge))
            first_index += 1
            second_index += 1

    def _init_beach_line_default(self) -> None:
        # get the first and the second site event
        self._insert_new_arc(self._site_events[0], self._site_events[0],
                             self._site_events[1])
        # the second site was already processed, move the position
        self._site_event_index += 1

    def _insert_new_arc(self,
                        first_arc_site: SiteEvent,
                        second_arc_site: SiteEvent,
                        site_event: SiteEvent) -> red_black.Node:
        # create two new bisectors with opposite directions
        new_left_node = BeachLineKey(first_arc_site, site_event)
        new_right_node = BeachLineKey(site_event, second_arc_site)
        # set correct orientation for the first site of the second node
        if site_event.is_segment:
            new_right_node.left_site.inverse()
        # update the output
        edges = self._insert_new_edge(second_arc_site, site_event)
        self._beach_line.insert(new_right_node, BeachLineValue(edges[1]))
        if site_event.is_segment:
            # update the beach line with temporary bisector,
            # that will # disappear after processing site event
            # corresponding to the second endpoint of the segment site
            new_node = BeachLineKey(site_event, site_event)
            new_node.right_site.inverse()
            node = self._beach_line.insert(new_node, BeachLineValue(None))
            # update the data structure that holds temporary bisectors
            self._end_points.push((site_event.end, node))
        return self._beach_line.insert(new_left_node, BeachLineValue(edges[0]))

    def _init_sites_queue(self) -> None:
        self._site_events.sort()
        self._site_events = to_unique_just_seen(self._site_events)
        for index, event in enumerate(self._site_events):
            event.sorted_index = index
        self._site_event_index = 0

    def _insert_new_edge(self,
                         first_site: SiteEvent,
                         second_site: SiteEvent) -> Tuple[Edge, Edge]:
        if not self.cells:
            self.cells.append(Cell(first_site.source,
                                   first_site.source_category))
        # the second site represents a new site during site event processing,
        # add a new cell to the cell records
        self.cells.append(Cell(second_site.source,
                               second_site.source_category))
        is_linear = is_linear_edge(first_site, second_site)
        is_primary = is_primary_edge(first_site, second_site)
        first_edge = Edge(None, self.cells[first_site.sorted_index], is_linear,
                          is_primary)
        second_edge = Edge(None, self.cells[second_site.sorted_index],
                           is_linear, is_primary)
        first_edge.twin, second_edge.twin = second_edge, first_edge
        self.edges.append(first_edge)
        self.edges.append(second_edge)
        return first_edge, second_edge

    def _insert_new_edge_from_intersection(self,
                                           first_site_event: SiteEvent,
                                           second_site_event: SiteEvent,
                                           circle_event: CircleEvent,
                                           first_bisector: Edge,
                                           second_bisector: Edge
                                           ) -> Tuple[Edge, Edge]:
        # add a new Voronoi vertex
        new_vertex = Vertex(circle_event.center_x, circle_event.center_y)
        self.vertices.append(new_vertex)
        # update vertex pointers of the old edges
        first_bisector.start = second_bisector.start = new_vertex
        is_linear = is_linear_edge(first_site_event, second_site_event)
        is_primary = is_primary_edge(first_site_event, second_site_event)
        first_edge = Edge(None, self.cells[first_site_event.sorted_index],
                          is_linear, is_primary)
        second_edge = Edge(new_vertex,
                           self.cells[second_site_event.sorted_index],
                           is_linear, is_primary)
        first_edge.twin, second_edge.twin = second_edge, first_edge
        first_edge.next, second_edge.prev = (first_bisector,
                                             second_bisector.twin)
        first_bisector.prev, second_bisector.prev = (first_edge,
                                                     first_bisector.twin)
        first_bisector.twin.next, second_bisector.twin.next = (second_bisector,
                                                               second_edge)
        self.edges.append(first_edge)
        self.edges.append(second_edge)
        return first_edge, second_edge

    def _insert_point(self, point: Point) -> None:
        self._site_events.append(SiteEvent(point, point, point,
                                           SourceCategory.SINGLE_POINT))

    def _insert_segment(self, segment: Segment) -> None:
        site_events = self._site_events
        start, end = segment
        site_events.append(SiteEvent(start, start, segment,
                                     SourceCategory.SEGMENT_START_POINT))
        site_events.append(SiteEvent(end, end, segment,
                                     SourceCategory.SEGMENT_END_POINT))
        site_events.append(SiteEvent(start, end, segment,
                                     SourceCategory.INITIAL_SEGMENT)
                           if start < end
                           else SiteEvent(end, start, segment,
                                          SourceCategory.REVERSE_SEGMENT))

    def _process_circle_event(self) -> None:
        circle_event, first_node = self._circle_events.pop()
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
        first_node.value.edge, _ = self._insert_new_edge_from_intersection(
                first_site, second_site, circle_event, first_bisector,
                second_bisector)
        self._beach_line.remove(last_node)
        last_node = first_node
        if first_node is not self._beach_line.min():
            first_node.value.deactivate_circle_event()
            first_node = self._beach_line.predecessor(first_node)
            self._activate_circle_event(first_node.key.left_site, first_site,
                                        second_site, last_node)
        last_node = self._beach_line.successor(last_node)
        if last_node is not red_black.NIL:
            last_node.value.deactivate_circle_event()
            self._activate_circle_event(first_site, second_site,
                                        last_node.key.right_site, last_node)

    def _process_single_site(self, site: SiteEvent) -> None:
        self.cells.append(Cell(site.source, site.source_category))

    def _process_site_event(self) -> None:
        last_index = self._site_event_index + 1
        if not self._site_event.is_segment:
            while (self._end_points
                   and self._end_points.peek()[0] == self._site_event.start):
                _, node = self._end_points.pop()
                self._beach_line.remove(node)
        else:
            while (last_index < len(self._site_events)
                   and self._site_events[last_index].is_segment
                   and (self._site_events[last_index].start
                        == self._site_event.start)):
                last_index += 1
        # find the node in the binary search tree
        # with left arc lying above the new site point
        new_key = BeachLineKey(self._site_event, self._site_event)
        right_node = self._beach_line.supremum(new_key)
        while self._site_event_index < last_index:
            site_event = copy(self._site_event)
            left_node = right_node
            if right_node is red_black.NIL:
                # the above arc corresponds to the second arc of the last node,
                # move the iterator to the last node
                left_node = self._beach_line.max()
                # get the second site of the last node
                arc_site = left_node.key.right_site
                # insert new nodes into the beach line, update the output
                right_node = self._insert_new_arc(arc_site, arc_site,
                                                  site_event)
                # add a candidate circle to the circle event queue;
                # there could be only one new circle event
                # formed by a new bisector and the one on the left
                self._activate_circle_event(left_node.key.left_site,
                                            left_node.key.right_site,
                                            site_event, right_node)
            elif right_node is self._beach_line.min():
                # the above arc corresponds to the first site of the first node
                arc_site = right_node.key.left_site
                # Insert new nodes into the beach line. Update the output.
                left_node = self._insert_new_arc(arc_site, arc_site,
                                                 site_event)
                # if the site event is a segment, update its direction
                if site_event.is_segment:
                    site_event.inverse()
                # add a candidate circle to the circle event queue;
                # there could be only one new circle event
                # formed by a new bisector and the one on the right
                self._activate_circle_event(site_event,
                                            right_node.key.left_site,
                                            right_node.key.right_site,
                                            right_node)
                right_node = left_node
            else:
                # the above arc corresponds neither to the first,
                # nor to the last site in the beach line
                second_arc_site = right_node.key.left_site
                third_site = right_node.key.right_site
                # remove the candidate circle from the event queue
                right_node.value.deactivate_circle_event()
                left_node = self._beach_line.predecessor(left_node)
                first_arc_site = left_node.key.right_site
                first_site = left_node.key.left_site
                # insert new nodes into the beach line. Update the output
                new_node = self._insert_new_arc(first_arc_site,
                                                second_arc_site, site_event)
                # add candidate circles to the circle event queue;
                # there could be up to two circle events
                # formed by a new bisector and the one on the left or right
                self._activate_circle_event(first_site, first_arc_site,
                                            site_event, new_node)
                # if the site event is a segment, update its direction
                if site_event.is_segment:
                    site_event.inverse()
                self._activate_circle_event(site_event, second_arc_site,
                                            third_site, right_node)
                right_node = new_node
            self._site_event_index += 1

    def _remove_degenerate_edges(self) -> None:
        first_degenerate_edge_index = 0
        for edge_index in range(0, len(self.edges), 2):
            edge = self.edges[edge_index]
            if edge.is_degenerate:
                edge.disconnect()
            else:
                if edge_index != first_degenerate_edge_index:
                    self.edges[first_degenerate_edge_index] = edge
                    next_edge = self.edges[first_degenerate_edge_index + 1] = (
                        self.edges[edge_index + 1])
                    edge.twin, next_edge.twin = next_edge, edge
                    if edge.prev is not None:
                        edge.prev.next, next_edge.next.prev = edge, next_edge
                    if next_edge.prev is not None:
                        edge.next.prev, next_edge.prev.next = edge, next_edge
                first_degenerate_edge_index += 2
        del self.edges[first_degenerate_edge_index:]

    def _remove_degenerate_vertices(self) -> None:
        first_degenerate_vertex_index = 0
        for index, vertex in enumerate(self.vertices):
            if vertex.is_degenerate:
                continue
            if index != first_degenerate_vertex_index:
                self.vertices[first_degenerate_vertex_index] = vertex
                cursor = vertex.incident_edge
                while True:
                    cursor.start = vertex
                    cursor = cursor.rot_next
                    if cursor is vertex.incident_edge:
                        break
            first_degenerate_vertex_index += 1
        del self.vertices[first_degenerate_vertex_index:]

    def _update_line_edges(self) -> None:
        edge_index = 0
        edge = self.edges[edge_index]
        edge.prev = edge.next = edge
        edge_index += 1
        edge = self.edges[edge_index]
        edge_index += 1
        while edge_index < len(self.edges):
            next_edge = self.edges[edge_index]
            edge_index += 1
            edge.prev = edge.next = next_edge
            next_edge.prev = next_edge.next = edge
            edge = self.edges[edge_index]
            edge_index += 1
        edge.prev = edge.next = edge

    def _update_ray_edges(self) -> None:
        for cell in self.cells:
            if cell.is_degenerate:
                continue
            # move to the previous edge while it is possible
            # in the clockwise direction
            left_edge = cell.incident_edge
            while left_edge.prev is not None:
                left_edge = left_edge.prev
                # terminate if this is not a boundary cell
                if left_edge is cell.incident_edge:
                    break
            if left_edge.prev is not None:
                continue
            right_edge = cell.incident_edge
            while right_edge.next is not None:
                right_edge = right_edge.next
            left_edge.prev, right_edge.next = right_edge, left_edge


def is_linear_edge(first_event: SiteEvent, second_event: SiteEvent) -> bool:
    return (not is_primary_edge(first_event, second_event)
            or first_event.is_segment is second_event.is_segment)


def is_primary_edge(first_event: SiteEvent, second_event: SiteEvent) -> bool:
    first_event_is_segment, second_event_is_segment = (
        first_event.is_segment, second_event.is_segment)
    if first_event_is_segment and not second_event_is_segment:
        return (first_event.start != second_event.start
                and first_event.end != second_event.start)
    elif not first_event_is_segment and second_event_is_segment:
        return (second_event.start != first_event.start
                and second_event.end != first_event.start)
    return True
