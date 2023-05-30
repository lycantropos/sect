from __future__ import annotations

from typing import (TYPE_CHECKING,
                    Optional)

from ground.hints import Point
from reprit.base import generate_repr

if TYPE_CHECKING:
    from .edge import Edge
    from .node import Node


class Trapezoid:
    @property
    def component(self) -> bool:
        """
        Checks if the trapezoid is a component of decomposed geometry.
        """
        return self.below.interior_to_left and not self.above.interior_to_left

    @property
    def lower_left(self) -> Optional[Trapezoid]:
        return self._lower_left

    @lower_left.setter
    def lower_left(self, value: Optional[Trapezoid]) -> None:
        self._lower_left = value
        if value is not None:
            value._lower_right = self

    @property
    def lower_right(self) -> Optional[Trapezoid]:
        return self._lower_right

    @lower_right.setter
    def lower_right(self, value: Optional[Trapezoid]) -> None:
        self._lower_right = value
        if value is not None:
            value._lower_left = self

    @property
    def upper_left(self) -> Optional[Trapezoid]:
        return self._upper_left

    @upper_left.setter
    def upper_left(self, value: Optional[Trapezoid]) -> None:
        self._upper_left = value
        if value is not None:
            value._upper_right = self

    @property
    def upper_right(self) -> Optional[Trapezoid]:
        return self._upper_right

    @upper_right.setter
    def upper_right(self, value: Optional[Trapezoid]) -> None:
        self._upper_right = value
        if value is not None:
            value._upper_left = self

    __slots__ = ('left', 'right', 'below', 'above', 'node', '_lower_left',
                 '_lower_right', '_upper_left', '_upper_right')

    def __init__(self,
                 left: Point,
                 right: Point,
                 below: Edge,
                 above: Edge,
                 node: Node) -> None:
        assert left < right, 'Incorrect endpoints order'
        self.above, self.below, self.left, self.node, self.right = (
            above, below, left, node, right
        )
        self._lower_left: Optional[Trapezoid] = None
        self._lower_right: Optional[Trapezoid] = None
        self._upper_left: Optional[Trapezoid] = None
        self._upper_right: Optional[Trapezoid] = None

    __repr__ = generate_repr(__init__)
