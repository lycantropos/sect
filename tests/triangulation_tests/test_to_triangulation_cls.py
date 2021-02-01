from ground.base import Context
from hypothesis import given

from sect.triangulation import (Triangulation,
                                to_triangulation_cls)
from . import strategies


@given(strategies.contexts)
def test_basic(context: Context) -> None:
    result = to_triangulation_cls(context)

    assert issubclass(result, Triangulation)
