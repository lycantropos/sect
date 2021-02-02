from typing import (Callable,
                    TypeVar)

from ground.base import Orientation
from ground.hints import Point

Domain = TypeVar('Domain')
Orienteer = Callable[[Point, Point, Point], Orientation]
