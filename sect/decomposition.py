import random

from .core.node import Node
from .core.trapezoidal_map import build_graph
from .hints import (Contour,
                    Shuffler)


def trapezoidal(contour: Contour,
                *,
                shuffler: Shuffler = random.shuffle) -> Node:
    return build_graph(contour, shuffler)
