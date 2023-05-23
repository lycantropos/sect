from __future__ import annotations

from typing import (TYPE_CHECKING,
                    Optional)

from ground.hints import Point
from reprit.base import generate_repr

if TYPE_CHECKING:
    from .node import Node
    from .edge import Edge


class Trapezoid:
    __slots__ = ('left', 'right', 'below', 'above', 'node', '_lower_left',
                 '_lower_right', '_upper_left', '_upper_right')

    def __init__(self,
                 left: Point,
                 right: Point,
                 below: Edge,
                 above: Edge) -> None:
        assert left < right, 'Incorrect endpoints order'
        self.left = left
        self.right = right
        self.above = above
        self.below = below
        self.node: Optional[Node] = None
        self._lower_left: Optional[Trapezoid] = None
        self._lower_right: Optional[Trapezoid] = None
        self._upper_left: Optional[Trapezoid] = None
        self._upper_right: Optional[Trapezoid] = None

    __repr__ = generate_repr(__init__)

    @property
    def component(self) -> bool:
        """
        Checks if the trapezoid is a component of decomposed geometry.
        """
        return self.below.interior_to_left and not self.above.interior_to_left

    @property
    def lower_left(self) -> Optional[Trapezoid]:
        return self._lower_left

    @property
    def lower_right(self) -> Optional[Trapezoid]:
        return self._lower_right

    @property
    def upper_left(self) -> Optional[Trapezoid]:
        return self._upper_left

    @property
    def upper_right(self) -> Optional[Trapezoid]:
        return self._upper_right

    @lower_left.setter
    def lower_left(self, value: Optional[Trapezoid]) -> None:
        self._lower_left = value
        if value is not None:
            value._lower_right = self

    @lower_right.setter
    def lower_right(self, value: Optional[Trapezoid]) -> None:
        self._lower_right = value
        if value is not None:
            value._lower_left = self

    @upper_left.setter
    def upper_left(self, value: Optional[Trapezoid]) -> None:
        self._upper_left = value
        if value is not None:
            value._upper_right = self

    @upper_right.setter
    def upper_right(self, value: Optional[Trapezoid]) -> None:
        self._upper_right = value
        if value is not None:
            value._upper_left = self
