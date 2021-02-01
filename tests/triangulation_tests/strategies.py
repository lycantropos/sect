from ground.base import get_context
from hypothesis import strategies

contexts = strategies.just(get_context())
