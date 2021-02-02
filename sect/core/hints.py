from typing import Callable

from ground.base import Orientation
from ground.hints import Point

Orienteer = Callable[[Point, Point, Point], Orientation]
