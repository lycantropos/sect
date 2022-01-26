from typing import (Callable,
                    MutableSequence,
                    Tuple)

from ground.hints import Scalar

Box = Tuple[Scalar, Scalar, Scalar, Scalar]
Shuffler = Callable[[MutableSequence], None]
